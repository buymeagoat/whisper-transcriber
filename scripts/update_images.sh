#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
COMPOSE_FILE="$ROOT_DIR/docker-compose.yml"
source "$SCRIPT_DIR/shared_checks.sh"

# Return 0 if docker compose build supports --secret
supports_secret() {
    docker compose build --help 2>/dev/null | grep -q -- "--secret"
}

# Load SECRET_KEY from .env
ensure_env_file

# Rebuild frontend assets

(cd "$ROOT_DIR/frontend" && npm run build)

# Rebuild API and worker images using Docker cache
if supports_secret; then
    secret_file=$(mktemp)
    printf '%s' "$SECRET_KEY" > "$secret_file"
    docker compose -f "$COMPOSE_FILE" build \
        --secret id=secret_key,src="$secret_file" api worker
    rm -f "$secret_file"
else
    docker compose -f "$COMPOSE_FILE" build \
        --build-arg SECRET_KEY="$SECRET_KEY" api worker
fi

docker compose -f "$COMPOSE_FILE" up -d api worker
