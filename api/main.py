import os
import uuid
import time
import shutil
import logging
import sqlite3
import subprocess
from datetime import datetime
from subprocess import Popen

from fastapi import FastAPI, UploadFile, File, Form, Request, Query
from fastapi.responses import JSONResponse, FileResponse, PlainTextResponse
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware

from api.metadata_writer import run_metadata_writer

UPLOAD_DIR = "uploads"
TRANSCRIPTS_DIR = "transcripts"
MODEL_DIR = "models"
LOG_DIR = "logs"
ACCESS_LOG = os.path.join(LOG_DIR, "access.log")
FRONTEND_LOG = os.path.join(LOG_DIR, "frontend.log")
DB_PATH = "jobs.db"

for path in [UPLOAD_DIR, TRANSCRIPTS_DIR, MODEL_DIR, LOG_DIR]:
    os.makedirs(path, exist_ok=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("whisper")

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

@app.middleware("http")
async def access_logger(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    log_line = f"[{datetime.utcnow().isoformat()}] {request.client.host} {request.method} {request.url.path} -> {response.status_code} in {duration:.2f}s\n"
    with open(ACCESS_LOG, "a", encoding="utf-8") as f:
        f.write(log_line)
    return response

def get_duration(filepath: str) -> float:
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries",
             "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", filepath],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        return float(result.stdout.decode().strip())
    except Exception as e:
        return 0.0

def handle_whisper_job(job_id, upload_path, log_path, job_dir, model):
    txt_path = os.path.join(job_dir, "raw.txt")
    cmd = [
        "whisper", upload_path,
        "--model", model,
        "--model_dir", MODEL_DIR,
        "--output_dir", job_dir,
        "--output_format", "txt",
        "--language", "en",
        "--verbose", "True"
    ]

    def run():
        os.makedirs(job_dir, exist_ok=True)
        with open(log_path, "w", encoding="utf-8") as log_fp:
            process = Popen(cmd, stdout=log_fp, stderr=log_fp)
            process.wait()

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        if os.path.exists(txt_path):
            duration = get_duration(upload_path)
            cur.execute("UPDATE jobs SET status = ? WHERE id = ?", ("enriching", job_id))
            conn.commit()

            try:
                run_metadata_writer(job_id, txt_path, duration_sec=duration, sample_rate=16000)
                md_path = os.path.join(job_dir, "transcript.md")
                cur.execute("UPDATE jobs SET status = ?, transcript_path = ? WHERE id = ?", ("completed", md_path, job_id))
            except Exception as e:
                cur.execute("UPDATE jobs SET status = ?, error_message = ? WHERE id = ?", ("failed", str(e), job_id))
        else:
            cur.execute("UPDATE jobs SET status = ?, error_message = ? WHERE id = ?", ("failed", "Transcript file not found", job_id))
        conn.commit()
        conn.close()

    import threading
    threading.Thread(target=run).start()

@app.post("/log_event")
async def log_frontend_event(payload: dict):
    timestamp = datetime.utcnow().isoformat()
    with open(FRONTEND_LOG, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {jsonable_encoder(payload)}\n")
    return {"status": "logged"}

@app.get("/log/access")
def read_access_log():
    return PlainTextResponse(open(ACCESS_LOG, "r", encoding="utf-8").read())

@app.post("/jobs")
async def submit_job(file: UploadFile = File(...), model: str = Form("tiny")):
    job_id = str(uuid.uuid4())
    saved_filename = f"{job_id}_{file.filename}"
    upload_path = os.path.join(UPLOAD_DIR, saved_filename)
    log_path = os.path.join(LOG_DIR, f"{job_id}.log")
    job_dir = os.path.join(TRANSCRIPTS_DIR, job_id)

    with open(upload_path, "wb") as out_file:
        shutil.copyfileobj(file.file, out_file)

    timestamp = datetime.utcnow().isoformat()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO jobs (id, original_filename, saved_filename, model, created_at, status)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (job_id, file.filename, saved_filename, model, timestamp, "processing"))
    conn.commit()
    conn.close()

    handle_whisper_job(job_id, upload_path, log_path, job_dir, model)
    return {"job_id": job_id}

@app.get("/jobs")
def list_jobs(status: str = Query(None)):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    if status:
        cur.execute("SELECT id, original_filename, saved_filename, model, created_at, status FROM jobs WHERE status = ? ORDER BY created_at DESC", (status,))
    else:
        cur.execute("SELECT id, original_filename, saved_filename, model, created_at, status FROM jobs ORDER BY created_at DESC")
    rows = cur.fetchall()
    conn.close()
    return jsonable_encoder([
        {"id": r[0], "original_filename": r[1], "saved_filename": r[2], "model": r[3], "created_at": r[4], "status": r[5]} for r in rows
    ])

@app.get("/transcript/{job_id}")
def get_transcript(job_id: str):
    md_path = os.path.join(TRANSCRIPTS_DIR, job_id, "transcript.md")
    if not os.path.exists(md_path):
        return JSONResponse(status_code=404, content={"error": "Transcript not found"})
    return FileResponse(md_path, media_type="text/markdown", filename="transcript.md")

@app.get("/transcript/{job_id}/view")
def get_transcript_text(job_id: str):
    md_path = os.path.join(TRANSCRIPTS_DIR, job_id, "transcript.md")
    if not os.path.exists(md_path):
        return JSONResponse(status_code=404, content={"error": "Transcript not found"})
    with open(md_path, "r", encoding="utf-8") as f:
        return {"text": f.read()}

@app.post("/jobs/{job_id}/restart")
def restart_job(job_id: str, model: str = Form("tiny")):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT original_filename, saved_filename FROM jobs WHERE id = ?", (job_id,))
    row = cur.fetchone()
    conn.close()

    if not row:
        return JSONResponse(status_code=404, content={"error": "Original job not found"})

    filename, saved = row
    full_path = os.path.join(UPLOAD_DIR, saved)
    log_path = os.path.join(LOG_DIR, f"{job_id}.log")
    job_dir = os.path.join(TRANSCRIPTS_DIR, job_id)

    if not os.path.exists(full_path):
        return JSONResponse(status_code=404, content={"error": "Original file missing"})

    timestamp = datetime.utcnow().isoformat()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("UPDATE jobs SET model = ?, created_at = ?, status = ?, transcript_path = NULL, error_message = NULL WHERE id = ?", (model, timestamp, "processing", job_id))
    conn.commit()
    conn.close()

    handle_whisper_job(job_id, full_path, log_path, job_dir, model)
    return {"status": "restarted"}

@app.delete("/jobs/{job_id}")
def delete_job(job_id: str):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT saved_filename FROM jobs WHERE id = ?", (job_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return JSONResponse(status_code=404, content={"error": "Job not found"})

    upload_path = os.path.join(UPLOAD_DIR, row[0])
    job_dir = os.path.join(TRANSCRIPTS_DIR, job_id)
    if os.path.exists(upload_path): os.remove(upload_path)
    if os.path.exists(job_dir): shutil.rmtree(job_dir)
    cur.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
    conn.commit()
    conn.close()
    return {"status": "deleted"}

@app.get("/audio/{job_id}")
def get_original_audio(job_id: str):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT saved_filename FROM jobs WHERE id = ?", (job_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return JSONResponse(status_code=404, content={"error": "Audio not found"})
    path = os.path.join(UPLOAD_DIR, row[0])
    if not os.path.exists(path):
        return JSONResponse(status_code=404, content={"error": "Audio file missing"})
    return FileResponse(path, media_type="audio/mpeg", filename=os.path.basename(path))
