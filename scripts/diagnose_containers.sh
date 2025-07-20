#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
COMPOSE_FILE="$ROOT_DIR/docker-compose.yml"
LOG_LINES="${LOG_LINES:-20}"

echo "Container status:" 
# Display container status including health information
docker compose -f "$COMPOSE_FILE" ps

# Get list of services defined in the compose file
services=$(docker compose -f "$COMPOSE_FILE" config --services)

for svc in $services; do
    echo
    echo "===== Inspecting $svc ====="
    container_id=$(docker compose -f "$COMPOSE_FILE" ps -q "$svc" 2>/dev/null || true)
    if [ -n "$container_id" ]; then
        docker inspect --format 'Status: {{ .State.Status }} (Health: {{ if .State.Health }}{{ .State.Health.Status }}{{ else }}none{{ end }})  Exit Code: {{ .State.ExitCode }}  Restarts: {{ .RestartCount }}' "$container_id" || true
        echo "Environment variables:"
        docker inspect --format '{{range .Config.Env}}{{println .}}{{end}}' "$container_id" | grep -E '^(SERVICE_TYPE|CELERY_BROKER_URL)=' || true
    else
        echo "Container not running"
    fi
    echo "===== Last ${LOG_LINES} log lines for $svc ====="
    docker compose -f "$COMPOSE_FILE" logs --tail "$LOG_LINES" "$svc" || true
done
