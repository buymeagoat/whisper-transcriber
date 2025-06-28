from api.settings import settings

import os
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.orm_bootstrap import SessionLocal, validate_or_initialize_database
from api.models import Job
from api.models import JobStatusEnum
from api.utils.logger import get_system_logger
from api.utils.model_validation import validate_models_dir
from api.router_setup import register_routes
from api.middlewares.access_log import access_logger
from api.paths import storage, UPLOAD_DIR, TRANSCRIPTS_DIR
from api.utils.db_lock import db_lock
from api.app_state import (
    handle_whisper,
    LOCAL_TZ,
    backend_log,
    start_cleanup_thread,
)

# ─── Logging ───
system_log = get_system_logger()


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
    validate_models_dir()
    rehydrate_incomplete_jobs()
    if settings.cleanup_enabled:
        start_cleanup_thread()
    yield
    system_log.info("App shutdown — lifespan exiting.")


log_startup_settings()
system_log.info("FastAPI app initialization starting.")

# ─── App Setup ───
app = FastAPI(lifespan=lifespan)

# ─── Middleware ───
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
    return {"status": "ok"}


@app.get("/version")
def version() -> dict:
    """Return the application version from pyproject.toml."""
    pyproject = ROOT.parent / "pyproject.toml"
    import tomllib

    data = tomllib.loads(pyproject.read_text())
    version = data.get("project", {}).get("version", "unknown")
    return {"version": version}


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
                handle_whisper(job.id, upload_path, job_dir, job.model)
            except Exception as e:
                backend_log.error(f"Failed to rehydrate job {job.id}: {e}")


# ─── Register Routers ─────────────────────────────────────
register_routes(app)
