import os
import time

from datetime import datetime
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import HTTPException
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from api.routes import jobs, admin, logs

from api.orm_bootstrap import SessionLocal, validate_or_initialize_database
from api.models import Job
from api.models import JobStatusEnum
from api.utils.logger import get_system_logger
from api.app_state import (
    UPLOAD_DIR,
    TRANSCRIPTS_DIR,
    MODEL_DIR,
    LOG_DIR,
    db_lock,
    handle_whisper,
    LOCAL_TZ,
    backend_log,
    ACCESS_LOG,
)

# ─── Logging ───
system_log = get_system_logger()

# ─── Paths ───
ROOT = Path(__file__).parent

# ─── ENV SAFETY CHECK ───
from dotenv import load_dotenv

load_dotenv()

# Read API host from environment with a default for local development.
API_HOST = os.getenv("VITE_API_HOST", "http://localhost:8000")
if os.getenv("VITE_API_HOST") is None:
    system_log.warning("VITE_API_HOST not set, defaulting to http://localhost:8000")


def validate_models_dir():
    if not MODEL_DIR.exists() or not any(MODEL_DIR.iterdir()):
        system_log.critical(
            "Missing or empty models directory. Populate models/ before running."
        )
        raise RuntimeError("Whisper models required; see download_models.sh")


# ─── Lifespan Hook ───
@asynccontextmanager
async def lifespan(app: FastAPI):
    system_log.info("App startup — lifespan entering.")
    validate_or_initialize_database()
    validate_models_dir()
    rehydrate_incomplete_jobs()
    yield
    system_log.info("App shutdown — lifespan exiting.")


system_log.info("FastAPI app initialization starting.")

# ─── App Setup ───
app = FastAPI(lifespan=lifespan)

# ─── Middleware ───
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def access_logger(request: Request, call_next):
    start = time.time()
    resp = await call_next(request)
    dur = time.time() - start
    host = getattr(request.client, "host", "localtest")
    with ACCESS_LOG.open("a", encoding="utf-8") as fh:
        fh.write(
            f"[{datetime.now(LOCAL_TZ).isoformat()}] {host} "
            f"{request.method} {request.url.path} -> "
            f"{resp.status_code} in {dur:.2f}s\n"
        )
    return resp


# ─── Static File Routes ───
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR, html=True), name="uploads")
app.mount(
    "/transcripts",
    StaticFiles(directory=TRANSCRIPTS_DIR, html=True),
    name="transcripts",
)

# ─── Debug Output ───
backend_log.debug("\nSTATIC ROUTE CHECK:")
for route in app.routes:
    backend_log.debug(
        f"Path: {getattr(route, 'path', 'n/a')}  →  Name: {getattr(route, 'name', 'n/a')}  →  Type: {type(route)}"
    )


@app.get("/health")
def health_check():
    return {"status": "ok"}


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
                upload_path = UPLOAD_DIR / job.saved_filename
                job_dir = TRANSCRIPTS_DIR / job.id
                handle_whisper(job.id, upload_path, job_dir, job.model)
            except Exception as e:
                backend_log.error(f"Failed to rehydrate job {job.id}: {e}")


# ─── Register Routers ─────────────────────────────────────
app.include_router(jobs.router)
app.include_router(admin.router)
app.include_router(logs.router)


# ── Serve React SPA ───────────────────────────────────────
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_dir, html=True), name="static")


@app.get("/", include_in_schema=False)
def spa_index():
    return FileResponse(static_dir / "index.html")


# ──────────────────────────────────────────────────────────


# ── React-Router fallback ────────────────────────────────────────
@app.get("/{full_path:path}", include_in_schema=False)
def spa_fallback(full_path: str):
    # Let real API and asset paths keep their normal behaviour
    protected = (
        "static",
        "uploads",
        "transcripts",
        "jobs",
        "log",
        "admin/files",
        "admin/reset",
        "admin/download-all",
        "health",
        "docs",
        "openapi.json",
    )
    if full_path.startswith(protected):
        raise HTTPException(status_code=404, detail="Not Found")

    # Everything else is a front-end route -> serve React bundle
    return FileResponse(static_dir / "index.html")
