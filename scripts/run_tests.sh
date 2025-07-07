#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
COMPOSE_FILE="$ROOT_DIR/docker-compose.yml"

# Ensure docker compose services are stopped on exit
trap 'docker compose -f "$COMPOSE_FILE" down' EXIT

# Install Python dependencies
pip install -r "$ROOT_DIR/requirements.txt"

# Install development dependencies for running tests
pip install -r "$ROOT_DIR/requirements-dev.txt"

# Install Node dependencies for the frontend
(cd "$ROOT_DIR/frontend" && npm install)

# Build images and start containers
"$SCRIPT_DIR/update_images.sh"

# Run the Python test suite
pytest
