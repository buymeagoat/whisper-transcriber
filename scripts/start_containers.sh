#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
CACHE_DIR="${CACHE_DIR:-$ROOT_DIR/cache}"
COMPOSE_FILE="$ROOT_DIR/docker-compose.yml"
source "$SCRIPT_DIR/shared_checks.sh"

LOG_DIR="$ROOT_DIR/logs"
LOG_FILE="$LOG_DIR/start_containers.log"
mkdir -p "$LOG_DIR"
# Mirror all output to a startup log for troubleshooting
exec > >(tee -a "$LOG_FILE") 2>&1

# Ensure required offline assets are present
verify_offline_assets

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

stage_build_dependencies

# Build the frontend if needed

if [ ! -d "$ROOT_DIR/frontend/dist" ]; then
    echo "Building frontend..."
    (cd "$ROOT_DIR/frontend" && npm run build)
fi

setup_persistent_dirs
check_whisper_models
check_ffmpeg
ensure_env_file

secret_file="$ROOT_DIR/secret_key.txt"
printf '%s' "$SECRET_KEY" > "$secret_file"

echo "Environment variables:" >&2
env | sort >&2

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
        echo "Run scripts/diagnose_containers.sh for further troubleshooting." >&2
        exit 1
    fi
    printf "."
    sleep 5
done

echo "Containers are ready. Use 'docker compose ps' to check status."
echo "Run scripts/run_tests.sh to execute the test suite." 
rm -f "$secret_file"
