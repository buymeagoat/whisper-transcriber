from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import os
import uuid
import shutil
import threading
import subprocess
import sqlite3
import datetime

app = Flask(__name__)

# Config
UPLOAD_FOLDER = 'uploads'
TRANSCRIPT_FOLDER = 'transcripts'
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'mp4', 'm4a'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['TRANSCRIPT_FOLDER'] = TRANSCRIPT_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(TRANSCRIPT_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Database Helpers
def insert_job(filename, model):
    conn = sqlite3.connect('data/jobs.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO jobs (file_name, status, model)
        VALUES (?, ?, ?)
    ''', (filename, 'Queued', model))
    conn.commit()
    conn.close()

def update_job_status(filename, status):
    conn = sqlite3.connect('data/jobs.db')
    c = conn.cursor()
    c.execute('UPDATE jobs SET status = ? WHERE file_name = ?', (status, filename))
    conn.commit()
    conn.close()

def load_completed_jobs():
    conn = sqlite3.connect('data/jobs.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM jobs WHERE status = "Completed" ORDER BY created DESC')
    jobs = c.fetchall()
    conn.close()
    return jobs

# Routes
@app.route('/')
def index():
    return redirect(url_for('new_transcription'))

@app.route('/new-transcription', methods=['GET', 'POST'])
def new_transcription():
    if request.method == 'POST':
        file = request.files.get('audio_file')
        model_size = request.form.get('model_size')
        language_variant = request.form.get('language_variant')

        if file and allowed_file(file.filename):
            filename = file.filename
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(save_path)

            model = f"{model_size}{'.en' if language_variant == 'english-only' else ''}"
            insert_job(filename, model)

            threading.Thread(target=transcribe_file, args=(filename, model), daemon=True).start()

            return redirect(url_for('active_jobs_view'))
    return render_template('new_transcription.html')

@app.route('/active-jobs')
def active_jobs_view():
    # This is a simple memory representation for now.
    # Optional: query database for status IN ("Queued", "Running")
    return render_template('active_jobs.html')

@app.route('/past-jobs')
def past_jobs():
    jobs = load_completed_jobs()
    return render_template('past_jobs.html', jobs=jobs)

@app.route('/transcripts/<path:filename>')
def download_transcript(filename):
    return send_from_directory(app.config['TRANSCRIPT_FOLDER'], filename, as_attachment=True)

def transcribe_file(filename, model):
    update_job_status(filename, 'Running')
    input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    try:
        subprocess.run([
            'python', 'transcribe.py',
            '--model', model,
            '--input', input_path
        ], check=True)

        update_job_status(filename, 'Completed')

    except subprocess.CalledProcessError as e:
        update_job_status(filename, 'Failed')
        print(f"Transcription failed for {filename}: {e}")

if __name__ == '__main__':
    app.run(debug=True)
