#!/usr/bin/env bash
set -euo pipefail

# Codex: unified build entrypoint

print_help() {
    cat <<EOF
Usage: $(basename "$0") [--full|--offline|--update|--frontend-only|--validate-only] [--purge-cache] [--verify-sources] [--docker-cleanup]

--full            Full online build (default)
--offline         Require all assets to be pre-cached
--update          Incrementally refresh dependencies and rebuild
--frontend-only   Build frontend assets only
--validate-only   Run validation checks only, no build
--purge-cache     Remove CACHE_DIR before staging dependencies
--verify-sources  Test connectivity to package mirrors and registry
--docker-cleanup  Remove unused Docker images and builders
--help            Show this help message
EOF
}

for arg in "$@"; do
    case "$arg" in
        -h|--help)
            print_help
            exit 0
            ;;
    esac
done  # Codex: help guard

echo "[NOTICE] Legacy build helpers removed. Use this script directly." >&2  # Codex:

if [[ $EUID -ne 0 ]]; then
    echo "Run with sudo to download apt packages" >&2
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
source "$SCRIPT_DIR/shared_checks.sh"
set_cache_dir  # Codex: cache override for WSL hosts

LOG_DIR="$ROOT_DIR/logs"
LOG_FILE="$LOG_DIR/whisper_build.log"
mkdir -p "$LOG_DIR"
exec > >(tee -a "$LOG_FILE") 2>&1

# Codex: ensure check_env.sh output is logged
bash "$SCRIPT_DIR/check_env.sh" >> "$LOG_FILE" 2>&1

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

# Track selected mode. Only one mode flag may be provided
MODE="full"
MODE_SET=false
PURGE_CACHE=false
VERIFY_SOURCES=false
# Codex: new mode flags
DOCKER_CLEANUP=false
# Codex: removed legacy usage() helper

while [[ $# -gt 0 ]]; do
    case "$1" in
        --full)
            if $MODE_SET; then
                echo "Conflicting switches detected. Only one build mode can be used at a time." >&2
                exit 1
            fi
            MODE="full"
            MODE_SET=true
            shift
            ;;
        --offline)
            if $MODE_SET; then
                echo "Conflicting switches detected. Only one build mode can be used at a time." >&2
                exit 1
            fi
            MODE="offline"
            MODE_SET=true
            shift
            ;;
        --update)  # Codex: update switch
            if $MODE_SET; then
                echo "Conflicting switches detected. Only one build mode can be used at a time." >&2
                exit 1
            fi
            MODE="update"
            MODE_SET=true
            shift
            ;;
        --frontend-only)  # Codex: frontend-only switch
            if $MODE_SET; then
                echo "Conflicting switches detected. Only one build mode can be used at a time." >&2
                exit 1
            fi
            MODE="frontend_only"
            MODE_SET=true
            shift
            ;;
        --validate-only)  # Codex: validate-only switch
            if $MODE_SET; then
                echo "Conflicting switches detected. Only one build mode can be used at a time." >&2
                exit 1
            fi
            MODE="validate_only"
            MODE_SET=true
            shift
            ;;
        --docker-cleanup)  # Codex: docker-cleanup switch
            DOCKER_CLEANUP=true
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
            print_help
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            print_help >&2
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

# Codex: build helper for frontend-only mode
docker_build_frontend() {
    log_step "FRONTEND"
    echo "Building frontend assets only (--frontend-only)"
    (cd "$ROOT_DIR/frontend" && npm run build)
    if [ ! -f "$ROOT_DIR/frontend/dist/index.html" ]; then
        echo "[ERROR] Frontend build failed or dist/ missing" >&2
        exit 1
    fi
    echo "Frontend assets built under frontend/dist"
}

# Codex: validation mode helper
run_validations() {
    if $VERIFY_SOURCES; then
        log_step "VERIFY SOURCES"
        check_download_sources
    fi
    if [ "${SKIP_CACHE_CHECKS:-false}" != "true" ]; then
        verify_cache_integrity
    fi
    check_whisper_models
    check_ffmpeg
    ensure_env_file
    echo "Validation successful."
}

# Codex: docker cleanup helper
docker_cleanup() {
    log_step "CLEANUP"
    echo "Cleaning up unused Docker images (--docker-cleanup)"
    docker image prune -f
    docker builder prune -f
}

# Codex: incremental rebuild helper
docker_build_update() {
    log_step "UPDATE"
    echo "Performing incremental build (--update)"
    download_dependencies
    local hash_file="$LOG_DIR/.update_hash"
    local current_hash
    current_hash=$(sha1sum "$ROOT_DIR/Dockerfile" \
        "$ROOT_DIR/requirements.txt" \
        "$ROOT_DIR/requirements-dev.txt" \
        "$ROOT_DIR/frontend/package.json" \
        "$ROOT_DIR/frontend/package-lock.json" 2>/dev/null | sha1sum | awk '{print $1}')
    local rebuild=false
    if [ ! -f "$hash_file" ] || [ "$(cat "$hash_file" 2>/dev/null)" != "$current_hash" ]; then
        rebuild=true
        echo "$current_hash" > "$hash_file"
    fi
    if ! docker image inspect whisper-app >/dev/null 2>&1; then
        rebuild=true
    fi
    if $rebuild; then
        docker_build
    else
        echo "No dependency changes detected. Skipping Docker rebuild."
        docker compose -f "$ROOT_DIR/docker-compose.yml" up -d api worker broker db
    fi
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

    if [ "${SKIP_CACHE_CHECKS:-false}" != "true" ]; then
        verify_cache_integrity
    fi

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
    check_download_sources  # Codex: network connectivity test for package mirrors
fi

case "$MODE" in
    full)
        log_step "STAGING"
        echo "Performing full rebuild using Docker cache. All images will be rebuilt." >&2
        download_dependencies
        docker_build
        ;;
    offline)
        log_step "OFFLINE VERIFY"
        echo "Performing full rebuild using only cached assets." >&2
        verify_cache_integrity  # Codex: offline mode validates cached assets
        docker_build
        ;;
    update) # Codex: update workflow
        docker_build_update
        ;;
    frontend_only) # Codex: frontend-only workflow
        log_step "FRONTEND ONLY"
        install_node18
        (cd "$ROOT_DIR/frontend" && npm install)
        docker_build_frontend
        ;;
    validate_only) # Codex: validate-only workflow
        log_step "VALIDATION"
        SKIP_CACHE_CHECKS=true run_validations
        rm -f "$secret_file_runtime"
        [ "$DOCKER_CLEANUP" = true ] && docker_cleanup
        exit 0
        ;;
    *)
        echo "Unknown MODE $MODE" >&2
        exit 1
        ;;
esac

rm -f "$secret_file_runtime"
[ "$DOCKER_CLEANUP" = true ] && docker_cleanup

