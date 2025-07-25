#!/usr/bin/env bash
set -euo pipefail

# Ensure the script runs with root privileges for apt operations
if [[ $EUID -ne 0 ]]; then
    echo "Run with sudo to download apt packages" >&2
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
CACHE_DIR="${CACHE_DIR:-$ROOT_DIR/cache}"
source "$SCRIPT_DIR/shared_checks.sh"

LOG_DIR="$ROOT_DIR/logs"
LOG_FILE="$LOG_DIR/docker_build.log"
mkdir -p "$LOG_DIR"
exec > >(tee -a "$LOG_FILE") 2>&1

# File storing the SECRET_KEY during the build
secret_file_runtime="$ROOT_DIR/secret_key.txt"

# Remove the temporary secret file on exit or error
cleanup() {
    rm -f "$secret_file_runtime"
}

# Echo a marker indicating the current script stage
log_step() {
    echo "===== $1 ====="
}

# Summarize failures before exiting and clean up secret file
trap 'echo "[ERROR] docker_build.sh failed near line $LINENO. Check $LOG_FILE for details." >&2; cleanup' ERR
trap cleanup EXIT

MODE=""
FORCE_PRUNE=false
FORCE_FRONTEND=false
OFFLINE=false





usage() {
    cat <<EOF
Usage: $(basename "$0") [--full|--incremental] [--force] [--force-frontend] [--offline]

--full          Prune Docker resources and rebuild the compose stack from scratch.
--incremental   Rebuild only missing or unhealthy images similar to update_images.sh.
--force-frontend Rebuild the frontend even if frontend/dist exists.
--offline        Skip prestage_dependencies.sh and use cached packages.
You must supply either --full or --incremental.
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
        --force-frontend)
            FORCE_FRONTEND=true
            shift
            ;;
        --offline)
            OFFLINE=true
            shift
            ;;
        *)
            echo "Unknown option: $1" >&2
            usage >&2
            exit 1
            ;;
    esac
done

if [ -z "$MODE" ]; then
    echo "Specify --full for a clean rebuild or --incremental for an in-place update." >&2
    usage >&2
    exit 1
fi

# If running an incremental build, delegate to update_images.sh
if [ "$MODE" = "incremental" ]; then
    if [ "$OFFLINE" = true ] || [ "${SKIP_PRESTAGE:-}" = "1" ]; then
        SKIP_PRESTAGE=1 "$SCRIPT_DIR/update_images.sh" --offline
    else
        "$SCRIPT_DIR/update_images.sh"
    fi
    exit $?
fi

log_step "STAGING"
install_node18
if [ "${SKIP_PRESTAGE:-}" = "1" ] || [ "$OFFLINE" = true ]; then
    echo "Skipping prestage_dependencies.sh (offline mode)"
else
    "$SCRIPT_DIR/prestage_dependencies.sh"
fi
check_docker_running
check_cache_dirs
stage_build_dependencies

# Build frontend assets if missing or forced before verifying cached resources
if [ "$FORCE_FRONTEND" = true ] || [ ! -d "$ROOT_DIR/frontend/dist" ]; then
    echo "Building frontend assets..."
    (cd "$ROOT_DIR/frontend" && npm run build)
fi

verify_offline_assets

# Remove existing containers and volumes created by this repository
docker compose -f "$ROOT_DIR/docker-compose.yml" down -v --remove-orphans || true

# Remove only the Docker images built for this project
remove_project_images() {
    local images=(whisper-app whisper-transcriber-api:latest whisper-transcriber-worker:latest)
    for img in "${images[@]}"; do
        if docker image inspect "$img" >/dev/null 2>&1; then
            docker image rm "$img" >/dev/null 2>&1 || true
        fi
    done
}

if [ "$FORCE_PRUNE" = true ]; then
    remove_project_images
else
    read -r -p "Remove Docker images built for this project? [y/N] " response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        remove_project_images
    else
        echo "Skipping image removal."
    fi
fi

log_step "VERIFICATION"
check_whisper_models
check_ffmpeg
ensure_env_file

echo "Environment variables:" >&2
env | sort | grep -v '^SECRET_KEY=' >&2
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
max_wait=${API_HEALTH_TIMEOUT:-300}
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

