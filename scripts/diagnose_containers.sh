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
        status=$(docker inspect --format '{{ .State.Status }}' "$container_id" || echo "unknown")
        health=$(docker inspect --format '{{ if .State.Health }}{{ .State.Health.Status }}{{ else }}none{{ end }}' "$container_id" || echo "none")
        exit_code=$(docker inspect --format '{{ .State.ExitCode }}' "$container_id" || echo "unknown")
        restarts=$(docker inspect --format '{{ .RestartCount }}' "$container_id" || echo "unknown")
        echo "Status: $status (Health: $health)  Exit Code: $exit_code  Restarts: $restarts"
        echo "Environment variables:"
        docker inspect --format '{{range .Config.Env}}{{println .}}{{end}}' "$container_id" | grep -E '^(SERVICE_TYPE|CELERY_BROKER_URL)=' || true
    else
        status="not_created"
        echo "Container not running"
    fi
    echo "===== Last ${LOG_LINES} log lines for $svc ====="
    docker compose -f "$COMPOSE_FILE" logs --tail "$LOG_LINES" "$svc" || true

    if [ "$svc" = "worker" ] && [ "$status" != "running" ]; then
        echo "Checking worker image for /app/worker.py..."
        if docker compose -f "$COMPOSE_FILE" run --rm --no-deps --entrypoint "" worker test -f /app/worker.py >/dev/null; then
            echo "worker.py present in worker image"
        else
            echo "worker.py missing in worker image"
        fi
    fi
done

api_id=$(docker compose -f "$COMPOSE_FILE" ps -q api 2>/dev/null || true)
if [ -z "$api_id" ]; then
    echo
    echo "API container is not running. Checking dependencies..."
    for dep in worker broker db; do
        dep_id=$(docker compose -f "$COMPOSE_FILE" ps -q "$dep" 2>/dev/null || true)
        if [ -n "$dep_id" ]; then
            dep_status=$(docker inspect --format '{{ .State.Status }} (Health: {{ if .State.Health }}{{ .State.Health.Status }}{{ else }}none{{ end }})' "$dep_id" 2>/dev/null || echo "unknown")
            echo "Dependency $dep: $dep_status"
        else
            echo "Dependency $dep: container not running"
        fi
    done
fi

echo
echo "===== Build logs ====="
for log in docker_build.log start_containers.log update_images.log entrypoint.log; do
    log_path="$ROOT_DIR/logs/$log"
    echo
    echo "----- ${log} -----"
    if [ -f "$log_path" ]; then
        cat "$log_path"
    else
        echo "Log file $log_path not found"
    fi
done
