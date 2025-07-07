#!/usr/bin/env bash
set -e
mkdir -p /app/uploads /app/transcripts /app/logs
chown -R 1000:1000 /app/uploads /app/transcripts /app/logs

# If this container is running a worker, wait for the broker to be ready
if [ "${SERVICE_TYPE:-api}" = "worker" ]; then
    broker_host="${CELERY_BROKER_HOST:-broker}"
    echo "Waiting for RabbitMQ at ${broker_host}..."
    while ! rabbitmq-diagnostics -q ping -n "rabbit@${broker_host}" >/dev/null 2>&1; do
        sleep 1
    done
    echo "Broker is available. Starting worker."
fi
exec gosu appuser "$@"
