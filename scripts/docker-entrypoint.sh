#!/usr/bin/env bash
set -euo pipefail

LOG_FILE="/app/logs/entrypoint.log"
mkdir -p /app/uploads /app/transcripts /app/logs
# Mirror output to a log file for troubleshooting
exec > >(tee -a "$LOG_FILE") 2>&1
chown -R 1000:1000 /app/uploads /app/transcripts /app/logs

echo "Container entrypoint starting with environment:" >&2
env | sort >&2

# If this container is running a worker, wait for the broker to be ready
if [ "${SERVICE_TYPE:-api}" = "worker" ]; then
    if [ ! -f /app/worker.py ]; then
        echo "ERROR: /app/worker.py not found" >&2
        exit 1
    fi
    broker_host="${CELERY_BROKER_HOST:-broker}"
    broker_port="${CELERY_BROKER_PORT:-5672}"
    max_wait=${BROKER_PING_TIMEOUT:-60}
    echo "Waiting for RabbitMQ at ${broker_host}:${broker_port}..."
    BROKER_HOST="$broker_host" BROKER_PORT="$broker_port" TIMEOUT="$max_wait" \
    python - <<'PY'
import os, socket, sys, time

host = os.environ["BROKER_HOST"]
port = int(os.environ["BROKER_PORT"])
timeout = int(os.environ["TIMEOUT"])
start = time.time()
while True:
    try:
        with socket.create_connection((host, port), timeout=1):
            break
    except OSError:
        print("waiting...", flush=True)
        if time.time() - start >= timeout:
            print(f"Broker unreachable after {timeout}s", file=sys.stderr)
            sys.exit(1)
        time.sleep(1)
print("Broker is available. Starting worker.")
PY
fi
echo "Executing: $@" >&2
exec gosu appuser "$@"
