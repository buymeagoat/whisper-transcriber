#!/usr/bin/env bash
set -euo pipefail
set -x

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

# End of whisper_build.sh
LOG_DIR="$ROOT_DIR/logs"
LOG_FILE="$LOG_DIR/whisper_build.log"
mkdir -p "$LOG_DIR"
# Add build attempt header

echo "" >> "$LOG_FILE"
echo "========== NEW BUILD ATTEMPT: $(date '+%Y-%m-%d %H:%M:%S') ==========" >> "$LOG_FILE"
# Remove exec > >(awk ...) and fallback logic for compatibility
# All output will be logged using tee -a "$LOG_FILE" in each command



# Function definitions (move to top)
populate_pip_cache() {
    local pip_cache="$CACHE_DIR/pip"
    echo "[INFO] Populating pip cache for offline build..." | tee -a "$LOG_FILE"
    pip download -d "$pip_cache" -r "$ROOT_DIR/requirements.txt"
    if [ $? -ne 0 ]; then
        echo "[ERROR] pip cache population failed. Check pip logs for details." | tee -a "$LOG_FILE"
        exit 1
    fi
    echo "[INFO] pip cache populated."
}

populate_apt_cache() {
    local apt_cache="$CACHE_DIR/apt"
    local apt_list="$apt_cache/deb_list.txt"
    echo "[INFO] Populating apt cache for offline build..." | tee -a "$LOG_FILE"
    sudo apt-get clean
    sudo apt-get update
    # Download required debs if missing
    if ! ls "$apt_cache/nodejs_*" >/dev/null 2>&1; then
        echo "[INFO] Downloading nodejs deb package..." | tee -a "$LOG_FILE"
        sudo apt download nodejs -o Dir::Cache::archives="$apt_cache"
    fi
    if ! ls "$apt_cache/docker-compose-plugin_*" >/dev/null 2>&1; then
        echo "[INFO] Downloading docker-compose-plugin deb package..." | tee -a "$LOG_FILE"
        sudo apt download docker-compose-plugin -o Dir::Cache::archives="$apt_cache"
    fi
    # Replace with your actual package list file if different
    sudo apt-get install --download-only -o Dir::Cache::archives="$apt_cache" $(grep -vE '^\s*#' "$ROOT_DIR/scripts/apt-packages.txt")
    if [ $? -ne 0 ]; then
        echo "[ERROR] apt cache population failed. Check apt logs for details." | tee -a "$LOG_FILE"
        exit 1
    fi
    echo "[INFO] apt cache populated."
}

populate_npm_cache() {
    local npm_cache="$CACHE_DIR/npm"
    local frontend_dir="$ROOT_DIR/frontend"
    echo "[INFO] Populating npm cache for offline build..." | tee -a "$LOG_FILE"
    npm install --prefix "$frontend_dir" --cache "$npm_cache"
    if [ $? -ne 0 ]; then
        echo "[ERROR] npm install failed. Check npm logs for details." | tee -a "$LOG_FILE"
        exit 1
    fi
    echo "[INFO] npm cache populated. Running offline install..." | tee -a "$LOG_FILE"
    npm ci --offline --prefix "$frontend_dir" --cache "$npm_cache"
    if [ $? -ne 0 ]; then
        echo "[WARN] npm offline install failed. Retrying online to populate missing cache." | tee -a "$LOG_FILE"
        npm ci --prefix "$frontend_dir" --cache "$npm_cache"
        if [ $? -ne 0 ]; then
            echo "[ERROR] npm online install failed after offline failure. Check npm logs for details." | tee -a "$LOG_FILE"
            exit 1
        fi
        echo "[INFO] Retrying offline install after cache update..." | tee -a "$LOG_FILE"
        npm ci --offline --prefix "$frontend_dir" --cache "$npm_cache"
        if [ $? -ne 0 ]; then
            echo "[ERROR] npm offline install failed again. Some dependencies may still be missing from cache." | tee -a "$LOG_FILE"
            exit 1
        fi
    fi
}

