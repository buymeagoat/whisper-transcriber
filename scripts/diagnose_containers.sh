#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
COMPOSE_FILE="$ROOT_DIR/docker-compose.yml"

echo "Container status:" 
# Display container status including health information
docker compose -f "$COMPOSE_FILE" ps

# Get list of services defined in the compose file
services=$(docker compose -f "$COMPOSE_FILE" config --services)

for svc in $services; do
    echo
    echo "===== Last 20 log lines for $svc ====="
    docker compose -f "$COMPOSE_FILE" logs --tail 20 "$svc" || true
done
