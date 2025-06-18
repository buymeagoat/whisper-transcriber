import os
import uuid
import time
import shutil
import threading
import subprocess
import zipfile
import io

from datetime import timezone
from datetime import datetime
from subprocess import Popen, PIPE
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import HTTPException
from fastapi import FastAPI, UploadFile, File, Form, Request, status
from fastapi.responses import (
    FileResponse,
    PlainTextResponse,
    HTMLResponse,
    StreamingResponse
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.metadata_writer import run_metadata_writer
from api.errors import ErrorCode, http_error
from api.utils.logger import get_logger
from api.orm_bootstrap import SessionLocal
from api.models import Job
from api.models import JobStatusEnum 
from api.utils.logger import get_system_logger
from zoneinfo import ZoneInfo
LOCAL_TZ = ZoneInfo("America/Chicago")
import psutil

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
DB_PATH = ROOT / "jobs.db"


# ─── Ensure Required Dirs Exist ───
for p in (UPLOAD_DIR, TRANSCRIPTS_DIR, MODEL_DIR, LOG_DIR):
    p.mkdir(parents=True, exist_ok=True)

# ─── Whisper CLI Check ───
WHISPER_BIN = shutil.which("whisper")
if not WHISPER_BIN:
    raise RuntimeError("Whisper CLI not found in PATH. Is it installed and in the environment?")

# ─── ENV SAFETY CHECK ───
from dotenv import load_dotenv
load_dotenv()

REQUIRED_ENV_VARS = ["VITE_API_HOST"]
missing_env = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]
if missing_env:
    raise RuntimeError(f"Missing required environment variables: {', '.join(missing_env)}")

# ─── DB Lock ───
db_lock = threading.RLock()

# ─── Lifespan Hook ───
@asynccontextmanager
async def lifespan(app: FastAPI):
    system_log.info("App startup — lifespan entering.")
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
        fh.write(f"[{datetime.now(LOCAL_TZ).isoformat()}] {host} "
                 f"{request.method} {request.url.path} -> "
                 f"{resp.status_code} in {dur:.2f}s\n")
    return resp

# ─── Static File Routes ───
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR, html=True), name="uploads")
app.mount("/transcripts", StaticFiles(directory=TRANSCRIPTS_DIR, html=True), name="transcripts")

# ─── Debug Output ───
print("\nSTATIC ROUTE CHECK:")
for route in app.routes:
    print(f"Path: {getattr(route, 'path', 'n/a')}  →  Name: {getattr(route, 'name', 'n/a')}  →  Type: {type(route)}")

from typing import Union
def get_duration(path: Union[str, os.PathLike]) -> float:
    if shutil.which("ffprobe") is None:
        raise RuntimeError("ffprobe not found in PATH. Required to determine duration.")

    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        return float(out.stdout.strip())
    except Exception:
        return 0.0

