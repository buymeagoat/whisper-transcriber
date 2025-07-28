# Quick Start Guide

Follow these steps to install and run Whisper Transcriber.

## Prerequisites
- Python 3 and `pip`
- Node.js 18 *(required to build the frontend; must already be installed when building offline)*
- `ffmpeg` with `ffprobe`
- `models/` directory with `base.pt`, `small.pt`, `medium.pt`, `large-v3.pt` and `tiny.pt`
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
5. Install the Compose plugin with `sudo apt install docker-compose-plugin`.
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
Run `scripts/check_env.sh` before offline builds to validate DNS, confirm cached `.deb` packages align with the `python:3.11-jammy` base image and **fail** when the cached image digest no longer matches. Set `ALLOW_DIGEST_MISMATCH=1` to ignore this failure. If Docker fails to resolve registry hosts on WSL2, pass `DNS_SERVER=<ip>` to the build scripts or use `--network=host`.
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

