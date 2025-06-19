# ===== Whisper Web App (Flask version) =====
from flask import Flask, render_template, request, redirect, send_file, jsonify
import whisper
import os
import uuid
import threading
import time
import datetime
from werkzeug.utils import secure_filename
from contextlib import redirect_stdout, redirect_stderr
import sys
import tempfile
import ffmpeg
import logging

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "transcripts"
LOG_FOLDER = "logs"
APP_LOG_FILE = "app_log.txt"
ALLOWED_EXTENSIONS = {'m4a', 'mp3', 'wav', 'flac'}
STATUS = {}
PROGRESS = {}
THREADS = {}
CANCELLED = {}

# Setup application-level logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(APP_LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
app.config['LOG_FOLDER'] = LOG_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(LOG_FOLDER, exist_ok=True)

logging.info("Application started. Upload and output folders initialized.")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.errorhandler(Exception)
def handle_exception(e):
    logging.exception("Unhandled exception occurred:")
    return jsonify({"error": str(e)}), 500

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/analyze_audio", methods=["POST"])
def analyze_audio():
    file = request.files['file']
    if not file or not allowed_file(file.filename):
        logging.warning("Invalid or missing file in analyze_audio request.")
        return jsonify({"error": "Invalid file"}), 400

    try:
        logging.info("Received file for analysis: %s", file.filename)
        with tempfile.NamedTemporaryFile(delete=False, suffix='.' + file.filename.rsplit('.', 1)[-1]) as tmp:
            file.save(tmp.name)
            audio = whisper.load_audio(tmp.name)
            duration = round(audio.shape[0] / whisper.audio.SAMPLE_RATE, 2)

            mel = whisper.log_mel_spectrogram(audio[:whisper.audio.SAMPLE_RATE * 30]).to("cpu")
            model = whisper.load_model("tiny")
            _, probs = model.detect_language(mel)
            language = max(probs, key=probs.get)

        logging.info("File analyzed successfully: duration=%.2f seconds, language=%s", duration, language)
        return jsonify({
            "duration_seconds": duration,
            "duration_str": f"{int(duration // 60)}m {int(duration % 60)}s",
            "language": language
        })
    except Exception as e:
        logging.exception("Failed during audio analysis:")
        return jsonify({"error": str(e)}), 500

@app.route("/upload", methods=["POST"])
def upload():
    file = request.files['file']
    model = request.form['model']
    format_ = request.form['format']
    timestamps = request.form.get("timestamps") == "on"

    segment_mode = request.form.get("segment")
    start_time = request.form.get("start", type=int)
    end_time = request.form.get("end", type=int)

    if not file or not allowed_file(file.filename):
        logging.warning("Invalid or missing file in upload request.")
        return jsonify({"error": "Invalid file"}), 400

    try:
        filename = secure_filename(file.filename)
        unique_id = str(uuid.uuid4())
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"{unique_id}_{filename}")
        file.save(filepath)
        logging.info("Saved file %s to %s", file.filename, filepath)

        STATUS[unique_id] = "Queued"

        def transcribe_task():
            from transcribe import run_transcription
            run_transcription(
                job_id=unique_id,
                filepath=filepath,
                model=model,
                format_=format_,
                use_timestamps=timestamps,
                segment_mode=segment_mode,
                start=start_time,
                end=end_time,
                output_dir=app.config['OUTPUT_FOLDER'],
                log_dir=app.config['LOG_FOLDER'],
                status_dict=STATUS,
                progress_dict=PROGRESS,
                cancelled_dict=CANCELLED
            )

        thread = threading.Thread(target=transcribe_task)
        thread.start()
        THREADS[unique_id] = thread

        return redirect(f"/status/{unique_id}")
    except Exception as e:
        logging.exception("Failed to start transcription:")
        return jsonify({"error": str(e)}), 500

@app.route("/cancel/<job_id>", methods=["POST"])
def cancel(job_id):
    thread = THREADS.get(job_id)
    if thread and thread.is_alive():
        STATUS[job_id] = "Cancelled by user. (Note: thread is not force-killed)"
        logging.info("Cancellation requested for job: %s", job_id)
        return jsonify({"status": "cancelled", "job_id": job_id})
    else:
        return jsonify({"status": "not running", "job_id": job_id})

@app.route("/status/<job_id>")
def status(job_id):
    state = STATUS.get(job_id, "Unknown job ID")
    done = state.startswith("Done:")
    error = state.startswith("Error:")
    progress = PROGRESS.get(job_id)
    download_url = ""
    log_text = ""
    log_path = os.path.join(LOG_FOLDER, f"{job_id}.log")
    if os.path.exists(log_path):
        with open(log_path, "r", encoding="utf-8") as log_file:
            log_text = log_file.read()
    if done:
        path = state.split(": ", 1)[1]
        download_url = f"/download/{os.path.basename(path)}"
    return render_template(
    "status.html",
    job_id=job_id,
    state=state,
    done=done,
    error=error,
    download_url=download_url,
    progress=progress,
    log=log_text,
    cancel_url=f"/cancel/{job_id}",
    refresh_token=str(datetime.datetime.now().timestamp())  # ✅ force-refresh trick
    )

@app.route("/download/<filename>")
def download(filename):
    try:
        return send_file(os.path.join(OUTPUT_FOLDER, filename), as_attachment=True)
    except Exception as e:
        logging.exception(f"Failed to send file: {filename}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    try:
        logging.info("Starting Flask app...")
        app.run(host="0.0.0.0", port=5000, debug=True)
    except Exception as e:
        logging.exception("Failed to start Flask app:")
