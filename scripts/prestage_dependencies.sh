#!/usr/bin/env bash
set -euo pipefail
trap 'echo "prestage_dependencies.sh failed near line $LINENO" >&2' ERR

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
source "$SCRIPT_DIR/shared_checks.sh"

# Parse options
DRY_RUN="${DRY_RUN:-0}"
CHECKSUM="0"
VERIFY_ONLY="0"
while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run)
            DRY_RUN=1
            shift
            ;;
        --checksum)
            CHECKSUM="1"
            shift
            ;;
        --verify-only)
            VERIFY_ONLY="1"
            shift
            ;;
        -h|--help)
            echo "Usage: $(basename "$0") [--dry-run] [--checksum] [--verify-only]" >&2
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            exit 1
            ;;
    esac
done

# When not verifying only, ensure root and internet connectivity
if [ "$VERIFY_ONLY" != "1" ]; then
    if [[ $EUID -ne 0 ]]; then
        echo "Run with sudo to download apt packages" >&2
        exit 1
    fi
    if [ "$DRY_RUN" != "1" ] && ! check_internet; then
        echo "Network unreachable. Connect before running or use offline assets." >&2
        exit 1
    fi
    check_apt_sources
fi

# Execute a command unless DRY_RUN is enabled
run_cmd() {
    echo "+ $*"
    if [ "$DRY_RUN" != "1" ]; then
        "$@"
    fi
}

# Default cache directory when not set
if [ -z "${CACHE_DIR:-}" ]; then
    CACHE_DIR="/tmp/docker_cache"
fi

export CACHE_DIR

if [ "$VERIFY_ONLY" = "1" ]; then
    verify_offline_assets
    exit $?
fi

# Verify that CACHE_DIR is writable before continuing.
check_cache_writable() {
    mkdir -p "$CACHE_DIR" || true
    local test_file="$CACHE_DIR/.write_test"
    if ! touch "$test_file" >/dev/null 2>&1; then
        echo "Cannot write to $CACHE_DIR. Set CACHE_DIR to a writable path or fix permissions." >&2
        exit 1
    fi
    rm -f "$test_file"
}

# Ensure Node.js 18 is installed before running npm commands
run_cmd install_node18

LOG_FILE="$ROOT_DIR/logs/prestage_dependencies.log"
mkdir -p "$(dirname "$LOG_FILE")"
exec > >(tee -a "$LOG_FILE") 2>&1

# Exit early if the cache directory is not writable
check_cache_writable

# Always start from a clean cache so staged packages match the
# current requirements.
run_cmd rm -rf "$CACHE_DIR"

IMAGES_DIR="$CACHE_DIR/images"
mkdir -p "$IMAGES_DIR" "$CACHE_DIR/pip" "$CACHE_DIR/npm" "$CACHE_DIR/apt" \
    "$ROOT_DIR/cache/pip" "$ROOT_DIR/cache/npm" "$ROOT_DIR/cache/apt" \
    "$ROOT_DIR/cache/images"

# Echo a marker for major milestones
log_step() {
    echo "===== $1 ====="
}


# Ensure Docker is running and required cache directories exist
check_docker_running
check_cache_dirs

COMPOSE_FILE="$ROOT_DIR/docker-compose.yml"

# Determine base image from Dockerfile and extract codename
BASE_IMAGE=$(grep -m1 '^FROM ' "$ROOT_DIR/Dockerfile" | awk '{print $2}')
BASE_CODENAME="${BASE_IMAGE##*-}"

# Read host VERSION_CODENAME
source /etc/os-release
HOST_CODENAME="${VERSION_CODENAME:-}"

# Abort when host codename differs from the Dockerfile base unless overridden
if [ "${ALLOW_OS_MISMATCH:-}" != "1" ] && [ "$HOST_CODENAME" != "$BASE_CODENAME" ]; then
    echo "OS codename mismatch: Dockerfile uses '$BASE_CODENAME', host is '$HOST_CODENAME'. Set ALLOW_OS_MISMATCH=1 to bypass." >&2
    exit 1
fi

# Gather images used by docker-compose services
mapfile -t COMPOSE_IMAGES < <(grep -E '^\s*image:' "$COMPOSE_FILE" | awk '{print $2}')

IMAGES=("$BASE_IMAGE" "${COMPOSE_IMAGES[@]}")
IMAGES=($(printf '%s\n' "${IMAGES[@]}" | sort -u))

