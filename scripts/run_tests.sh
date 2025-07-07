#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
COMPOSE_FILE="$ROOT_DIR/docker-compose.yml"

docker compose -f "$COMPOSE_FILE" exec -T api coverage run -m pytest
docker compose -f "$COMPOSE_FILE" exec -T api coverage report
