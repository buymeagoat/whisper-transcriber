# Whisper Transcriber

A local-first, privacy-focused audio transcription platform powered by OpenAI's Whisper models.

---

## 📦 Project Structure

```
/whisper-transcriber/
  app/
    app.py
    templates/
  data/
    jobs.db
  logs/
  models/
  transcripts/
  uploads/
  paths.py
  transcribe.py
  setup_env.py
  Whisper_Design.md
  README.md
```

---

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/buymeagoat/whisper-transcriber.git
cd whisper-transcriber
```

### 2. Set Up the Environment

Make sure you have Python 3.10 installed. Then, set up a virtual environment:

```bash
python -m venv whisper-env
.\whisper-env\Scripts\activate
pip install -r requirements.txt
```

Ensure `ffmpeg` is installed and available in your system PATH.

### 3. Run the Application

From the project root, run:

```bash
py -m app.app
```

This will launch the Flask server locally.

> ℹ️ We use `-m app.app` to ensure Python treats `/app` as a module, enabling clean imports like `from paths import ...`.

---

## 🛠 Core Features

- Simple web UI for uploading audio files.
- Background threading to transcribe files asynchronously.
- Local SQLite database to track job statuses.
- Downloadable `.txt` transcripts.
- Centralized filesystem management via `paths.py`.


## 🔮 Future Enhancements

- Transcript download button after transcription completes.
- Full audio testing of `transcribe.py` output.
- Docker containerization for offline deployment.
- UI improvements for active job tracking.
- Unit tests and full coverage.

---

## 📢 Special Notes

- Always run the app from the project root.
- No hardcoded folder paths — always import from `paths.py`.
- Keep `Whisper_Design.md` updated with any architectural changes.

---

## 📄 License

This project is licensed under the MIT License.