cache_docker_images() {
    local image_cache="$CACHE_DIR/images"
    local images=("python:3.11-bookworm" "postgres:15-alpine" "rabbitmq:3-management")
    mkdir -p "$image_cache"
    for img in "${images[@]}"; do
        local tar="$image_cache/$(echo $img | sed 's#[/:]#_#g').tar"
        if [ ! -f "$tar" ]; then
            echo "[INFO] Saving Docker image $img to $tar..." | tee -a "$LOG_FILE"
            docker pull "$img"
            docker save "$img" -o "$tar"
        fi
    done
}

verify_cache_integrity() {
    check_cache_dirs
    verify_offline_assets
    cache_docker_images
}

preflight_checks() {
    # Check for required executables
    for exe in python3 pip node npm docker ffmpeg; do
        if ! command -v "$exe" >/dev/null 2>&1; then
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: Required executable '$exe' not found in PATH." >&2
            exit 1
        fi
    done
    # Check for docker compose (v2)
    if ! docker compose version >/dev/null 2>&1; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: 'docker compose' command not available. Install Docker Compose v2." >&2
        exit 1
    fi
    # Check for sudo/root access
    if [[ $EUID -ne 0 ]]; then
        if ! command -v sudo >/dev/null 2>&1; then
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: Sudo required for some operations, but 'sudo' not found." >&2
            exit 1
        fi
    fi
    # Check Node.js version
    node_version=$(node --version | sed 's/^v//')
    node_major=${node_version%%.*}
    if [ "$node_major" -lt 18 ]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: Node.js 18 or newer is required. Found $node_version" >&2
        exit 1
    fi
    # Check internet connectivity
    if ! curl -sSf https://pypi.org >/dev/null 2>&1; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: No internet connectivity to pypi.org." >&2
        exit 1
    fi
    if ! curl -sSf https://registry.npmjs.org >/dev/null 2>&1; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: No internet connectivity to registry.npmjs.org." >&2
        exit 1
    fi
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Running preflight checks..."
    # Use default_cache_dir logic from shared_checks.sh
    CACHE_DIR=""
    if grep -qi microsoft /proc/version; then
        CACHE_DIR="/mnt/wsl/shared/docker_cache"
    else
        CACHE_DIR="/tmp/docker_cache"
    fi
    base="$CACHE_DIR"
    dirs=("$base/images" "$base/pip" "$base/npm" "$base/apt")
    for d in "${dirs[@]}"; do
        [ -d "$d" ] || mkdir -p "$d"
    done
    [ -f "$base/apt/deb_list.txt" ] || touch "$base/apt/deb_list.txt"
    [ -f "$ROOT_DIR/.env" ] || echo "SECRET_KEY=CHANGE_ME" > "$ROOT_DIR/.env"
    # Whisper model files check
    model_dir="$ROOT_DIR/models"
    required_models=(base.pt small.pt medium.pt large-v3.pt tiny.pt)
    for m in "${required_models[@]}"; do
        [ -f "$model_dir/$m" ] || echo "[$(date '+%Y-%m-%d %H:%M:%S')] Warning: missing model file $model_dir/$m" >&2
    done
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Preflight checks complete."
}

# Run preflight checks before anything else
preflight_checks

# Codex: generate manifest before environment checks
python3 "$SCRIPT_DIR/update_manifest.py"

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


