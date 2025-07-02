#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

# Re-run the script with sudo if not already root so ownership can be adjusted
if [ "$(id -u)" -ne 0 ]; then
    if command -v sudo >/dev/null; then
        exec sudo "$0" "$@"
    else
        echo "sudo is required to set directory ownership" >&2
        exit 1
    fi
fi

# Install and build the frontend if needed
if [ ! -d "$ROOT_DIR/frontend/node_modules" ]; then
    echo "Installing frontend dependencies..."
    (cd "$ROOT_DIR/frontend" && npm install)
fi

if [ ! -d "$ROOT_DIR/frontend/dist" ]; then
    echo "Building frontend..."
    (cd "$ROOT_DIR/frontend" && npm run build)
fi

# Ensure persistent directories exist
mkdir -p "$ROOT_DIR/uploads" "$ROOT_DIR/transcripts" "$ROOT_DIR/logs"
# Fix permissions in case they were created as root
chown -R 1000:1000 "$ROOT_DIR/uploads" "$ROOT_DIR/transcripts" "$ROOT_DIR/logs"

if [ ! -d "$ROOT_DIR/models" ]; then
    echo "Models directory $ROOT_DIR/models is missing. Place Whisper model files here before running." >&2
    exit 1
fi

echo "Starting containers with docker compose..."
docker compose -f "$ROOT_DIR/docker-compose.yml" up --build -d api worker broker db

echo "Containers are starting. Use 'docker compose ps' to check status."
