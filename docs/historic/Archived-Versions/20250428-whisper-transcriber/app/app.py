from flask import Flask, render_template, request, redirect, url_for
import os
import threading
import sqlite3
import uuid
import subprocess
from logger import get_server_logger

# --------------------------
# Flask App Setup
# --------------------------
app = Flask(__name__)

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
TRANSCRIPT_FOLDER = os.path.join(os.getcwd(), 'transcripts')
DATABASE = os.path.join(os.getcwd(), 'jobs.db')

# Ensure necessary folders exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(TRANSCRIPT_FOLDER, exist_ok=True)

# --------------------------
# Server Logger Initialization
# --------------------------
server_logger = get_server_logger()

# --------------------------
# Helper Functions
# --------------------------
def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS jobs
                 (id TEXT PRIMARY KEY, filename TEXT, status TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

init_db()


def add_job_to_db(job_id, filename):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("INSERT INTO jobs (id, filename, status) VALUES (?, ?, ?)", (job_id, filename, "Queued"))
    conn.commit()
    conn.close()
    server_logger.info(f"New job added to DB: JobID={job_id}, Filename={filename}")


def update_job_status(job_id, status):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("UPDATE jobs SET status = ? WHERE id = ?", (status, job_id))
    conn.commit()
    conn.close()
    server_logger.info(f"JobID={job_id} status updated to {status}")


def transcribe_background(job_id, filepath):
    try:
        update_job_status(job_id, "Running")
        server_logger.info(f"Background transcription started for JobID={job_id}")
        
        subprocess.run([
            "python", "transcribe.py", "--job_id", job_id, "--input_file", filepath
        ], check=True)

        update_job_status(job_id, "Completed")
        server_logger.info(f"Background transcription completed for JobID={job_id}")
    except subprocess.CalledProcessError as e:
        update_job_status(job_id, "Failed")
        server_logger.error(f"Transcription failed for JobID={job_id}: {str(e)}")

# --------------------------
# Routes
# --------------------------
@app.route("/")
def home():
    server_logger.info("Accessed home page '/'")
    return render_template("home.html")


@app.route("/new-transcription", methods=["GET", "POST"])
def new_transcription():
    if request.method == "POST":
        if 'file' not in request.files:
            server_logger.warning("No file part in upload request.")
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            server_logger.warning("No file selected for uploading.")
            return redirect(request.url)
        if file:
            filename = file.filename
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)
            server_logger.info(f"File uploaded successfully: {filename}, saved at {filepath}")

            job_id = str(uuid.uuid4())
            add_job_to_db(job_id, filename)

            thread = threading.Thread(target=transcribe_background, args=(job_id, filepath))
            thread.start()
            server_logger.info(f"Background thread launched for JobID={job_id}")

            return redirect(url_for('active_jobs'))
    return render_template("new_transcription.html")


@app.route("/active-jobs")
def active_jobs():
    server_logger.info("Accessed active jobs page '/active-jobs'")
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT id, filename, status, created_at FROM jobs WHERE status IN ('Queued', 'Running')")
    jobs = c.fetchall()
    conn.close()
    return render_template("active_jobs.html", jobs=jobs)


@app.route("/past-jobs")
def past_jobs():
    server_logger.info("Accessed past jobs page '/past-jobs'")
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT id, filename, status, created_at FROM jobs WHERE status = 'Completed'")
    jobs = c.fetchall()
    conn.close()
    return render_template("past_jobs.html", jobs=jobs)

# --------------------------
# App Runner
# --------------------------
if __name__ == "__main__":
    server_logger.info("Starting Flask server for Whisper Transcriber...")
    app.run(debug=True, host='0.0.0.0', port=5000)