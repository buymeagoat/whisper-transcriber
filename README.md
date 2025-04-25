Whisper Transcriber
Offline-first, privacy-focused audio transcription platform using OpenAI Whisper models.

📋 Features
⚡ Offline transcription (no cloud dependency if models are staged)

🖥️ Minimal web UI for uploading and viewing transcripts

🧠 Local-only SQLite job tracking (no external servers)

🚀 Developer bootstrap scripts for easy session startup

🎯 Clean .txt and .json transcript outputs

📦 Local Whisper model staging to avoid downloads

🛠️ Installation
Clone the repository:

bash
Copy
Edit
git clone https://github.com/buymeagoat/whisper-transcriber.git
cd whisper-transcriber
Create and activate a Python virtual environment:

bash
Copy
Edit
python -m venv whisper-env

# Windows
.\whisper-env\Scripts\activate

# macOS/Linux
source whisper-env/bin/activate
Install dependencies:

bash
Copy
Edit
pip install -r requirements.txt
(Optional) Pre-stage Whisper models for fully offline operation:
Place .pt model files into /models/{model_name}/{model_name}.pt folders.

Example structure:

plaintext
Copy
Edit
models/
  base.en/base.en.pt
  tiny/tiny.pt
  medium/medium.pt
⚡ Usage
🔹 Start Local Developer Session
(Recommended for setup validation)

bash
Copy
Edit
.\scripts\run-dev-session.ps1
Verifies repo, venv, Python modules, models folder, etc.

Fix issues before running the app.

🔹 Run CLI Transcription
bash
Copy
Edit
python app/transcribe.py --input uploads/your_audio_file.wav
Optional flags:

--model tiny

--model small.en

Default: base.en

Transcripts are saved into:

transcripts/your_audio_file.json

transcripts/your_audio_file.txt

🔹 Run Web UI
Start the local Flask server:

bash
Copy
Edit
python app/main.py
Open your browser to:

cpp
Copy
Edit
http://127.0.0.1:5000
Upload new audio files

View processing status

Download finished transcripts

📂 Project Structure
plaintext
Copy
Edit
whisper-transcriber/
├── app/
├── scripts/
├── uploads/
├── transcripts/
├── logs/
├── models/
├── data/
├── whisper-env/ (local virtualenv)
├── setup_env.py
├── requirements.txt
├── README.md
├── Whisper_Design.md
└── .gitignore
🧹 GitHub Hygiene
.gitignore ensures:

whisper-env/

uploads/

logs/

transcripts/

models/

data/jobs.db

are NOT committed to GitHub for security and cleanliness.

🔮 Upcoming Improvements
Transcript download button in Web UI

Docker container for easy full offline deployment

Improved session log viewer

Unit tests for CLI and Flask routes

Config option for "strict offline mode" (no downloads allowed)

🛡️ License
MIT License.
See LICENSE file for details.