#!/usr/bin/env bash
set -euo pipefail

# Ensure the script runs with root privileges for apt operations
if [[ $EUID -ne 0 ]]; then
    echo "Run with sudo to download apt packages" >&2
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Choose a persistent cache location when running under WSL. This keeps
# cached packages on the Windows drive so they survive Linux
# distribution resets.
if [ -z "${CACHE_DIR:-}" ]; then
    if grep -qi microsoft /proc/version && [ -d /mnt/c ]; then
        CACHE_DIR="/mnt/c/whisper_cache"
    else
        CACHE_DIR="/tmp/docker_cache"
    fi
fi
COMPOSE_FILE="$ROOT_DIR/docker-compose.yml"
source "$SCRIPT_DIR/shared_checks.sh"

LOG_DIR="$ROOT_DIR/logs"
LOG_FILE="$LOG_DIR/update_images.log"
mkdir -p "$LOG_DIR"
exec > >(tee -a "$LOG_FILE") 2>&1

log_step() {
    echo "===== $1 ====="
}

trap 'echo "[ERROR] update_images.sh failed near line $LINENO. Check $LOG_FILE for details." >&2' ERR

FORCE_FRONTEND=false
OFFLINE=false

usage() {
    cat <<EOF
Usage: $(basename "$0") [--force-frontend] [--offline]

--force-frontend Rebuild the frontend even if frontend/dist exists.
--offline        Skip prestage_dependencies.sh and use cached packages.
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

if [ "$FORCE_FRONTEND" = true ] || [ ! -d "$ROOT_DIR/frontend/dist" ]; then
    echo "Building frontend assets..."
    (cd "$ROOT_DIR/frontend" && npm run build)
fi

# Verify required offline assets after downloads complete
verify_offline_assets


# Load SECRET_KEY from .env
ensure_env_file

log_step "VERIFICATION"
echo "Verifying Whisper models and ffmpeg..."
check_whisper_models
check_ffmpeg

echo "Environment variables:" >&2
env | sort | grep -v '^SECRET_KEY=' >&2

log_step "BUILD"
# Determine which services require a rebuild
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
        secret_file=$(mktemp)
        printf '%s' "$SECRET_KEY" > "$secret_file"
        docker compose -f "$COMPOSE_FILE" build \
            --secret id=secret_key,src="$secret_file" \
            --network=none \
            --build-arg INSTALL_DEV=true "${build_targets[@]}"
        rm -f "$secret_file"
    else
        docker compose -f "$COMPOSE_FILE" build \
            --network=none \
            --build-arg SECRET_KEY="$SECRET_KEY" \
            --build-arg INSTALL_DEV=true "${build_targets[@]}"
    fi
fi

echo "Verifying built images..."
verify_built_images "${images_to_check[@]}"

if [ "${#build_targets[@]}" -gt 0 ]; then
    log_step "STARTUP"
    echo "Starting containers..."
    docker compose -f "$COMPOSE_FILE" up -d "${build_targets[@]}"
fi

cat <<'EOF'
Images verified. Updated services have been restarted if necessary.
Available test scripts:
  scripts/run_tests.sh         - runs backend tests plus frontend unit and Cypress end-to-end tests.
  scripts/run_backend_tests.sh - executes only the backend tests and verifies the /health and /version endpoints.

Run the desired script to verify the update.
If containers encounter issues, use scripts/diagnose_containers.sh for troubleshooting.
EOF
