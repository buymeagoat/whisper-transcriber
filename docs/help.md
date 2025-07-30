# Quick Start Guide

Use this page for the minimal steps to get Whisper Transcriber running. For a full walkthrough and advanced usage, see [README.md](../README.md) and the architecture notes in [design_scope.md](design_scope.md).

## Prerequisites
- Python 3 with `pip`
- Node.js 18+
- `ffmpeg` with `ffprobe`
- Whisper models placed in `models/` (`tiny.pt`, `base.pt`, `small.pt`, `medium.pt`, `large-v3.pt`)
- Docker and Docker Compose *(optional)*

## Install
```bash
pip install -r requirements.txt
cd frontend && npm install && npm run build && cd ..
```
Copy `.env.example` to `.env` and set `SECRET_KEY`.

## Run
Start the API locally:
```bash
uvicorn api.main:app
```
Or launch the Docker stack:
```bash
docker compose up --build
```

See [README.md](../README.md) for troubleshooting, offline setup and Docker details. The [design_scope.md](design_scope.md) document outlines how the system works under the hood.

Codex Analyst GPT (CAG) drives repository audits and patch creation. CAG fetches file lists and contents through prompt-driven commands and returns the diffs to apply, so no manual scripts are needed.
