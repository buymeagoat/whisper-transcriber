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
from api.paths import UPLOAD_DIR, TRANSCRIPTS_DIR
from api.app_state import (
    db_lock,
    handle_whisper,
    LOCAL_TZ,
    backend_log,
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


app.middleware("http")(access_logger)


# ─── Static File Routes ───
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
register_routes(app)
