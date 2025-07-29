#!/usr/bin/env bash
set -euo pipefail

# Codex: unified build entrypoint

if [[ $EUID -ne 0 ]]; then
    echo "Run with sudo to download apt packages" >&2
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
source "$SCRIPT_DIR/shared_checks.sh"
set_cache_dir
"$SCRIPT_DIR/check_env.sh"

LOG_DIR="$ROOT_DIR/logs"
LOG_FILE="$LOG_DIR/whisper_build.log"
mkdir -p "$LOG_DIR"
exec > >(tee -a "$LOG_FILE") 2>&1

secret_file_runtime="$ROOT_DIR/secret_key.txt"
secret_file=""

cleanup() {
    rm -f "$secret_file_runtime"
    if [ -n "${secret_file:-}" ]; then
        rm -rf "$secret_file"
    fi
}
trap 'echo "[ERROR] whisper_build.sh failed near line $LINENO. Check $LOG_FILE for details." >&2; cleanup' ERR
trap cleanup EXIT

MODE="full"
PURGE_CACHE=false
VERIFY_SOURCES=false

usage() {
    cat <<EOF
Usage: $(basename "$0") [--full|--offline] [--purge-cache] [--verify-sources]

--full            Full online build (default)
--offline         Require all assets to be pre-cached
--purge-cache     Remove CACHE_DIR before staging dependencies
--verify-sources  Test connectivity to package mirrors and registry
--help            Show this help message
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --full)
            MODE="full"
            shift
            ;;
        --offline)
            MODE="offline"
            shift
            ;;
        --purge-cache)
            PURGE_CACHE=true
            shift
            ;;
        --verify-sources)
            VERIFY_SOURCES=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            usage >&2
            exit 1
            ;;
    esac
    shift
done

log_step() { echo "===== $1 ====="; }

check_download_sources() {
    check_internet && check_docker_registry && check_apt_sources
}

verify_cache_integrity() {
    check_cache_dirs
    verify_offline_assets
}

download_dependencies() {
    if $PURGE_CACHE; then
        echo "Purging cache at $CACHE_DIR" >&2
        rm -rf "$CACHE_DIR"
    fi
    install_node18
    check_docker_running
    stage_build_dependencies
}

docker_build() {
    log_step "FRONTEND"
    if [ ! -d "$ROOT_DIR/frontend/dist" ]; then
        echo "Building frontend assets..."
        (cd "$ROOT_DIR/frontend" && npm run build)
    fi
    if [ ! -f "$ROOT_DIR/frontend/dist/index.html" ]; then
        echo "[ERROR] Frontend build failed or dist/ missing" >&2
        exit 1
    fi

    verify_cache_integrity

    docker compose -f "$ROOT_DIR/docker-compose.yml" down -v --remove-orphans || true

    log_step "VERIFICATION"
    check_whisper_models
    check_ffmpeg
    ensure_env_file

    echo "Environment variables:" >&2
    env | sort | grep -v '^SECRET_KEY=' >&2
    printf '%s' "$SECRET_KEY" > "$secret_file_runtime"

    log_step "BUILD"
    echo "Building the production image..."
    if supports_secret; then
        secret_file=$(mktemp)
        printf '%s' "$SECRET_KEY" > "$secret_file"
        docker build --network=none --secret id=secret_key,src="$secret_file" -t whisper-app "$ROOT_DIR"
        rm -f "$secret_file"
    else
        echo "BuildKit secret not found; falling back to --build-arg for SECRET_KEY"
        docker build --network=none --build-arg SECRET_KEY="$SECRET_KEY" -t whisper-app "$ROOT_DIR"
    fi

    echo "Rebuilding API and worker images..."
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
            docker compose -f "$ROOT_DIR/docker-compose.yml" logs api | tail -n 20 >&2 || true
            echo "Run scripts/diagnose_containers.sh for a detailed status report." >&2
            exit 1
        fi
        printf "."
        sleep 5
    done

    echo "Images built and containers started."
    cat <<'EOM'
Available test scripts:
  scripts/run_tests.sh         - runs backend tests plus frontend unit and Cypress end-to-end tests. Recommended after a full build.
  scripts/run_backend_tests.sh - executes only the backend tests and verifies the /health and /version endpoints.
EOM
}

if $VERIFY_SOURCES; then
    log_step "VERIFY SOURCES"
    check_download_sources
fi

if [ "$MODE" = "full" ]; then
    log_step "STAGING"
    download_dependencies
else
    log_step "OFFLINE VERIFY"
    verify_cache_integrity
fi

docker_build
rm -f "$secret_file_runtime"

