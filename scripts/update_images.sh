#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
COMPOSE_FILE="$ROOT_DIR/docker-compose.yml"
source "$SCRIPT_DIR/shared_checks.sh"

# Load SECRET_KEY from .env
ensure_env_file

# Rebuild frontend assets
(cd "$ROOT_DIR/frontend" && npm run build)

# Rebuild API and worker images using Docker cache
docker compose -f "$COMPOSE_FILE" build --build-arg SECRET_KEY="$SECRET_KEY" api worker

docker compose -f "$COMPOSE_FILE" up -d api worker
