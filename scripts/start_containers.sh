#!/usr/bin/env bash
set -euo pipefail

# Ensure the script runs with root privileges for apt operations
if [[ $EUID -ne 0 ]]; then
    echo "Run with sudo to download apt packages" >&2
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
CACHE_DIR="${CACHE_DIR:-/tmp/docker_cache}"
COMPOSE_FILE="$ROOT_DIR/docker-compose.yml"
source "$SCRIPT_DIR/shared_checks.sh"

LOG_DIR="$ROOT_DIR/logs"
LOG_FILE="$LOG_DIR/start_containers.log"
mkdir -p "$LOG_DIR"
# Mirror all output to a startup log for troubleshooting
exec > >(tee -a "$LOG_FILE") 2>&1

# File storing the SECRET_KEY during startup
secret_file="$ROOT_DIR/secret_key.txt"

# Remove the temporary secret file on exit or error
cleanup() {
    rm -f "$secret_file"
}

log_step() {
    echo "===== $1 ====="
}

trap 'echo "[ERROR] start_containers.sh failed near line $LINENO. Check $LOG_FILE for details." >&2; cleanup' ERR
trap cleanup EXIT

FORCE_FRONTEND=false
OFFLINE=false

usage() {
    cat <<EOF
Usage: $(basename "$0") [--force-frontend] [--offline]

Builds the frontend if needed and starts the docker compose stack.
Run with sudo so apt packages can be downloaded and to adjust ownership of the uploads, transcripts and logs directories.
--force-frontend  Rebuild the frontend even if frontend/dist exists.
--offline        Skip prestage_dependencies.sh and use existing cached packages.
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        -h|--help)
            usage
            exit 0
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

log_step "STAGING"
# Ensure Node.js is available before downloading npm packages
install_node18
# Stage dependencies for an offline build, clearing the cache before downloads
if [ "${SKIP_PRESTAGE:-}" = "1" ] || [ "$OFFLINE" = true ]; then
    echo "Skipping prestage_dependencies.sh (offline mode)"
else
    "$SCRIPT_DIR/prestage_dependencies.sh"
fi
# Verify Docker and cache directories are ready
check_docker_running
check_cache_dirs
echo "Checking network connectivity and installing dependencies..."
stage_build_dependencies

# Build the frontend if needed before verifying offline assets
if [ "$FORCE_FRONTEND" = true ] || [ ! -d "$ROOT_DIR/frontend/dist" ]; then
    echo "Building frontend..."
    (cd "$ROOT_DIR/frontend" && npm run build)
fi

# Verify required offline assets after downloads complete
verify_offline_assets

log_step "VERIFICATION"
setup_persistent_dirs
check_whisper_models
check_ffmpeg
ensure_env_file

log_step "BUILD"
printf '%s' "$SECRET_KEY" > "$secret_file"


services=(api worker)
build_targets=()
images_to_check=()
for svc in "${services[@]}"; do
    image="whisper-transcriber-${svc}:latest"
    rebuild=false
    if ! docker image inspect "$image" >/dev/null 2>&1; then
        echo "Image $image missing. Marking $svc for rebuild."
        rebuild=true
    else
        container_id=$(docker compose -f "$COMPOSE_FILE" ps -q "$svc" || true)
        if [ -n "$container_id" ]; then
            health=$(docker inspect --format '{{ .State.Health.Status }}' "$container_id" 2>/dev/null || echo "")
            if [ "$health" = "unhealthy" ]; then
                echo "$svc container unhealthy. Marking for rebuild."
                rebuild=true
            fi
        fi
    fi
    if [ "$rebuild" = true ]; then
        build_targets+=("$svc")
    fi
    images_to_check+=("$image")
done

if [ "${#build_targets[@]}" -eq 0 ]; then
    echo "All images present and containers healthy. Skipping rebuild."
else
    echo "Rebuilding services: ${build_targets[*]}"
    if supports_secret; then
        temp_secret=$(mktemp)
        printf '%s' "$SECRET_KEY" > "$temp_secret"
        docker compose -f "$COMPOSE_FILE" build \
            --secret id=secret_key,src="$temp_secret" \
            --network=none \
            --build-arg INSTALL_DEV=true "${build_targets[@]}"
        rm -f "$temp_secret"
    else
        docker compose -f "$COMPOSE_FILE" build \
            --network=none \
            --build-arg SECRET_KEY="$SECRET_KEY" \
            --build-arg INSTALL_DEV=true "${build_targets[@]}"
    fi
    echo "Verifying built images..."
    verify_built_images "${images_to_check[@]}"
fi

log_step "STARTUP"
echo "Environment variables:" >&2
env | sort | grep -v '^SECRET_KEY=' >&2

echo "Starting containers with docker compose..."
docker compose -f "$COMPOSE_FILE" up -d api worker broker db

# Wait for the API service to become healthy
max_wait=${API_HEALTH_TIMEOUT:-300}
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
