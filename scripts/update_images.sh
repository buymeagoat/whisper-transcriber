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

# Return 0 if docker compose build supports --secret
supports_secret() {
    docker compose build --help 2>/dev/null | grep -q -- "--secret"
}

# Load SECRET_KEY from .env
ensure_env_file
echo "Checking network connectivity and installing dependencies..."
stage_build_dependencies

echo "Environment variables:" >&2
env | sort >&2

echo "Building frontend assets..."
(cd "$ROOT_DIR/frontend" && npm run build)

echo "Rebuilding API and worker images..."
# Rebuild API and worker images using Docker cache
if supports_secret; then
    secret_file=$(mktemp)
    printf '%s' "$SECRET_KEY" > "$secret_file"
    docker compose -f "$COMPOSE_FILE" build \
        --secret id=secret_key,src="$secret_file" \
        --build-arg INSTALL_DEV=true api worker
    rm -f "$secret_file"
else
    docker compose -f "$COMPOSE_FILE" build \
        --build-arg SECRET_KEY="$SECRET_KEY" \
        --build-arg INSTALL_DEV=true api worker
fi

echo "Verifying built images..."
verify_built_images

echo "Starting containers..."
docker compose -f "$COMPOSE_FILE" up -d api worker

cat <<'EOF'
API and worker images updated.
Available test scripts:
  scripts/run_tests.sh         - runs backend tests plus frontend unit and Cypress end-to-end tests.
  scripts/run_backend_tests.sh - executes only the backend tests and verifies the /health and /version endpoints.

Run the desired script to verify the update.
If containers encounter issues, use scripts/diagnose_containers.sh for troubleshooting.
EOF
