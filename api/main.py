import os
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from api.utils.logger import get_system_logger
from api.exceptions import ConfigurationError, InitError

system_log = get_system_logger()

try:
    from api.settings import settings
    from api.config_validator import validate_config
    from api.paths import storage, UPLOAD_DIR, TRANSCRIPTS_DIR
    import api.app_state as app_state
    from api.app_state import (
        handle_whisper,
        LOCAL_TZ,
        backend_log,
        start_cleanup_thread,
        stop_cleanup_thread,
        check_celery_connection,
    )
    from api.services.job_queue import ThreadJobQueue
    from api.middlewares.security_headers import SecurityHeadersMiddleware
    from api.middlewares.rate_limit import RateLimitMiddleware, RateLimitConfig
    from api.middlewares.api_cache import ApiCacheMiddleware, CacheConfig

    validate_config()
except (ConfigurationError, InitError) as exc:  # pragma: no cover - startup fail
    system_log.critical(str(exc))
    raise SystemExit(1)

from api.orm_bootstrap import SessionLocal, validate_or_initialize_database
from api.models import Job
from api.models import JobStatusEnum
from api.services.users import ensure_default_admin
from api.utils.model_validation import validate_models_dir
from api.router_setup import register_routes
from api.middlewares.access_log import access_logger
from api.utils.db_lock import db_lock
from functools import partial


def log_startup_settings() -> None:
    """Log key configuration settings."""
    system_log.info(
        "db_url=%s, job_queue_backend=%s, storage_backend=%s, log_level=%s",
        settings.db_url,
        settings.job_queue_backend,
        settings.storage_backend,
        settings.log_level,
    )


# ─── Paths ───
ROOT = Path(__file__).parent

# ─── ENV SAFETY CHECK ───
# Read API host from environment with a default for local development.
API_HOST = settings.vite_api_host
if "VITE_API_HOST" not in os.environ:
    system_log.warning("VITE_API_HOST not set, defaulting to http://localhost:8000")


# ─── Lifespan Hook ───
@asynccontextmanager
async def lifespan(app: FastAPI):
    system_log.info("App startup — lifespan entering.")
    validate_or_initialize_database()
    ensure_default_admin(settings.auth_username, settings.auth_password)
    validate_models_dir()
    system_log.info(
        "Startup complete: DB connected, storage backend %s ready, job queue %s, timezone %s",
        settings.storage_backend,
        settings.job_queue_backend,
        settings.timezone,
    )
    try:
        await check_celery_connection()
    except InitError as exc:
        system_log.critical(str(exc))
        raise SystemExit(1)
    rehydrate_incomplete_jobs()
    if settings.cleanup_enabled:
        start_cleanup_thread()
    system_log.info(
        "Application startup complete. Connect at %s",
        settings.vite_api_host,
    )
    yield
    system_log.info("App shutdown — lifespan exiting.")
    if isinstance(app_state.job_queue, ThreadJobQueue):
        app_state.job_queue.shutdown()
    if settings.cleanup_enabled:
        stop_cleanup_thread()


log_startup_settings()
system_log.info("FastAPI app initialization starting.")

# ─── App Setup ───
app = FastAPI(lifespan=lifespan)

# ─── Middleware ───
# API Response Caching (5 minute default TTL, 1000 entry limit)
cache_config = CacheConfig(
    default_ttl=300,       # 5 minutes
    max_cache_size=1000,   # Maximum 1000 cached responses
    enable_caching=True
)
app.add_middleware(ApiCacheMiddleware, config=cache_config)

# Rate limiting for authentication endpoints (5 requests per 5 minutes)
rate_limit_config = RateLimitConfig(
    max_requests=5,
    window_seconds=300,    # 5 minutes
    block_duration_seconds=900  # 15 minutes block after rate limit hit
)
app.add_middleware(RateLimitMiddleware, config=rate_limit_config)

app.add_middleware(SecurityHeadersMiddleware, enable_hsts=False)  # HSTS disabled for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.middleware("http")(access_logger)


# ─── Static File Routes ───
@app.get("/health")
def health_check():
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception as exc:
        system_log.error(f"Health check failed: {exc}")
        return JSONResponse(status_code=500, content={"status": "db_error"})


@app.get("/version")
def version() -> dict:
    """Return the application version from pyproject.toml."""
    try:
        pyproject = ROOT.parent / "pyproject.toml"
        try:
            import tomllib
        except ImportError:
            # Fallback for Python < 3.11
            import tomli as tomllib
        
        data = tomllib.loads(pyproject.read_text())
        version = data.get("project", {}).get("version", "unknown")
        return {"version": version}
    except Exception as e:
        return {"version": "error", "details": str(e)}


def rehydrate_incomplete_jobs():
    with SessionLocal() as db:
        jobs = (
            db.query(Job)
            .filter(
                Job.status.in_(
                    [
                        JobStatusEnum.QUEUED,
                        JobStatusEnum.PROCESSING,
                        JobStatusEnum.ENRICHING,
                    ]
                )
            )
            .all()
        )
        for job in jobs:
            backend_log.info(f"Rehydrating job {job.id} with model '{job.model}'")
            try:
                upload_path = storage.get_upload_path(job.saved_filename)
                job_dir = storage.get_transcript_dir(job.id)
                app_state.job_queue.enqueue(
                    partial(
                        handle_whisper,
                        job.id,
                        upload_path,
                        job_dir,
                        job.model,
                        start_thread=False,
                    )
                )
            except Exception as e:
                backend_log.error(f"Failed to rehydrate job {job.id}: {e}")


# ─── Register Routers ─────────────────────────────────────
register_routes(app)
