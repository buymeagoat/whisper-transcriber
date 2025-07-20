#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
COMPOSE_FILE="$ROOT_DIR/docker-compose.yml"
LOG_DIR="$ROOT_DIR/logs"
LOG_FILE="$LOG_DIR/test.log"

mkdir -p "$LOG_DIR"

# Ensure the API container is running before executing tests
if ! docker compose -f "$COMPOSE_FILE" ps api | grep -q "running"; then
    echo "API container is not running. Start the stack with scripts/start_containers.sh" >&2
    echo "Last API container logs:" >&2
    docker compose -f "$COMPOSE_FILE" logs api | tail -n 20 >&2 || true
    exit 1
fi

API_HOST="${VITE_API_HOST:-http://localhost:8000}"
API_HOST="${API_HOST%/}"

check_endpoint() {
    local path="$1"
    if curl -fsS "$API_HOST$path" >/dev/null; then
        echo "$path OK"
    else
        echo "$path FAILED"
        return 1
    fi
}

{
    docker compose -f "$COMPOSE_FILE" exec -T api coverage run -m pytest
    docker compose -f "$COMPOSE_FILE" exec -T api coverage report
    check_endpoint /health
    check_endpoint /version
} | tee "$LOG_FILE"

echo "Test log saved to $LOG_FILE"
