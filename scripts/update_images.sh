#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
CACHE_DIR="${CACHE_DIR:-$ROOT_DIR/cache}"
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

log_step "STAGING"
# Stage dependencies needed for an offline build
"$SCRIPT_DIR/prestage_dependencies.sh"
# Verify Docker and cache directories are ready
check_docker_running
check_cache_dirs
echo "Checking network connectivity and installing dependencies..."
stage_build_dependencies

echo "Building frontend assets..."
(cd "$ROOT_DIR/frontend" && npm run build)

# Verify required offline assets after downloads complete
verify_offline_assets

# Return 0 if docker compose build supports --secret
supports_secret() {
    docker compose build --help 2>/dev/null | grep -q -- "--secret"
}

# Verify the given Docker images exist
verify_built_images() {
    local images=("$@")
    for img in "${images[@]}"; do
        if ! docker image inspect "$img" >/dev/null 2>&1; then
            echo "Missing Docker image $img" >&2
            return 1
        fi
    done
}

# Load SECRET_KEY from .env
ensure_env_file

log_step "VERIFICATION"
echo "Verifying Whisper models and ffmpeg..."
check_whisper_models
check_ffmpeg

echo "Environment variables:" >&2
env | sort >&2

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
            --build-arg INSTALL_DEV=true "${build_targets[@]}"
        rm -f "$secret_file"
    else
        docker compose -f "$COMPOSE_FILE" build \
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
