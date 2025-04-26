from flask import Flask, request, render_template, redirect, url_for, send_from_directory
import threading
import os
import sqlite3
from datetime import datetime
import time

# Import centralized paths
from paths import UPLOADS_DIR, TRANSCRIPTS_DIR, DB_PATH

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOADS_DIR

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            job_id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name TEXT,
            status TEXT,
            model TEXT,
            created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()


def save_job(file_name, status='Queued'):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO jobs (file_name, status, created) VALUES (?, ?, ?)', (file_name, status, datetime.now()))
    conn.commit()
    conn.close()

def update_job_status(file_name, status):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE jobs SET status = ? WHERE file_name = ?', (status, file_name))
    conn.commit()
    conn.close()

def transcribe_file(filepath, file_name):
    from transcribe import transcribe_audio  # Import here to avoid circular imports

    update_job_status(file_name, 'Running')
    try:
        transcribe_audio(filepath)
        update_job_status(file_name, 'Completed')
    except Exception as e:
        print(f"Error transcribing {file_name}: {e}")
        update_job_status(file_name, 'Failed')

def background_transcription(filepath, file_name):
    thread = threading.Thread(target=transcribe_file, args=(filepath, file_name))
    thread.start()

@app.route('/', methods=['GET'])
def home():
    return render_template('home.html')

@app.route('/new-transcription', methods=['GET', 'POST'])
def new_transcription():
    if request.method == 'POST':
        file = request.files['file']
        if file:
            file_name = file.filename
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], file_name)
            file.save(save_path)
            save_job(file_name)
            background_transcription(save_path, file_name)
            return redirect(url_for('active_jobs'))
    return render_template('new-transcription.html')

@app.route('/active-jobs')
def active_jobs():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT file_name, status, created FROM jobs ORDER BY created DESC')
    jobs = cursor.fetchall()
    conn.close()
    return render_template('active-jobs.html', jobs=jobs)

@app.route('/past-jobs')
def past_jobs():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT file_name, status, created FROM jobs WHERE status = "Completed" ORDER BY created DESC')
    jobs = cursor.fetchall()
    conn.close()
    return render_template('past-jobs.html', jobs=jobs)

@app.route('/transcripts/<file_name>')
def download_transcript(file_name):
    return send_from_directory(TRANSCRIPTS_DIR, file_name)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
