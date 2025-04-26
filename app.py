from flask import Flask, request, render_template, redirect, url_for, send_from_directory
import threading
import os
import sqlite3
from datetime import datetime
import time

# Import centralized paths
from paths import UPLOADS_FOLDER, TRANSCRIPTS_FOLDER, DB_PATH

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOADS_FOLDER

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            status TEXT,
            created_at TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def save_job(filename, status='Queued'):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO jobs (filename, status, created_at) VALUES (?, ?, ?)', (filename, status, datetime.now()))
    conn.commit()
    conn.close()

def update_job_status(filename, status):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE jobs SET status = ? WHERE filename = ?', (status, filename))
    conn.commit()
    conn.close()

def transcribe_file(filepath, filename):
    from transcribe import transcribe_audio  # Import here to avoid circular imports

    update_job_status(filename, 'Running')
    try:
        transcribe_audio(filepath)
        update_job_status(filename, 'Completed')
    except Exception as e:
        print(f"Error transcribing {filename}: {e}")
        update_job_status(filename, 'Failed')

def background_transcription(filepath, filename):
    thread = threading.Thread(target=transcribe_file, args=(filepath, filename))
    thread.start()

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        if file:
            filename = file.filename
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(save_path)
            save_job(filename)
            background_transcription(save_path, filename)
            return redirect(url_for('jobs'))
    return render_template('upload.html')

@app.route('/jobs')
def jobs():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT filename, status, created_at FROM jobs ORDER BY created_at DESC')
    jobs = cursor.fetchall()
    conn.close()
    return render_template('jobs.html', jobs=jobs)

@app.route('/transcripts/<filename>')
def download_transcript(filename):
    return send_from_directory(TRANSCRIPTS_FOLDER, filename)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
