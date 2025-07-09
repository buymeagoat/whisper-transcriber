#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
COMPOSE_FILE="$ROOT_DIR/docker-compose.yml"
source "$SCRIPT_DIR/shared_checks.sh"

usage() {
    cat <<EOF
Usage: $(basename "$0")

Builds the frontend if needed and starts the docker compose stack.
sudo is required only to adjust ownership of the uploads, transcripts
and logs directories.
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
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

setup_persistent_dirs
check_whisper_models
ensure_env_file

echo "Starting containers with docker compose..."
docker compose -f "$COMPOSE_FILE" up --build -d api worker broker db

# Wait for the API service to become healthy
max_wait=${API_HEALTH_TIMEOUT:-120}
start_time=$(date +%s)
printf "Waiting for api service to become healthy..."
while true; do
    container_id=$(docker compose -f "$COMPOSE_FILE" ps -q api)
    if [ -n "$container_id" ]; then
        health=$(docker inspect --format '{{ .State.Health.Status }}' "$container_id" 2>/dev/null || echo "starting")
        if [ "$health" = "healthy" ]; then
            echo " done"
            break
        fi
    fi
    elapsed=$(( $(date +%s) - start_time ))
    if [ $elapsed -ge $max_wait ]; then
        echo ""
        echo "API service failed to become healthy within ${max_wait}s. Check 'docker compose logs api' for details." >&2
        exit 1
    fi
    printf "."
    sleep 5
done

echo "Containers are ready. Use 'docker compose ps' to check status."
