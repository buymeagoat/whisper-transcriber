#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
COMPOSE_FILE="$ROOT_DIR/docker-compose.yml"

# Rebuild frontend assets
(cd "$ROOT_DIR/frontend" && npm run build)

# Rebuild API and worker images using Docker cache
docker compose -f "$COMPOSE_FILE" build api worker

docker compose -f "$COMPOSE_FILE" up -d api worker
