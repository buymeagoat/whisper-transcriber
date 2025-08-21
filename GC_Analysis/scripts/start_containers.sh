#!/usr/bin/env bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
echo "start_containers.sh is deprecated. Use whisper_build.sh instead." >&2
exec "$SCRIPT_DIR/whisper_build.sh" "$@"
