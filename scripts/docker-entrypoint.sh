#!/usr/bin/env bash
set -e
mkdir -p /app/uploads /app/transcripts /app/logs
chown -R 1000:1000 /app/uploads /app/transcripts /app/logs
exec gosu appuser "$@"
