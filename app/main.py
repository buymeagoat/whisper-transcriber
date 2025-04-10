# app/main.py
from flask import Flask, render_template, request, redirect, send_file, jsonify
import logging
import os
import uuid
from datetime import datetime

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
TRANSCRIPT_FOLDER = "transcripts"
LOG_FOLDER = "logs"
APP_LOG = "app_log.txt"

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
    return redirect(f"/status/{job_id}")

@app.route("/status/<job_id>")
def status(job_id):
    return render_template("status.html", job_id=job_id, state="Pending...", done=False, error=False, download_url="", log="", progress=None)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
