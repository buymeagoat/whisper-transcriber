#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
CACHE_DIR="${CACHE_DIR:-$ROOT_DIR/cache}"
source "$SCRIPT_DIR/shared_checks.sh"

LOG_DIR="$ROOT_DIR/logs"
LOG_FILE="$LOG_DIR/docker_build.log"
mkdir -p "$LOG_DIR"
exec > >(tee -a "$LOG_FILE") 2>&1

# Echo a marker indicating the current script stage
log_step() {
    echo "===== $1 ====="
}

# Summarize failures before exiting
trap 'echo "[ERROR] docker_build.sh failed near line $LINENO. Check $LOG_FILE for details." >&2' ERR

log_step "STAGING"
# Stage dependencies needed for an offline build
"$SCRIPT_DIR/prestage_dependencies.sh"
# Verify Docker and cache directories are ready and install packages
check_docker_running
check_cache_dirs
stage_build_dependencies

# Build frontend assets before verifying cached resources
(cd "$ROOT_DIR/frontend" && npm run build)

# Verify required offline assets after downloads complete
verify_offline_assets

# Return 0 if docker compose build supports --secret
supports_secret() {
    docker compose build --help 2>/dev/null | grep -q -- "--secret"
}

# Return 0 only if the API and worker images exist after the build
verify_built_images() {
    local images=(whisper-transcriber-api:latest whisper-transcriber-worker:latest)
    for img in "${images[@]}"; do
        if ! docker image inspect "$img" >/dev/null 2>&1; then
            echo "Missing Docker image $img" >&2
            return 1
        fi
    done
}

MODE=full
FORCE_PRUNE=false

usage() {
    cat <<EOF
Usage: $(basename "$0") [--full|--incremental] [--force]

--full          Prune Docker resources and rebuild the compose stack from scratch.
--incremental   Rebuild only missing or unhealthy images similar to update_images.sh.
--force         Skip confirmation prompt when using --full.
With no option, --full is assumed.
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
        --full)
            MODE=full
            shift
            ;;
        --incremental)
            MODE=incremental
            shift
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

# If running an incremental build, delegate to update_images.sh
if [ "$MODE" = "incremental" ]; then
    "$SCRIPT_DIR/update_images.sh"
    exit $?
fi

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

log_step "VERIFICATION"
check_whisper_models
check_ffmpeg
ensure_env_file

echo "Environment variables:" >&2
env | sort >&2

secret_file_runtime="$ROOT_DIR/secret_key.txt"
printf '%s' "$SECRET_KEY" > "$secret_file_runtime"

log_step "BUILD"
echo "Building the production image..."
# Build the standalone image used for production deployments
if supports_secret; then
    secret_file=$(mktemp)
    printf '%s' "$SECRET_KEY" > "$secret_file"
    docker build --network=none --secret id=secret_key,src="$secret_file" -t whisper-app "$ROOT_DIR"
    rm -f "$secret_file"
else
    docker build --network=none --build-arg SECRET_KEY="$SECRET_KEY" -t whisper-app "$ROOT_DIR"
fi

echo "Rebuilding API and worker images..."
# Build images for the compose stack and start the services
if supports_secret; then
    secret_file=$(mktemp)
    printf '%s' "$SECRET_KEY" > "$secret_file"
    docker compose -f "$ROOT_DIR/docker-compose.yml" build \
      --secret id=secret_key,src="$secret_file" \
      --network=none \
      --build-arg INSTALL_DEV=true api worker
    rm -f "$secret_file"
else
    docker compose -f "$ROOT_DIR/docker-compose.yml" build \
      --network=none \
      --build-arg SECRET_KEY="$SECRET_KEY" \
      --build-arg INSTALL_DEV=true api worker
fi

echo "Verifying built images..."
verify_built_images

log_step "STARTUP"
echo "Starting containers..."
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

