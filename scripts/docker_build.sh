#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
source "$SCRIPT_DIR/shared_checks.sh"

# Verify Docker Hub access before proceeding
check_docker_registry || {
    echo "Docker Hub is unreachable. Configure your proxy or network settings before building." >&2
    exit 1
}

LOG_DIR="$ROOT_DIR/logs"
LOG_FILE="$LOG_DIR/docker_build.log"
mkdir -p "$LOG_DIR"
exec > >(tee -a "$LOG_FILE") 2>&1

# Return 0 if docker compose build supports --secret
supports_secret() {
    docker compose build --help 2>/dev/null | grep -q -- "--secret"
}

FORCE_PRUNE=false

usage() {
    cat <<EOF
Usage: $(basename "$0") [--force]

Prunes Docker resources, rebuilds images and starts the compose stack from scratch.
With no options, the script will prompt before removing Docker data.
  --force  Skip confirmation prompt and prune without asking.
Run scripts/run_tests.sh afterward to execute the test suite.
If startup fails, use scripts/diagnose_containers.sh to inspect the containers.
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        -h|--help)
            usage
            exit 0
            ;;
        -f|--force)
            FORCE_PRUNE=true
            shift
            ;;
        *)
            echo "Unknown option: $1" >&2
            usage >&2
            exit 1
            ;;
    esac
done

# Remove existing containers, images and volumes to start fresh
docker compose -f "$ROOT_DIR/docker-compose.yml" down -v --remove-orphans || true

if [ "$FORCE_PRUNE" = true ]; then
    docker system prune -af --volumes
else
    read -r -p "Run 'docker system prune -af --volumes'? This may remove unrelated Docker data. [y/N] " response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        docker system prune -af --volumes
    else
        echo "Skipping docker system prune."
    fi
fi

# Update the repo
git -C "$ROOT_DIR" fetch
git -C "$ROOT_DIR" pull

stage_build_dependencies
(cd "$ROOT_DIR/frontend" && npm run build)

check_whisper_models
check_ffmpeg
ensure_env_file

echo "Environment variables:" >&2
env | sort >&2

secret_file_runtime="$ROOT_DIR/secret_key.txt"
printf '%s' "$SECRET_KEY" > "$secret_file_runtime"

# Build the standalone image used for production deployments
if supports_secret; then
    secret_file=$(mktemp)
    printf '%s' "$SECRET_KEY" > "$secret_file"
    docker build --network=host --secret id=secret_key,src="$secret_file" -t whisper-app "$ROOT_DIR"
    rm -f "$secret_file"
else
    docker build --network=host --build-arg SECRET_KEY="$SECRET_KEY" -t whisper-app "$ROOT_DIR"
fi

# Build images for the compose stack and start the services
if supports_secret; then
    secret_file=$(mktemp)
    printf '%s' "$SECRET_KEY" > "$secret_file"
    docker compose -f "$ROOT_DIR/docker-compose.yml" build \
      --network=host \
      --secret id=secret_key,src="$secret_file" \
      --build-arg INSTALL_DEV=true api worker
    rm -f "$secret_file"
else
    docker compose -f "$ROOT_DIR/docker-compose.yml" build \
      --network=host \
      --build-arg SECRET_KEY="$SECRET_KEY" \
      --build-arg INSTALL_DEV=true api worker
fi
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
        echo "Run scripts/diagnose_containers.sh for a detailed status report." >&2
        exit 1
    fi
    printf "."
    sleep 5
done

echo "Images built and containers started."
cat <<'EOF'
Available test scripts:
  scripts/run_tests.sh         - runs backend tests plus frontend unit and Cypress end-to-end tests. Recommended after a full build.
  scripts/run_backend_tests.sh - executes only the backend tests and verifies the /health and /version endpoints.

Run the desired script to verify the build.
If containers encounter issues, use scripts/diagnose_containers.sh for troubleshooting.
EOF
rm -f "$secret_file_runtime"

