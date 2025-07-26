# Quick Start Guide

Follow these steps to install and run Whisper Transcriber.

## Prerequisites
- Python 3 and `pip`
- `ffmpeg` with `ffprobe`
- Docker and Docker Compose *(optional)*

## Docker on WSL
Follow these steps to install Docker inside the WSL distribution:
1. `sudo apt remove docker docker.io containerd runc`
2. `sudo apt update && sudo apt install docker.io`
3. Enable and start the daemon:
   ```bash
   sudo systemctl enable docker
   sudo service docker start
   ```
4. Add your user to the `docker` group with `sudo usermod -aG docker $USER` and log out.
Remove Docker Desktop to avoid conflicts when running WSL-native Docker.


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
The compiled frontend assets live in `frontend/dist/`, which is not committed. Run `npm run build` in the `frontend` directory or use the helper scripts to generate this folder.
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

