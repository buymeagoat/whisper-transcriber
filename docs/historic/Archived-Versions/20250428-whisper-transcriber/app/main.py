# app/main.py
from job_store import get_all_jobs
from flask import Flask, render_template, request, redirect, send_file, jsonify
import logging
import os
import uuid
from datetime import datetime
from job_store import init_db, add_job, get_job

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
TRANSCRIPT_FOLDER = "transcripts"
LOG_FOLDER = "logs"
APP_LOG = "app_log.log"

# Ensure folders exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(TRANSCRIPT_FOLDER, exist_ok=True)
os.makedirs(LOG_FOLDER, exist_ok=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    filename=APP_LOG,
    filemode="a",
    format="%(asctime)s [%(levelname)s] %(message)s"
)

logging.info("🟢 Flask application starting...")
init_db()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("file")
    if not file:
        return "No file uploaded", 400

    job_id = str(uuid.uuid4())
    filename = f"{job_id}_{file.filename}"
    path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(path)

    logging.info(f"📥 Received file: {file.filename} → {filename}")
    logging.info(f"📝 Created job ID: {job_id}")

    # For now, just redirect to a dummy status page
    created_at = datetime.utcnow().isoformat()
    job = {
        "job_id": job_id,
        "file_name": filename,
        "original_name": file.filename,
        "created_at": created_at,
        "status": "pending",
        "model": "base",
        "format": "txt",
        "timestamps": False,
        "task": "transcribe",
        "language": "auto",
        "initial_prompt": "",
        "start_time": None,
        "end_time": None,
        "log_path": f"logs/{job_id}.log",
        "output_path": f"transcripts/{job_id}.txt"
    }

    add_job(job)
    logging.info(f"📌 Job metadata saved: {job_id}")
    return redirect(f"/status/{job_id}")

@app.route("/status/<job_id>")
def status(job_id):
    job = get_job(job_id)
    if not job:
        return f"Job {job_id} not found", 404

    state = job["status"]
    done = state == "done"
    error = state.startswith("error")
    return render_template("status.html",
                           job_id=job_id,
                           state=state,
                           done=done,
                           error=error,
                           download_url=job["output_path"] if done else "",
                           log="(log not implemented yet)",
                           progress=None)
@app.route("/jobs")
def jobs():
    all_jobs = get_all_jobs()
    logging.info(f"📋 Loaded {len(all_jobs)} jobs for display")
    return render_template("jobs.html", jobs=all_jobs)
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