def handle_whisper(job_id: str, upload: Path, job_dir: Path, model: str):
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
                WHISPER_BIN, str(upload),
                "--model", model,
                "--model_dir", str(MODEL_DIR),
                "--output_dir", str(job_dir),
                "--output_format", "srt",
                "--language", "en",
                "--verbose", "True"
            ]
            logger.info(f"Launching subprocess: {' '.join(cmd)}")
            logger.info(f"FINAL CMD: {' '.join(cmd)}")

            try:
                with Popen(cmd, stdout=PIPE, stderr=PIPE, text=True, bufsize=1) as proc:
                    def stream_output(stream, label):
                        for line in iter(stream.readline, ''):
                            logger.info(f"{label}: {line.strip()}")

                    stdout_thread = threading.Thread(target=stream_output, args=(proc.stdout, "STDOUT"))
                    stderr_thread = threading.Thread(target=stream_output, args=(proc.stderr, "STDERR"))
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
                raise RuntimeError(f"[{job_id}] Expected .srt not found at {raw_txt_path}")

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
                                    db_lock  # type: ignore[arg-type] 
                                )
                                logger.info("metadata_writer complete.")
                                with SessionLocal() as db2:                      # NEW clean session
                                    job2 = db2.query(Job).filter_by(id=job_id).first()
                                    if job2:
                                        job2.status = JobStatusEnum.COMPLETED
                                        job2.transcript_path = str(raw_txt_path)
                                        db2.commit()
                                        logger.info("status -> COMPLETED committed")   # debug breadcrumb
                        except Exception as e:
                            job = db.query(Job).filter_by(id=job_id).first()
                            if job:
                                job.status = JobStatusEnum.FAILED_UNKNOWN
                                job.log_path = str(log_path)
                                logger.error(f"Metadata writer failed: {e}")
                            db.commit()
                    elif proc.returncode < 0:
                        logger.error(f"Whisper process terminated with signal {-proc.returncode}")
                        job = db.query(Job).filter_by(id=job_id).first()
                        if job:
                            job.status = JobStatusEnum.FAILED_WHISPER_ERROR
                            job.log_path = str(log_path)
                            db.commit()
                        logger.error(f"Whisper process terminated with signal {-proc.returncode}")
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
                    with SessionLocal() as db:
                        job = db.query(Job).filter_by(id=job_id).first()
                        if job:
                            job.status = JobStatusEnum.FAILED_THREAD_EXCEPTION
                            job.log_path = str(log_path)
                            db.commit()



    threading.Thread(target=_run, daemon=True).start()

@app.post("/jobs", status_code=status.HTTP_202_ACCEPTED)
async def submit_job(file: UploadFile = File(...), model: str = Form("base")):
    job_id = uuid.uuid4().hex
    saved = f"{job_id}_{file.filename}"
    upload_path = UPLOAD_DIR / saved
    job_dir = TRANSCRIPTS_DIR / job_id

    try:
        with upload_path.open("wb") as dst:
            shutil.copyfileobj(file.file, dst)
    except Exception as e:
        backend_log.error(f"File save failed for job {job_id}: {e}")
        raise http_error(ErrorCode.FILE_SAVE_FAILED)

    ts = datetime.now(LOCAL_TZ)
    with db_lock:
        with SessionLocal() as db:
            job = Job(
                id=job_id,
                original_filename=file.filename,
                saved_filename=saved,
                model=model,
                created_at=ts,
                status=JobStatusEnum.QUEUED
            )
            db.add(job)
            db.commit()
    backend_log.info(f"Job {job_id} created.")
    handle_whisper(job_id, upload_path, job_dir, model)
    return {"job_id": job_id}

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/jobs")
def list_jobs():
    with SessionLocal() as db:
        jobs = db.query(Job).order_by(Job.created_at.desc()).all()
        return [
            {
                "id": j.id,
                "original_filename": j.original_filename,
                "model": j.model,
                "created_at": j.created_at.isoformat(),
                "status": j.status.value,
            }
            for j in jobs
        ]

@app.get("/jobs/{job_id}")
def get_job(job_id: str):
    with SessionLocal() as db:
        job = db.query(Job).filter_by(id=job_id).first()
        if not job:
            raise http_error(ErrorCode.JOB_NOT_FOUND)
        return {
            "id": job.id,
            "original_filename": job.original_filename,
            "model": job.model,
            "created_at": job.created_at.isoformat(),
            "status": job.status.value,
        }

@app.delete("/jobs/{job_id}")
def delete_job(job_id: str):
    with db_lock:
        with SessionLocal() as db:
            job = db.query(Job).filter_by(id=job_id).first()
            if not job:
                raise http_error(ErrorCode.JOB_NOT_FOUND)

            saved_filename = job.saved_filename
            transcript_dir = TRANSCRIPTS_DIR / job_id
            upload_path = UPLOAD_DIR / saved_filename
            log_path = LOG_DIR / f"{job_id}.log"

            shutil.rmtree(transcript_dir, ignore_errors=True)

            try:
                upload_path.unlink()
            except FileNotFoundError:
                pass

            try:
                log_path.unlink()
            except FileNotFoundError:
                pass

            db.delete(job)
            db.commit()

        backend_log.info(f"Deleted job {job_id} and associated files")
        return {"status": "deleted"}