# Improved argument parsing: only shift once per loop, handle zero args
while [[ $# -gt 0 ]]; do
    case "$1" in
        --full)
            if $MODE_SET; then
                echo "Conflicting switches detected. Only one build mode can be used at a time." >&2
                exit 1
            fi
            MODE="full"
            MODE_SET=true
            ;;
        --offline)
            if $MODE_SET; then
                echo "Conflicting switches detected. Only one build mode can be used at a time." >&2
                exit 1
            fi
            MODE="offline"
            MODE_SET=true
            ;;
        --update)
            if $MODE_SET; then
                echo "Conflicting switches detected. Only one build mode can be used at a time." >&2
                exit 1
            fi
            MODE="update"
            MODE_SET=true
            ;;
        --frontend-only)
            if $MODE_SET; then
                echo "Conflicting switches detected. Only one build mode can be used at a time." >&2
                exit 1
            fi
                echo "[INFO] Ensuring pytest is installed from PyPI..."
                pip install pytest --index-url https://pypi.org/simple
                if ! pip install --no-index --find-links "$pip_cache" -r "$ROOT_DIR/requirements.txt"; then
                    echo "[WARNING] Cached pip install failed. Retrying with online PyPI for missing packages..."
                    pip install -r "$ROOT_DIR/requirements.txt"
                fi
            MODE_SET=true
            ;;
        --validate-only)
            if $MODE_SET; then
                echo "Conflicting switches detected. Only one build mode can be used at a time." >&2
                exit 1
            fi
            MODE="validate_only"
            MODE_SET=true
            ;;
        --docker-cleanup)
            DOCKER_CLEANUP=true
            ;;
        --purge-cache)
            PURGE_CACHE=true
            ;;
        --verify-sources)
            VERIFY_SOURCES=true
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

download_dependencies() {
    if $PURGE_CACHE; then
        echo "Purging cache at $CACHE_DIR" >&2
        rm -rf "$CACHE_DIR"
    fi
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Installing Node.js 18..." | tee -a "$LOG_FILE"
        install_node18 2>&1 | tee -a "$LOG_FILE"
        node_status=${PIPESTATUS[0]}
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] install_node18 exit code: $node_status" | tee -a "$LOG_FILE"
        if [ "$node_status" -ne 0 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: Node.js installation failed." >&2
            exit 1
        fi
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Checking if Docker is running..." | tee -a "$LOG_FILE"
        check_docker_running 2>&1 | tee -a "$LOG_FILE"
        docker_status=${PIPESTATUS[0]}
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] check_docker_running exit code: $docker_status" | tee -a "$LOG_FILE"
        if [ "$docker_status" -ne 0 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: Docker daemon is not running. Start Docker and retry." >&2
            exit 1
        fi
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Staging build dependencies..." | tee -a "$LOG_FILE"
        stage_build_dependencies 2>&1 | tee -a "$LOG_FILE"
        stage_status=${PIPESTATUS[0]}
    echo "[$(date \"%Y-%m-%d %H:%M:%S\")] stage_build_dependencies exit code: $stage_status" | tee -a "$LOG_FILE"
        if [ "$stage_status" -ne 0 ]; then
        echo "[$(date \"%Y-%m-%d %H:%M:%S\")] ERROR: Failed to stage build dependencies. Check cache directories and network." >&2
            exit 1
        fi
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
            health=$(docker inspect --format "{{ .State.Health.Status }}" "$container_id" 2>/dev/null || echo "starting")
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
cat <<EOM
Available test scripts:
    scripts/run_tests.sh         - runs backend tests plus frontend unit and Cypress end-to-end tests. Recommended after a full build.
    scripts/run_backend_tests.sh - executes only the backend tests and verifies the /health and /version endpoints.
EOM
}

# Ensure function closure before case statement

if $VERIFY_SOURCES; then
    log_step "VERIFY SOURCES"
    check_download_sources  # Codex: network connectivity test for package mirrors
fi

case "$MODE" in
    full)
        log_step "STAGING"
        echo "Performing full rebuild using Docker cache. All images will be rebuilt." >&2
        download_dependencies
        populate_pip_cache
        populate_apt_cache
        populate_npm_cache
        docker_build
        ;;
    offline)
        log_step "OFFLINE VERIFY"
        echo "Performing full rebuild using only cached assets." >&2
        verify_cache_integrity  # Codex: offline mode validates cached assets
        populate_npm_cache
        docker_build
        ;;
    update) # Codex: update workflow
        docker_build_update
        ;;
    frontend_only) # Codex: frontend-only workflow
        log_step "FRONTEND ONLY"
        install_node18
        populate_npm_cache
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

