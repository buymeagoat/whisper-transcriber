#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

usage() {
    cat <<EOF
Usage: $(basename "$0")

Prunes Docker resources, rebuilds images and starts the compose stack from scratch.
Run scripts/post_build_tests.sh afterward to execute the test suite.
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
    usage
    exit 0
fi

# Remove existing containers, images and volumes to start fresh
docker compose -f "$ROOT_DIR/docker-compose.yml" down -v --remove-orphans || true
docker system prune -af --volumes

# Update the repo
git -C "$ROOT_DIR" fetch
git -C "$ROOT_DIR" pull

# Install Python dependencies
pip install -r "$ROOT_DIR/requirements.txt"

# Install and build the frontend
(cd "$ROOT_DIR/frontend" && npm install && npm run build)

# Verify Whisper model files exist
MODELS=(base.pt small.pt medium.pt large-v3.pt tiny.pt)
for m in "${MODELS[@]}"; do
    if [ ! -f "$ROOT_DIR/models/$m" ]; then
        echo "Missing models/$m. Populate the models/ directory before building." >&2
        exit 1
    fi
done

# Ensure .env with SECRET_KEY
if [ ! -f "$ROOT_DIR/.env" ]; then
    cp "$ROOT_DIR/.env.example" "$ROOT_DIR/.env"
fi

SECRET_KEY=$(grep -E '^SECRET_KEY=' "$ROOT_DIR/.env" | cut -d= -f2-)
if [ -z "$SECRET_KEY" ] || [ "$SECRET_KEY" = "CHANGE_ME" ]; then
    SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
    sed -i "s/^SECRET_KEY=.*/SECRET_KEY=$SECRET_KEY/" "$ROOT_DIR/.env"
    echo "Generated SECRET_KEY saved in .env"
fi

# Build the standalone image used for production deployments
docker build --build-arg SECRET_KEY="$SECRET_KEY" -t whisper-app "$ROOT_DIR"

# Build images for the compose stack and start the services
docker compose -f "$ROOT_DIR/docker-compose.yml" build \
  --build-arg SECRET_KEY="$SECRET_KEY" api worker
docker compose -f "$ROOT_DIR/docker-compose.yml" up -d api worker broker db

echo "Images built and containers started. Run scripts/run_all_tests.sh separately to execute the test suite."