@app.get("/logs/access", response_class=PlainTextResponse)
def get_access_log():
    return ACCESS_LOG.read_text()

def rehydrate_incomplete_jobs():
    with SessionLocal() as db:
        jobs = db.query(Job).filter(Job.status.in_([
            JobStatusEnum.QUEUED,
            JobStatusEnum.PROCESSING,
            JobStatusEnum.ENRICHING
        ])).all()
        for job in jobs:
            backend_log.info(f"Rehydrating job {job.id} with model '{job.model}'")
            try:
                upload_path = UPLOAD_DIR / job.saved_filename
                job_dir = TRANSCRIPTS_DIR / job.id
                handle_whisper(job.id, upload_path, job_dir, job.model)
            except Exception as e:
                backend_log.error(f"Failed to rehydrate job {job.id}: {e}")


@app.get("/jobs/{job_id}/download")
def download_transcript(job_id: str):
    with SessionLocal() as db:
        job = db.query(Job).filter_by(id=job_id).first()
        if not job:
            backend_log.warning(f"Download failed: job {job_id} not found")
            raise http_error(ErrorCode.JOB_NOT_FOUND)

        if not job.transcript_path:
            backend_log.error(f"Transcript path is missing for job {job_id}")
            raise http_error(ErrorCode.FILE_NOT_FOUND)

        srt_path = Path(job.transcript_path)
        if not srt_path.exists():
            backend_log.error(f"Transcript file missing for job {job_id} at {srt_path}")
            raise http_error(ErrorCode.FILE_NOT_FOUND)

        original_name = Path(job.original_filename).stem + ".srt"
        return FileResponse(
            path=srt_path,
            media_type="text/plain",
            filename=original_name
        )

@app.get("/transcript/{job_id}/view", response_class=HTMLResponse)
def transcript_view(job_id: str, request: Request):
    with SessionLocal() as db:
        job = db.query(Job).filter_by(id=job_id).first()
        if not job:
            return HTMLResponse(content=f"<h2>Job not found: {job_id}</h2>", status_code=404)

        transcript_path = job.transcript_path

    if not transcript_path:
        return HTMLResponse(content=f"<h2>No transcript available for job {job_id}</h2>", status_code=404)

    transcript_file = Path(transcript_path)
    if not transcript_file.exists():
        return HTMLResponse(content=f"<h2>Transcript file not found at {transcript_file}</h2>", status_code=404)

    transcript_text = transcript_file.read_text(encoding="utf-8")
    html = f"""
    <html>
      <head>
        <title>Transcript for {job_id}</title>
        <style>
          body {{ background: #111; color: #eee; font-family: monospace; padding: 2rem; }}
          pre {{ white-space: pre-wrap; word-wrap: break-word; }}
        </style>
      </head>
      <body>
        <h1>Transcript for Job ID: {job_id}</h1>
        <pre>{transcript_text}</pre>
      </body>
    </html>
    """
    return HTMLResponse(content=html)

@app.post("/jobs/{job_id}/restart")
def restart_job(job_id: str):
    with db_lock:
        with SessionLocal() as db:
            job = db.query(Job).filter_by(id=job_id).first()
            if not job:
                raise http_error(ErrorCode.JOB_NOT_FOUND)

            saved_filename = job.saved_filename
            model = job.model
            upload_path = UPLOAD_DIR / saved_filename
            job_dir = TRANSCRIPTS_DIR / job_id

            if not upload_path.exists():
                raise http_error(ErrorCode.FILE_NOT_FOUND)

            shutil.rmtree(job_dir, ignore_errors=True)

            job.status = JobStatusEnum.QUEUED
            db.commit()

    backend_log.info(f"Restarting job {job_id}")
    handle_whisper(job_id, upload_path, job_dir, model)
    return {"status": "restarted"}

@app.get("/log/{job_id}", response_class=PlainTextResponse)
def get_job_log(job_id: str):
    log_path = LOG_DIR / f"{job_id}.log"
    if not log_path.exists():
        return PlainTextResponse("No log yet.", status_code=404)
    return log_path.read_text(encoding="utf-8")

