Whisper Transcriber - Project Design Document
📆 Project Overview
Whisper Transcriber is a local-first, privacy-respecting audio transcription platform.

Features:

Offline-first transcription using OpenAI Whisper models

Minimal web UI for uploading audio, viewing, and downloading transcripts

Local SQLite job tracking (no cloud dependency)

Staged local model loading to avoid unnecessary network downloads

Lightweight CLI bootstrap for developer sessions

📊 Project Layout
plaintext
Copy
Edit
whisper-transcriber/
├── app/
│   ├── transcribe.py          # CLI transcription tool
│   ├── job_store.py           # SQLite job tracking
│   ├── main.py                # Flask routes for UI
│   └── templates/             # HTML templates for UI
│       ├── base.html
│       ├── index.html
│       ├── jobs.html
│       └── status.html
│
├── scripts/
│   ├── start-whispersession.ps1  # Developer environment session starter
│   └── run-dev-session.ps1       # Local dev booster script
│
├── uploads/                 # Uploaded audio files (runtime only)
├── transcripts/              # Output transcript files (.json and .txt)
├── logs/                     # Runtime logs and debug logs
├── data/
│   └── jobs.db                # SQLite database file (created at runtime)
│
├── models/                   # Staged Whisper model files (.pt)
│
├── setup_env.py              # Developer environment reset tool
├── requirements.txt          # Python dependencies
├── README.md                 # Project overview and usage
├── Whisper_Design.md         # This design document
├── .gitignore                # Ignores whisper-env, uploads, logs, transcripts, models
└── whisper-env/              # (local virtual environment, ignored by Git)
🔢 Local Development Environment
Create a local Python virtual environment:

bash
Copy
Edit
python -m venv whisper-env
Activate the virtual environment:

bash
Copy
Edit
# Windows
.\whisper-env\Scripts\activate

# macOS/Linux
source whisper-env/bin/activate
Install dependencies:

bash
Copy
Edit
pip install -r requirements.txt
Important: Stage Whisper .pt models manually into the /models/ folder structure to avoid forced re-downloads during usage.

whisper-env/ is ignored from GitHub via .gitignore and should always remain local.

🔄 Development Workflow
Start Developer Session:

bash
Copy
Edit
.\scripts\run-dev-session.ps1
Upload or place audio files into uploads/

Run CLI transcription:

bash
Copy
Edit
python app/transcribe.py --input uploads/yourfile.wav
View transcripts in transcripts/:

.json for developer metadata

.txt for clean user-readable transcripts

(Optional) Start Flask UI for uploads and viewing:

bash
Copy
Edit
python app/main.py
📦 Whisper Models Staging

Model Name	Folder Structure	Filename
tiny	/models/tiny/	tiny.pt
tiny.en	/models/tiny.en/	tiny.en.pt
base	/models/base/	base.pt
base.en	/models/base.en/	base.en.pt
small	/models/small/	small.pt
medium	/models/medium/	medium.pt
large-v2	/models/large-v2/	large-v2.pt
Models must be staged manually.

If a requested model is not found locally, fallback download occurs automatically unless restricted via future config options.

📅 Milestone Status

Component	Status
Developer Session Script	✅ Completed
CLI Transcription (transcribe.py)	✅ Completed
Local Model Staging & Loading	✅ Completed
Clean TXT Transcript Export	✅ Completed
Flask App Skeleton (main.py)	✅ Completed
HTML Templates (templates/)	✅ Created
Transcript Download UI	⏳ Upcoming
Job Logs UI	⏳ Upcoming
Dockerfile / Offline Packaging	⏳ Upcoming
🚀 Next Steps
Implement transcript download feature in UI

Build Docker container for full offline deployment

Add basic log visualization (job status and error tracing)

Introduce optional config toggles for strict offline mode (no auto-downloads)

Create lightweight unit tests for CLI and Flask routes

