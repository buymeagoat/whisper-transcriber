#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
COMPOSE_FILE="$ROOT_DIR/docker-compose.yml"

# Load secret key from .env for Docker build
if [ ! -f "$ROOT_DIR/.env" ]; then
    echo "Missing .env file" >&2
    exit 1
fi

SECRET_KEY=$(grep -E '^SECRET_KEY=' "$ROOT_DIR/.env" | cut -d= -f2-)
if [ -z "$SECRET_KEY" ]; then
    echo "SECRET_KEY not set in .env" >&2
    exit 1
fi

# Rebuild frontend assets
(cd "$ROOT_DIR/frontend" && npm run build)

# Rebuild API and worker images using Docker cache
docker compose -f "$COMPOSE_FILE" build --build-arg SECRET_KEY="$SECRET_KEY" api worker

docker compose -f "$COMPOSE_FILE" up -d api worker
