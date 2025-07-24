#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
COMPOSE_FILE="$ROOT_DIR/docker-compose.yml"
LOG_DIR="$ROOT_DIR/logs"
LOG_FILE="$LOG_DIR/full_test.log"

RUN_BACKEND=false
RUN_FRONTEND=false
RUN_CYPRESS=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --backend)
            RUN_BACKEND=true
            ;;
        --frontend)
            RUN_FRONTEND=true
            ;;
        --cypress)
            RUN_CYPRESS=true
            ;;
        -h|--help)
            echo "Usage: $0 [--backend] [--frontend] [--cypress]" >&2
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            exit 1
            ;;
    esac
    shift
done

# default to all when no options supplied
if ! $RUN_BACKEND && ! $RUN_FRONTEND && ! $RUN_CYPRESS; then
    RUN_BACKEND=true
    RUN_FRONTEND=true
    RUN_CYPRESS=true
fi

mkdir -p "$LOG_DIR"

# Echo a marker for major milestones
log_step() {
    echo "===== $1 ====="
}

# Ensure the API container is running before executing tests
if ! docker compose -f "$COMPOSE_FILE" ps api | grep -q "running"; then
    echo "API container is not running. Start the stack with scripts/start_containers.sh" >&2
    echo "Last API container logs:" >&2
    docker compose -f "$COMPOSE_FILE" logs api | tail -n 20 >&2 || true
    docker compose -f "$COMPOSE_FILE" ps >&2
    exit 1
fi

{
    if $RUN_BACKEND; then
        log_step "BACKEND TESTS"
        "$SCRIPT_DIR/run_backend_tests.sh"
    fi
    if $RUN_FRONTEND; then
        log_step "FRONTEND UNIT"
        npm test --prefix "$ROOT_DIR/frontend"
    fi
    if $RUN_CYPRESS; then
        log_step "E2E TESTS"
        npm run e2e --prefix "$ROOT_DIR/frontend"
    fi
} | tee "$LOG_FILE"

echo "Full test log saved to $LOG_FILE"
