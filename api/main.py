import os
import uuid
import shutil
import subprocess
import json
import hashlib
import mimetypes
import traceback
import time
from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.responses import JSONResponse
from datetime import datetime

app = FastAPI()

UPLOAD_DIR = "uploads"
OUTPUT_DIR = "outputs"
LOG_DIR = "logs"
MODEL_DIR = "models"
ACCESS_LOG = os.path.join(LOG_DIR, "access.log")
ALLOWED_MODELS = {"tiny", "base", "small", "medium", "large"}
ALLOWED_EXT = (".m4a", ".mp3", ".wav")
MAX_SIZE_BYTES = 100 * 1024 * 1024

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(MODEL_DIR, exist_ok=True)

def log_event(log_fp, message):
    timestamp = datetime.utcnow().isoformat()
    log_fp.write(f"[{timestamp}] {message}\n")
    log_fp.flush()

def compute_sha256(file_path):
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def log_access(request: Request, response_code: int, duration: float):
    timestamp = datetime.utcnow().isoformat()
    log_line = f"[{timestamp}] {request.client.host} {request.method} {request.url.path} -> {response_code} in {duration:.2f}s\n"
    with open(ACCESS_LOG, "a", encoding="utf-8") as log_fp:
        log_fp.write(log_line)

@app.middleware("http")
async def access_logger(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    log_access(request, response.status_code, duration)
    return response

@app.post("/jobs")
async def create_job(file: UploadFile = File(...), model: str = Form("tiny")):
    overall_start = time.time()
    job_id = str(uuid.uuid4())
    filename = f"{job_id}_{file.filename}"
    upload_path = os.path.join(UPLOAD_DIR, filename)
    log_path = os.path.join(LOG_DIR, f"{job_id}.log")
    output_txt = os.path.join(OUTPUT_DIR, f"{job_id}.txt")
    output_json = os.path.join(OUTPUT_DIR, f"{job_id}.json")

    try:
        if not file.filename.lower().endswith(ALLOWED_EXT):
            return JSONResponse(content={"error": "Unsupported file type."}, status_code=400)

        with open(upload_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        if os.path.getsize(upload_path) > MAX_SIZE_BYTES:
            os.remove(upload_path)
            return JSONResponse(content={"error": "File too large."}, status_code=400)

        if model not in ALLOWED_MODELS:
            return JSONResponse(content={"error": f"Invalid model '{model}'"}, status_code=400)

        with open(log_path, "w", encoding="utf-8") as log_fp:
            start_time = datetime.utcnow()
            log_event(log_fp, f"🟢 START job {job_id}")
            log_event(log_fp, f"📥 File saved to: {upload_path}")
            file_size = os.path.getsize(upload_path)
            mime_type, _ = mimetypes.guess_type(upload_path)
            file_hash = compute_sha256(upload_path)

            log_event(log_fp, f"📦 File size: {file_size} bytes")
            log_event(log_fp, f"📄 MIME type: {mime_type}")
            log_event(log_fp, f"🔐 SHA256: {file_hash}")
            log_event(log_fp, f"📊 Model selected: {model}")

            cmd = [
                "whisper", upload_path,
                "--model", model,
                "--model_dir", MODEL_DIR,
                "--language", "en",
                "--output_dir", OUTPUT_DIR,
                "--output_format", "txt",
                "--verbose", "True"
            ]

            log_event(log_fp, f"🧠 Executing command: {' '.join(cmd)}")

            transcribe_start = time.time()
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=1,
                universal_newlines=True
            )

            for line in process.stdout:
                log_fp.write(line)
                log_fp.flush()

            process.stdout.close()
            return_code = process.wait()
            transcribe_end = time.time()

            log_event(log_fp, f"🏁 Whisper return code: {return_code}")
            log_event(log_fp, f"🕓 Transcription duration: {round(transcribe_end - transcribe_start, 2)} sec")

            if not os.path.exists(output_txt):
                log_event(log_fp, f"❌ Output not found: {output_txt}")
                return JSONResponse(content={"error": "Transcription failed."}, status_code=500)

            end_time = datetime.utcnow()
            metadata = {
                "job_id": job_id,
                "input_file": upload_path,
                "output_file": output_txt,
                "language": "en",
                "model": model,
                "duration_sec": round((end_time - start_time).total_seconds(), 2),
                "started_utc": start_time.isoformat(),
                "finished_utc": end_time.isoformat(),
                "file_size_bytes": file_size,
                "file_sha256": file_hash,
                "mime_type": mime_type,
                "return_code": return_code
            }

            with open(output_json, "w", encoding="utf-8") as jf:
                json.dump(metadata, jf, indent=2)

            log_event(log_fp, f"✅ Completed: {output_txt}")
            log_event(log_fp, f"📄 Metadata saved: {output_json}")
            log_event(log_fp, f"⏳ Total job duration: {round(time.time() - overall_start, 2)} sec")

        return {
            "job_id": job_id,
            "output_txt": output_txt,
            "output_json": output_json,
            "log": log_path
        }

    except Exception as e:
        with open(log_path, "a", encoding="utf-8") as log_fp:
            log_event(log_fp, f"❌ Exception occurred: {str(e)}")
            log_event(log_fp, traceback.format_exc())
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.post("/log_event")
async def log_frontend_event(request: Request):
    try:
        body = await request.json()
    except:
        body = {"error": "invalid json"}

    timestamp = datetime.utcnow().isoformat()
    entry = f"[{timestamp}] {request.client.host} {json.dumps(body)}\n"

    frontend_log = os.path.join(LOG_DIR, "frontend.log")
    with open(frontend_log, "a", encoding="utf-8") as log_fp:
        log_fp.write(entry)

    return {"status": "ok"}
