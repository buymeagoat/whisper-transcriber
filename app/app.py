import threading
import subprocess
from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import os
import uuid
import shutil

app = Flask(__name__)

# Config
UPLOAD_FOLDER = 'uploads'
TRANSCRIPT_FOLDER = 'transcripts'
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'mp4', 'm4a'}

# Memory storage for jobs
active_jobs = {}
completed_jobs = {}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['TRANSCRIPT_FOLDER'] = TRANSCRIPT_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(TRANSCRIPT_FOLDER, exist_ok=True)

# Helpers
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Routes
@app.route('/')
def index():
    return render_template('home.html')

@app.route('/new-transcription', methods=['GET', 'POST'])
def new_transcription():
    if request.method == 'POST':
        file = request.files.get('audio_file')
        model_size = request.form.get('model_size')
        language_variant = request.form.get('language_variant')
        task = request.form.get('task') or 'transcribe'
        temperature = request.form.get('temperature') or '0'
        beam_size = request.form.get('beam_size') or '5'
        best_of = request.form.get('best_of') or '5'
        word_timestamps = 'word_timestamps' in request.form
        initial_prompt = request.form.get('initial_prompt') or ''

        if file and allowed_file(file.filename):
            filename = file.filename
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(save_path)

            job_id = str(uuid.uuid4())
            active_jobs[job_id] = {
                'filename': filename,
                'model': f"{model_size}{'.en' if language_variant == 'english-only' else ''}",
                'progress': 0,
                'status': 'Queued',
                'settings': {
                    'task': task,
                    'temperature': temperature,
                    'beam_size': beam_size,
                    'best_of': best_of,
                    'word_timestamps': word_timestamps,
                    'initial_prompt': initial_prompt,
                }
            }

            # 🚀 Launch the transcription background thread
            threading.Thread(target=transcribe_file, args=(job_id,), daemon=True).start()

            return redirect(url_for('active_jobs_view'))
    return render_template('new_transcription.html')

@app.route('/active-jobs')
def active_jobs_view():
    return render_template('active_jobs.html', jobs=active_jobs)

@app.route('/past-jobs')
def past_jobs():
    return render_template('past_jobs.html', jobs=completed_jobs)

@app.route('/transcripts/<path:filename>')
def download_transcript(filename):
    return send_from_directory(app.config['TRANSCRIPT_FOLDER'], filename, as_attachment=True)

def transcribe_file(job_id):
    job = active_jobs.get(job_id)
    if not job:
        return

    filename = job['filename']
    input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    model = job['model']

    active_jobs[job_id]['status'] = 'Running'
    active_jobs[job_id]['progress'] = 10  # Start at 10%

    try:
        # Call transcribe.py as subprocess
        subprocess.run([
            'python', 'transcribe.py',
            '--model', model,
            '--input', input_path
        ], check=True)

        # Mark job as complete
        active_jobs[job_id]['progress'] = 100
        active_jobs[job_id]['status'] = 'Completed'

        # ✅ Move job to completed_jobs
        completed_jobs[job_id] = active_jobs.pop(job_id)

    except subprocess.CalledProcessError as e:
        active_jobs[job_id]['status'] = 'Failed'
        active_jobs[job_id]['progress'] = 0
        print(f"Transcription failed for {filename}: {e}")

if __name__ == '__main__':
    app.run(debug=True)
