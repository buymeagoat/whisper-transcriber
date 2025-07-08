#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
COMPOSE_FILE="$ROOT_DIR/docker-compose.yml"

usage() {
    cat <<EOF
Usage: $(basename "$0")

Builds the frontend if needed and starts the docker compose stack.
sudo is required only to adjust ownership of the uploads, transcripts
and logs directories.
EOF
}

if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    usage
    exit 0
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
sudo chown -R 1000:1000 "$ROOT_DIR/uploads" "$ROOT_DIR/transcripts" "$ROOT_DIR/logs"

if [ ! -d "$ROOT_DIR/models" ]; then
    echo "Models directory $ROOT_DIR/models is missing. Place Whisper model files here before running." >&2
    exit 1
fi

echo "Starting containers with docker compose..."
docker compose -f "$COMPOSE_FILE" up --build -d api worker broker db

echo "Containers are starting. Use 'docker compose ps' to check status."