@app.post("/log_event")
async def log_event(request: Request):
    try:
        payload = await request.json()
        event = payload.get("event", "unknown")
        context = payload.get("context", {})
        backend_log.info(f"Client Event: {event} | Context: {context}")
        return {"status": "logged"}
    except Exception as e:
        backend_log.error(f"Failed to log client event: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/admin/files")
def list_admin_files():
    logs = sorted(f.name for f in LOG_DIR.glob("*") if f.is_file())
    uploads = sorted(f.name for f in UPLOAD_DIR.glob("*") if f.is_file())
    transcripts = sorted(str(f.relative_to(TRANSCRIPTS_DIR)) for f in TRANSCRIPTS_DIR.rglob("*") if f.is_file())

    print("LOG_DIR:", LOG_DIR.resolve())
    print("UPLOAD_DIR:", UPLOAD_DIR.resolve())
    print("TRANSCRIPTS_DIR:", TRANSCRIPTS_DIR.resolve())
    print("Logs found:", logs)
    print("Uploads found:", uploads)
    print("Transcripts found:", transcripts)

    return {
        "logs": logs,
        "uploads": uploads,
        "transcripts": transcripts
    }

@app.delete("/admin/files")
def delete_admin_file(payload: dict):
    folder = payload.get("folder")
    filename = payload.get("filename")

    folder_map = {
        "logs": LOG_DIR,
        "uploads": UPLOAD_DIR,
        "transcripts": TRANSCRIPTS_DIR
    }

    if folder not in folder_map or not filename:
        raise http_error(ErrorCode.FILE_SAVE_FAILED)

    target = folder_map[folder] / filename
    if not target.exists() or not target.is_file():
        raise http_error(ErrorCode.FILE_NOT_FOUND)

    target.unlink()
    return { "status": "deleted" }

@app.post("/admin/reset")
def reset_system():
    with db_lock:
        with SessionLocal() as db:
            db.query(Job).delete()
            db.commit()

    for directory in [UPLOAD_DIR, TRANSCRIPTS_DIR, LOG_DIR]:
        for file in directory.rglob("*"):
            if file.is_file():
                file.unlink()
            elif file.is_dir():
                shutil.rmtree(file, ignore_errors=True)

    return { "status": "reset complete" }

@app.get("/admin/download-all")
def download_all():
    mem_zip = io.BytesIO()

    with zipfile.ZipFile(mem_zip, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for dir_path, prefix in [(LOG_DIR, "logs"), (UPLOAD_DIR, "uploads"), (TRANSCRIPTS_DIR, "transcripts")]:
            for file in dir_path.rglob("*"):
                if file.is_file():
                    arcname = f"{prefix}/{file.relative_to(dir_path)}"
                    zf.write(file, arcname)

    mem_zip.seek(0)
    return StreamingResponse(mem_zip, media_type="application/zip", headers={
        "Content-Disposition": "attachment; filename=all_data.zip"
    })
# ── NEW: /admin/stats ─────────────────────────────────────
@app.get("/admin/stats")
def admin_stats():
    """Return simple CPU and memory metrics for the running container."""
    cpu_percent = psutil.cpu_percent(interval=0.1)
    mem = psutil.virtual_memory()
    return {
        "cpu_percent": cpu_percent,
        "mem_used_mb": round(mem.used / (1024 * 1024), 1),
        "mem_total_mb": round(mem.total / (1024 * 1024), 1)
    }
# ──────────────────────────────────────────────────────────

@app.get("/logs/{filename}", response_class=PlainTextResponse)
def get_log_file(filename: str):
    path = LOG_DIR / filename
    if not path.exists():
        raise http_error(ErrorCode.FILE_NOT_FOUND)
    return path.read_text()

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
        "static", "uploads", "transcripts", "jobs",
        "log", "admin/files", "admin/reset", "admin/download-all",
        "health", "docs", "openapi.json"
    )
    if full_path.startswith(protected):
        raise HTTPException(status_code=404, detail="Not Found")

    # Everything else is a front-end route -> serve React bundle
    return FileResponse(static_dir / "index.html")
# ─────────────────────────────────────────────────────────────────