log_step "IMAGES"
echo "Pulling docker images..."
for img in "${IMAGES[@]}"; do
    echo "Fetching $img"
    run_cmd docker pull "$img"
    tar_name=$(echo "$img" | sed 's#[/:]#_#g').tar
    run_cmd docker save "$img" -o "$IMAGES_DIR/$tar_name"
    if [ "$DRY_RUN" != "1" ] && [ "$img" = "$BASE_IMAGE" ]; then
        digest=$(docker image inspect "$img" --format '{{index .RepoDigests 0}}' | awk -F@ '{print $2}')
        sanitized=$(echo "$img" | sed 's#[/:]#_#g')
        echo "$digest" > "$ROOT_DIR/cache/images/${sanitized}_digest.txt"
    fi
done

log_step "PYTHON"
echo "Downloading and building Python wheels..."
run_cmd pip wheel --wheel-dir "$CACHE_DIR/pip" \
    -r "$ROOT_DIR/requirements.txt" \
    -r "$ROOT_DIR/requirements-dev.txt"

# Verify the Whisper wheel was created
if [ "$DRY_RUN" != "1" ]; then
    if ! ls "$CACHE_DIR/pip"/openai_whisper-*.whl >/dev/null 2>&1; then
        echo "openai_whisper wheel build failed; expected $CACHE_DIR/pip/openai_whisper-*.whl" >&2
        exit 1
    fi
    ls "$CACHE_DIR/pip"/*.whl | xargs -n1 basename | sort > "$CACHE_DIR/pip/pip_versions.txt"
    cp "$CACHE_DIR/pip/pip_versions.txt" "$ROOT_DIR/cache/pip/pip_versions.txt"
fi

log_step "NPM"
echo "Caching Node modules..."
run_cmd npm install --prefix "$ROOT_DIR/frontend"
run_cmd npm ci --prefix "$ROOT_DIR/frontend" --cache "$CACHE_DIR/npm"
if [ "$DRY_RUN" != "1" ]; then
    npm ls --prefix "$ROOT_DIR/frontend" --depth=0 > "$CACHE_DIR/npm/npm_versions.txt"
    cp "$CACHE_DIR/npm/npm_versions.txt" "$ROOT_DIR/cache/npm/npm_versions.txt"
    tar -cf "$CACHE_DIR/npm/npm-cache.tar" -C "$CACHE_DIR/npm" .
fi

log_step "APT"
echo "Downloading apt packages..."
run_cmd apt-get update
run_cmd curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
run_cmd apt-get install -y --download-only --reinstall --no-install-recommends \
    ffmpeg git curl gosu nodejs docker-compose-plugin
if ls /var/cache/apt/archives/*.deb >/dev/null 2>&1; then
    mismatch=0
    for pkg in /var/cache/apt/archives/*.deb; do
        deb=$(basename "$pkg")
        if [[ "$deb" != *"$BASE_CODENAME"* ]]; then
            echo "Package $deb does not match codename $BASE_CODENAME" >&2
            mismatch=1
        fi
    done
    if [ $mismatch -ne 0 ]; then
        echo "Aborting due to codename mismatch" >&2
        exit 1
    fi
    ls /var/cache/apt/archives/*.deb \
        | xargs -n1 basename | tee "$CACHE_DIR/apt/deb_list.txt" > "$ROOT_DIR/cache/apt/deb_list.txt"
    run_cmd cp /var/cache/apt/archives/*.deb "$CACHE_DIR/apt/"
else
    echo "No deb files found in /var/cache/apt/archives" >&2
fi
run_cmd apt-get clean
run_cmd rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*

log_step "COMPLETE"
echo "Dependencies staged under $CACHE_DIR"

if [ "$CHECKSUM" = "1" ]; then
    for sub in pip npm apt images; do
        dir="$CACHE_DIR/$sub"
        if [ -d "$dir" ]; then
            (cd "$dir" && find . -type f -exec sha256sum {} \;) \
                | sort -k2 > "$dir/sha256sums.txt"
        fi
    done

    manifest="$CACHE_DIR/manifest.txt"
    echo "BASE_CODENAME=$BASE_CODENAME" > "$manifest"
    for sub in pip npm apt images; do
        file="$CACHE_DIR/$sub/sha256sums.txt"
        if [ -f "$file" ]; then
            hash=$(sha256sum "$file" | awk '{print $1}')
            echo "$sub=$hash" >> "$manifest"
        fi
    done

    cp "$manifest" "$ROOT_DIR/cache/manifest.txt"
fi

