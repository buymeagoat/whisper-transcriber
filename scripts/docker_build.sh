#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
source "$SCRIPT_DIR/shared_checks.sh"

usage() {
    cat <<EOF
Usage: $(basename "$0")

Prunes Docker resources, rebuilds images and starts the compose stack from scratch.
Run scripts/run_tests.sh afterward to execute the test suite.
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
    usage
    exit 0
fi

# Remove existing containers, images and volumes to start fresh
docker compose -f "$ROOT_DIR/docker-compose.yml" down -v --remove-orphans || true
docker system prune -af --volumes

# Update the repo
git -C "$ROOT_DIR" fetch
git -C "$ROOT_DIR" pull

# Install Python dependencies
pip install -r "$ROOT_DIR/requirements.txt"

# Install and build the frontend
(cd "$ROOT_DIR/frontend" && npm install && npm run build)

check_whisper_models
ensure_env_file

# Build the standalone image used for production deployments
docker build --build-arg SECRET_KEY="$SECRET_KEY" -t whisper-app "$ROOT_DIR"

# Build images for the compose stack and start the services
docker compose -f "$ROOT_DIR/docker-compose.yml" build \
  --build-arg SECRET_KEY="$SECRET_KEY" api worker
docker compose -f "$ROOT_DIR/docker-compose.yml" up -d api worker broker db

# Wait for the API container to become healthy
max_wait=${API_HEALTH_TIMEOUT:-120}
start_time=$(date +%s)
printf "Waiting for api service to become healthy..."
while true; do
    container_id=$(docker compose -f "$ROOT_DIR/docker-compose.yml" ps -q api)
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
        echo "API container failed to become healthy within ${max_wait}s." >&2
        echo "Last API container logs:" >&2
        docker compose -f "$ROOT_DIR/docker-compose.yml" logs api | tail -n 20 >&2 || true
        exit 1
    fi
    printf "."
    sleep 5
done

echo "Images built and containers started. Run scripts/run_tests.sh separately to execute the test suite."

