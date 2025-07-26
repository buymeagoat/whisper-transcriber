#!/usr/bin/env bash
set -euo pipefail
trap 'echo "prestage_dependencies.sh failed near line $LINENO" >&2' ERR

# Ensure script is run with root privileges for apt operations
if [[ $EUID -ne 0 ]]; then
    echo "Run with sudo to download apt packages" >&2
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
source "$SCRIPT_DIR/shared_checks.sh"

# Use /mnt/c/whisper_cache on WSL for persistence unless CACHE_DIR is provided.
if [ -z "${CACHE_DIR:-}" ]; then
    if grep -qi microsoft /proc/version && [ -d /mnt/c ]; then
        CACHE_DIR="/mnt/c/whisper_cache"
    else
        CACHE_DIR="/tmp/docker_cache"
    fi
fi

# Ensure Node.js 18 is installed before running npm commands
install_node18

LOG_FILE="$ROOT_DIR/logs/prestage_dependencies.log"
mkdir -p "$(dirname "$LOG_FILE")"
exec > >(tee -a "$LOG_FILE") 2>&1

export CACHE_DIR

# Always start from a clean cache so staged packages match the
# current requirements.
rm -rf "$CACHE_DIR"

IMAGES_DIR="$CACHE_DIR/images"
mkdir -p "$IMAGES_DIR" "$CACHE_DIR/pip" "$CACHE_DIR/npm" "$CACHE_DIR/apt"

# Echo a marker for major milestones
log_step() {
    echo "===== $1 ====="
}

# Ensure Docker is running and required cache directories exist
check_docker_running
check_cache_dirs

COMPOSE_FILE="$ROOT_DIR/docker-compose.yml"

# Determine base image from Dockerfile
BASE_IMAGE=$(grep -m1 '^FROM ' "$ROOT_DIR/Dockerfile" | awk '{print $2}')

# Gather images used by docker-compose services
mapfile -t COMPOSE_IMAGES < <(grep -E '^\s*image:' "$COMPOSE_FILE" | awk '{print $2}')

IMAGES=("$BASE_IMAGE" "${COMPOSE_IMAGES[@]}")
IMAGES=($(printf '%s\n' "${IMAGES[@]}" | sort -u))

log_step "IMAGES"
echo "Pulling docker images..."
for img in "${IMAGES[@]}"; do
    echo "Fetching $img"
    docker pull "$img"
    tar_name=$(echo "$img" | sed 's#[/:]#_#g').tar
    docker save "$img" -o "$IMAGES_DIR/$tar_name"
done

log_step "PYTHON"
echo "Downloading Python packages..."
pip download -d "$CACHE_DIR/pip" \
    pip \
    -r "$ROOT_DIR/requirements.txt" \
    -r "$ROOT_DIR/requirements-dev.txt"

log_step "NPM"
echo "Caching Node modules..."
npm install --prefix "$ROOT_DIR/frontend"
npm ci --prefix "$ROOT_DIR/frontend" --cache "$CACHE_DIR/npm"

log_step "APT"
echo "Downloading apt packages..."
apt-get update
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt-get install -y --download-only --no-install-recommends \
    ffmpeg git curl gosu nodejs
if ls /var/cache/apt/archives/*.deb >/dev/null 2>&1; then
    ls /var/cache/apt/archives/*.deb \
        | xargs -n1 basename > "$CACHE_DIR/apt/deb_list.txt"
    cp /var/cache/apt/archives/*.deb "$CACHE_DIR/apt/"
else
    echo "No deb files found in /var/cache/apt/archives" >&2
fi
apt-get clean && rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*

log_step "COMPLETE"
echo "Dependencies staged under $CACHE_DIR"

