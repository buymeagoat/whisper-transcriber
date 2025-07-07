#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
COMPOSE_FILE="$ROOT_DIR/docker-compose.yml"
LOG_DIR="$ROOT_DIR/logs"
LOG_FILE="$LOG_DIR/test.log"

mkdir -p "$LOG_DIR"

{
    docker compose -f "$COMPOSE_FILE" exec -T api coverage run -m pytest
    docker compose -f "$COMPOSE_FILE" exec -T api coverage report
    "$SCRIPT_DIR/integration_tests.sh"
} | tee "$LOG_FILE"

echo "Test log saved to $LOG_FILE"
