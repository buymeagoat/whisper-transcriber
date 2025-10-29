#!/usr/bin/env bash
# Security: Enable strict error handling and security options
set -euo pipefail
IFS=$'\n\t'

# Security: Define secure logging and directory creation
LOG_FILE="/app/logs/entrypoint.log"

# Security: Create required directories with proper permissions (non-root safe)
mkdir -p /app/storage/uploads /app/storage/transcripts /app/logs /app/data

# Security: Only set ownership if running as root (for initialization)
if [ "$(id -u)" -eq 0 ]; then
    echo "WARNING: Running as root - this should only happen during initialization"
    chown -R appuser:appuser /app/storage /app/logs /app/data
    # Security: Drop privileges using gosu
    exec gosu appuser "$0" "$@"
fi

# Security: Verify we're running as the correct user
if [ "$(id -u)" -ne 1000 ] || [ "$(id -g)" -ne 1000 ]; then
    echo "ERROR: Container must run as user appuser (uid=1000, gid=1000)" >&2
    echo "Current: uid=$(id -u), gid=$(id -g), user=$(whoami)" >&2
    exit 1
fi

# Security: Set up secure logging with log rotation consideration
exec > >(tee -a "$LOG_FILE") 2>&1

# Logging function for security audit trail
log_step() {
    echo "$(date -u +"%Y-%m-%d %H:%M:%S UTC") [ENTRYPOINT] $1"
}

log_step "ENVIRONMENT"
echo "Container entrypoint starting with environment:" >&2
env | sort >&2

# If this container is running a worker, wait for the broker to be ready
if [ "${SERVICE_TYPE:-api}" = "worker" ]; then
    if [ ! -f /app/api/worker.py ]; then
        echo "ERROR: /app/api/worker.py not found" >&2
        exit 1
    fi
    broker_host="${CELERY_BROKER_HOST:-broker}"
    broker_port="${CELERY_BROKER_PORT:-5672}"
    max_wait=${BROKER_PING_TIMEOUT:-60}
    log_step "WAIT FOR BROKER"
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
log_step "START"
echo "Executing: $@" >&2
# If we're already running as appuser (from Docker user setting), execute directly
if [ "$(id -u)" -eq 1000 ]; then
    exec "$@"
else
    exec gosu appuser "$@"
fi
