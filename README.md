# Whisper Transcriber

A lightweight audio transcription tool leveraging OpenAI's Whisper models, designed for rapid local transcription and future offline containerized deployment.

---

## 🏁 Developer Quickstart

1. **Clone the repository** (if you haven't already):

    ```bash
    git clone https://github.com/buymeagoat/whisper-transcriber.git
    cd whisper-transcriber
    ```

2. **(First time only)** — Create the virtual environment:

    ```powershell
    python -m venv whisper-env
    ```

3. **Start your development session** (this activates venv + validates setup automatically):

    ```powershell
    .\scripts\run-dev-session.ps1
    ```

✅ This automatically:
- Activates your Python virtual environment
- Validates environment modules (auto-installs missing ones)
- Confirms Git repo health
- Prepares your dev session for development or testing

---

## 📋 Developer Notes

- The `whisper-env/` folder is **ignored** by Git (`.gitignore`) and remains local-only.
- Always start your session by running:

    ```powershell
    .\scripts\run-dev-session.ps1
    ```

- If you see missing module warnings, simply re-run the dev session script — it will attempt automatic recovery.

---

## 🎯 Typical Daily Workflow

```powershell
cd whisper-transcriber
.\scripts\run-dev-session.ps1
