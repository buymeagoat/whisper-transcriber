#!/usr/bin/env bash
set -e

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

# Rebuild frontend assets
(cd "$ROOT_DIR/frontend" && npm run build)

# Rebuild API and worker images using Docker cache
docker compose -f "$ROOT_DIR/docker-compose.yml" build api worker

docker compose -f "$ROOT_DIR/docker-compose.yml" up -d api worker
