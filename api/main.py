import os
import uuid
import time
import shutil
import sqlite3
import threading
import subprocess
import zipfile
import io

from datetime import datetime
from subprocess import Popen, PIPE
from pathlib import Path
from contextlib import asynccontextmanager

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

# ─── Logging ───
backend_log = get_logger("backend")

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
db_lock = threading.Lock()

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

# ─── Lifespan Hook ───
@asynccontextmanager
async def lifespan(app: FastAPI):
    rehydrate_incomplete_jobs()
    yield

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

# ─── DB Schema ───
def init_db():
    with get_conn() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS metadata (
            job_id TEXT PRIMARY KEY,
            tokens INTEGER,
            duration REAL,
            abstract TEXT,
            sample_rate INTEGER,
            generated_at TEXT
        )
        """)
        conn.commit()

init_db()

@app.middleware("http")
async def access_logger(request: Request, call_next):
    start = time.time()
    resp = await call_next(request)
    dur = time.time() - start
    host = getattr(request.client, "host", "localtest")
    with ACCESS_LOG.open("a", encoding="utf-8") as fh:
        fh.write(f"[{datetime.utcnow().isoformat()}] {host} "
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
        with get_conn() as conn:
            conn.execute("UPDATE jobs SET status = 'processing' WHERE id = ?", (job_id,))
            conn.commit()

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
                    with get_conn() as conn:
                        conn.execute(
                            "UPDATE jobs SET status = ?, log_path = ? WHERE id = ?",
                            ("failed: timeout", str(log_path), job_id)
                        )
                        conn.commit()
                return

            except Exception as e:
                logger.error(f"Subprocess launch failed: {e}")
                with db_lock:
                    with get_conn() as conn:
                        conn.execute(
                            "UPDATE jobs SET status = ?, log_path = ? WHERE id = ?",
                            (f"failed: launch error: {e}", str(log_path), job_id)
                        )
                        conn.commit()
                return

            raw_txt_path = job_dir / (Path(upload).with_suffix(".srt").name)
            if not raw_txt_path.exists():
                raise RuntimeError(f"[{job_id}] Expected .srt not found at {raw_txt_path}")

            with db_lock:
                with get_conn() as conn:
                    if proc.returncode == 0:
                        try:
                            logger.info("Starting metadata_writer...")
                            duration = get_duration(upload)
                            conn.execute("UPDATE jobs SET status = 'enriching' WHERE id = ?", (job_id,))
                            conn.commit()
                            run_metadata_writer(job_id, raw_txt_path, duration, 16000, db_lock)
                            logger.info("metadata_writer complete.")
                            conn.execute(
                                "UPDATE jobs SET status = 'completed', transcript_path = ? WHERE id = ?",
                                (str(raw_txt_path), job_id)
                            )
                        except Exception as e:
                            logger.error(f"Metadata failure: {e}")
                            conn.execute(
                                "UPDATE jobs SET status = ?, log_path = ? WHERE id = ?",
                                (f"failed: {e}", str(log_path), job_id)
                            )
                    else:
                        logger.error("Whisper process failed — not zero return code")
                        conn.execute(
                            "UPDATE jobs SET status = ?, log_path = ? WHERE id = ?",
                            ("failed: whisper error", str(log_path), job_id)
                        )
                    conn.commit()
        except Exception as e:
            logger.critical(f"CRITICAL thread error: {e}")
            with db_lock:
                with get_conn() as conn:
                    conn.execute(
                        "UPDATE jobs SET status = ?, log_path = ? WHERE id = ?",
                        (f"failed: thread exception: {e}", str(log_path), job_id)
                    )
                    conn.commit()



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

    ts = datetime.utcnow().isoformat()
    with db_lock:
        with get_conn() as conn:
            conn.execute(
                "INSERT INTO jobs (id, original_filename, saved_filename, model, created_at, status) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (job_id, file.filename, saved, model, ts, "queued")
            )
            conn.commit()
    backend_log.info(f"Job {job_id} created.")
    handle_whisper(job_id, upload_path, job_dir, model)
    return {"job_id": job_id}

@app.get("/jobs")
def list_jobs():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, original_filename, model, created_at, status FROM jobs ORDER BY created_at DESC"
        ).fetchall()
    return [dict(row) for row in rows]

@app.get("/jobs/{job_id}")
def get_job(job_id: str):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id, original_filename, model, created_at, status FROM jobs WHERE id=?",
            (job_id,)
        ).fetchone()
    if not row:
        raise http_error(ErrorCode.JOB_NOT_FOUND)
    return dict(row)

@app.delete("/jobs/{job_id}")
def delete_job(job_id: str):
    with db_lock:
        with get_conn() as conn:
            row = conn.execute("SELECT saved_filename FROM jobs WHERE id=?", (job_id,)).fetchone()
            if not row:
                raise http_error(ErrorCode.JOB_NOT_FOUND)

            saved_filename = row["saved_filename"]
            transcript_dir = TRANSCRIPTS_DIR / job_id
            upload_path = UPLOAD_DIR / saved_filename
            log_path = LOG_DIR / f"{job_id}.log"  # ✅ new line

            # Remove transcript folder (recursive)
            shutil.rmtree(transcript_dir, ignore_errors=True)

            # Remove uploaded audio
            try:
                upload_path.unlink()
            except FileNotFoundError:
                pass

            # ✅ Remove log file
            try:
                log_path.unlink()
            except FileNotFoundError:
                pass

            conn.execute("DELETE FROM jobs WHERE id=?", (job_id,))
            conn.commit()

    backend_log.info(f"Deleted job {job_id} and associated files")
    return {"status": "deleted"}


@app.get("/logs/access", response_class=PlainTextResponse)
def get_access_log():
    return ACCESS_LOG.read_text()

def rehydrate_incomplete_jobs():
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, saved_filename, model FROM jobs "
            "WHERE status IN ('queued', 'processing', 'enriching')"
        )
        for job_id, saved_filename, model in cur.fetchall():
            backend_log.info(f"Rehydrating job {job_id} with model '{model}'")
            try:
                upload_path = UPLOAD_DIR / saved_filename
                job_dir = TRANSCRIPTS_DIR / job_id
                handle_whisper(job_id, upload_path, job_dir, model)
            except Exception as e:
                backend_log.error(f"Failed to rehydrate job {job_id}: {e}")

@app.get("/jobs/{job_id}/download")
def download_transcript(job_id: str):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT transcript_path, original_filename FROM jobs WHERE id=?",
            (job_id,)
        ).fetchone()
    if not row:
        backend_log.warning(f"Download failed: job {job_id} not found")
        raise http_error(ErrorCode.JOB_NOT_FOUND)

    srt_path = Path(row["transcript_path"])  # 🔥 Fix here
    if not srt_path.exists():
        backend_log.error(f"Transcript file missing for job {job_id} at {srt_path}")
        raise http_error(ErrorCode.FILE_NOT_FOUND)

    original_name = Path(row["original_filename"]).stem + ".srt"
    return FileResponse(
        path=srt_path,
        media_type="text/plain",
        filename=original_name  # ✅ matches upload name
    )

@app.get("/transcript/{job_id}/view", response_class=HTMLResponse)
def transcript_view(job_id: str, request: Request):
    with get_conn() as conn:
        row = conn.execute("SELECT transcript_path FROM jobs WHERE id=?", (job_id,)).fetchone()

    if not row:
        return HTMLResponse(content=f"<h2>Job not found: {job_id}</h2>", status_code=404)

    transcript_path = row["transcript_path"]

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
        with get_conn() as conn:
            row = conn.execute("SELECT saved_filename, model FROM jobs WHERE id=?", (job_id,)).fetchone()
            if not row:
                raise http_error(ErrorCode.JOB_NOT_FOUND)

            saved_filename, model = row["saved_filename"], row["model"]
            upload_path = UPLOAD_DIR / saved_filename
            job_dir = TRANSCRIPTS_DIR / job_id

            if not upload_path.exists():
                raise http_error(ErrorCode.FILE_NOT_FOUND)

            # Clear old transcript folder if it exists
            shutil.rmtree(job_dir, ignore_errors=True)

            conn.execute("UPDATE jobs SET status = 'queued' WHERE id = ?", (job_id,))
            conn.commit()

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
        with get_conn() as conn:
            conn.execute("DELETE FROM jobs")
            conn.commit()

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

@app.get("/logs/{filename}", response_class=PlainTextResponse)
def get_log_file(filename: str):
    path = LOG_DIR / filename
    if not path.exists():
        raise http_error(ErrorCode.FILE_NOT_FOUND)
    return path.read_text()