# Quick Start Guide

Follow these steps to install and run Whisper Transcriber.

## Prerequisites
- Python 3 and `pip`
- `ffmpeg` with `ffprobe`
- Docker and Docker Compose *(optional)*

## Install dependencies
- Python packages:
  ```bash
  pip install -r requirements.txt
  ```
## Configure the application
- Copy `.env.example` to `.env` and replace the placeholder value.
- Generate a secret with:
  ```bash
  python -c "import secrets; print(secrets.token_hex(32))"
  ```
  Use this value for `SECRET_KEY` in `.env`.

## Build and run
The React frontend is precompiled, so no additional build step is required.
- Start locally with:
  ```bash
  uvicorn api.main:app
  ```
- Or launch the Docker Compose stack:
  ```bash
  sudo scripts/start_containers.sh
  # or
  docker compose up --build
  ```

## Testing and maintenance
- Use `scripts/run_tests.sh` to run backend, frontend and Cypress tests.
- `scripts/start_containers.sh` verifies prerequisites and starts the containers.

