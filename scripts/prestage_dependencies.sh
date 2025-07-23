#!/usr/bin/env bash
set -euo pipefail
trap 'echo "prestage_dependencies.sh failed near line $LINENO" >&2' ERR

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

LOG_FILE="$ROOT_DIR/logs/prestage_dependencies.log"
mkdir -p "$(dirname "$LOG_FILE")"
exec > >(tee -a "$LOG_FILE") 2>&1

CACHE_DIR="$ROOT_DIR/cache"
IMAGES_DIR="$CACHE_DIR/images"

mkdir -p "$IMAGES_DIR" "$CACHE_DIR/pip" "$CACHE_DIR/npm"

COMPOSE_FILE="$ROOT_DIR/docker-compose.yml"

# Determine base image from Dockerfile
BASE_IMAGE=$(grep -m1 '^FROM ' "$ROOT_DIR/Dockerfile" | awk '{print $2}')

# Gather images used by docker-compose services
mapfile -t COMPOSE_IMAGES < <(grep -E '^\s*image:' "$COMPOSE_FILE" | awk '{print $2}')

IMAGES=("$BASE_IMAGE" "${COMPOSE_IMAGES[@]}")
IMAGES=($(printf '%s\n' "${IMAGES[@]}" | sort -u))

echo "Pulling docker images..."
for img in "${IMAGES[@]}"; do
    echo "Fetching $img"
    docker pull "$img"
    tar_name=$(echo "$img" | sed 's#[/:]#_#g').tar
    docker save "$img" -o "$IMAGES_DIR/$tar_name"
done

echo "Downloading Python packages..."
pip download -d "$CACHE_DIR/pip" \
    -r "$ROOT_DIR/requirements.txt" \
    -r "$ROOT_DIR/requirements-dev.txt"

echo "Caching Node modules..."
npm install --prefix "$ROOT_DIR/frontend"
npm ci --prefix "$ROOT_DIR/frontend" --cache "$CACHE_DIR/npm"

echo "Dependencies staged under $CACHE_DIR"

