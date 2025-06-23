import os
import time
import shutil
import threading
import subprocess

from datetime import datetime
from subprocess import Popen, PIPE
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import HTTPException
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from api.routes import jobs, admin, logs

from api.metadata_writer import run_metadata_writer
from api.errors import ErrorCode, http_error
from api.utils.logger import get_logger
from api.orm_bootstrap import SessionLocal, validate_or_initialize_database
from api.models import Job
from api.models import JobStatusEnum
from api.utils.logger import get_system_logger
from zoneinfo import ZoneInfo

LOCAL_TZ = ZoneInfo("America/Chicago")

# ─── Logging ───
backend_log = get_logger("backend")
system_log = get_system_logger()

# ─── Paths ───
ROOT = Path(__file__).parent
UPLOAD_DIR = ROOT.parent / "uploads"
TRANSCRIPTS_DIR = ROOT.parent / "transcripts"
MODEL_DIR = ROOT.parent / "models"
LOG_DIR = ROOT.parent / "logs"
ACCESS_LOG = LOG_DIR / "access.log"
DB_PATH = Path(os.getenv("DB", str(ROOT / "jobs.db")))


# ─── Ensure Required Dirs Exist ───
for p in (UPLOAD_DIR, TRANSCRIPTS_DIR, MODEL_DIR, LOG_DIR):
    p.mkdir(parents=True, exist_ok=True)

# ─── Whisper CLI Check ───
# Only check for the whisper binary when needed.
WHISPER_BIN = shutil.which("whisper")

# ─── ENV SAFETY CHECK ───
from dotenv import load_dotenv

load_dotenv()

# Read API host from environment with a default for local development.
API_HOST = os.getenv("VITE_API_HOST", "http://localhost:8000")
if os.getenv("VITE_API_HOST") is None:
    system_log.warning("VITE_API_HOST not set, defaulting to http://localhost:8000")

# ─── DB Lock ───
db_lock = threading.RLock()


# ─── Lifespan Hook ───
@asynccontextmanager
async def lifespan(app: FastAPI):
    system_log.info("App startup — lifespan entering.")
    validate_or_initialize_database()
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

from typing import Union


def get_duration(path: Union[str, os.PathLike]) -> float:
    if shutil.which("ffprobe") is None:
        raise RuntimeError("ffprobe not found in PATH. Required to determine duration.")

    try:
        out = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(path),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        return float(out.stdout.strip())
    except Exception:
        return 0.0


def handle_whisper(job_id: str, upload: Path, job_dir: Path, model: str):
    global WHISPER_BIN
    WHISPER_BIN = WHISPER_BIN or shutil.which("whisper")
    if not WHISPER_BIN:
        raise RuntimeError(
            "Whisper CLI not found in PATH. Is it installed and in the environment?"
        )

    with db_lock:
        with SessionLocal() as db:
            job = db.query(Job).filter_by(id=job_id).first()
            if job:
                job.status = JobStatusEnum.PROCESSING
                db.commit()

    def _run():
        log_path = LOG_DIR / f"{job_id}.log"
        logger = get_logger(job_id)
        logger.info("_run() started")

        try:
            job_dir.mkdir(parents=True, exist_ok=True)
            output_filename = Path(upload).stem + ".srt"

            cmd = [
                WHISPER_BIN,
                str(upload),
                "--model",
                model,
                "--model_dir",
                str(MODEL_DIR),
                "--output_dir",
                str(job_dir),
                "--output_format",
                "srt",
                "--language",
                "en",
                "--verbose",
                "True",
            ]
            logger.info(f"Launching subprocess: {' '.join(cmd)}")
            logger.info(f"FINAL CMD: {' '.join(cmd)}")

            try:
                with Popen(cmd, stdout=PIPE, stderr=PIPE, text=True, bufsize=1) as proc:

                    def stream_output(stream, label):
                        for line in iter(stream.readline, ""):
                            logger.info(f"{label}: {line.strip()}")

                    stdout_thread = threading.Thread(
                        target=stream_output, args=(proc.stdout, "STDOUT")
                    )
                    stderr_thread = threading.Thread(
                        target=stream_output, args=(proc.stderr, "STDERR")
                    )
                    stdout_thread.start()
                    stderr_thread.start()

                    proc.wait()
                    stdout_thread.join()
                    stderr_thread.join()
                    logger.info(f"Whisper exited with code {proc.returncode}")

            except subprocess.TimeoutExpired:
                logger.error("Whisper timed out")
                proc.kill()
                with db_lock:
                    with SessionLocal() as db:
                        job = db.query(Job).filter_by(id=job_id).first()
                        if job:
                            job.status = JobStatusEnum.FAILED_TIMEOUT
                            job.log_path = str(log_path)
                            db.commit()
                return

            except Exception as e:
                logger.error(f"Subprocess launch failed: {e}")
                with db_lock:
                    with SessionLocal() as db:
                        job = db.query(Job).filter_by(id=job_id).first()
                        if job:
                            job.status = JobStatusEnum.FAILED_LAUNCH_ERROR
                            job.log_path = str(log_path)
                            db.commit()
                return

            raw_txt_path = job_dir / (Path(upload).with_suffix(".srt").name)
            if not raw_txt_path.exists():
                raise RuntimeError(
                    f"[{job_id}] Expected .srt not found at {raw_txt_path}"
                )

            with db_lock:
                with SessionLocal() as db:
                    if proc.returncode == 0:
                        try:
                            logger.info("Starting metadata_writer...")
                            duration = get_duration(upload)
                            job = db.query(Job).filter_by(id=job_id).first()
                            if job:
                                job.status = JobStatusEnum.ENRICHING
                                db.commit()
                                run_metadata_writer(
                                    job_id,
                                    raw_txt_path,
                                    duration,
                                    16000,
                                    db_lock,  # type: ignore[arg-type]
                                )
                                logger.info("metadata_writer complete.")
                                with SessionLocal() as db2:  # NEW clean session
                                    job2 = db2.query(Job).filter_by(id=job_id).first()
                                    if job2:
                                        job2.status = JobStatusEnum.COMPLETED
                                        job2.transcript_path = str(raw_txt_path)
                                        db2.commit()
                                        logger.info(
                                            "status -> COMPLETED committed"
                                        )  # debug breadcrumb
                        except Exception as e:
                            job = db.query(Job).filter_by(id=job_id).first()
                            if job:
                                job.status = JobStatusEnum.FAILED_UNKNOWN
                                job.log_path = str(log_path)
                                logger.error(f"Metadata writer failed: {e}")
                            db.commit()
                    elif proc.returncode < 0:
                        logger.error(
                            f"Whisper process terminated with signal {-proc.returncode}"
                        )
                        job = db.query(Job).filter_by(id=job_id).first()
                        if job:
                            job.status = JobStatusEnum.FAILED_WHISPER_ERROR
                            job.log_path = str(log_path)
                            db.commit()
                        logger.error(
                            f"Whisper process terminated with signal {-proc.returncode}"
                        )
                    else:
                        logger.error("Whisper process failed — not zero return code")
                        job = db.query(Job).filter_by(id=job_id).first()
                        if job:
                            job.status = JobStatusEnum.FAILED_WHISPER_ERROR
                            job.log_path = str(log_path)
        except Exception as e:
            logger.critical(f"CRITICAL thread error: {e}")
            with db_lock:
                with SessionLocal() as db:
                    job = db.query(Job).filter_by(id=job_id).first()
                    if job:
                        job.status = JobStatusEnum.FAILED_THREAD_EXCEPTION
                        job.log_path = str(log_path)
                        db.commit()

    threading.Thread(target=_run, daemon=True).start()


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
