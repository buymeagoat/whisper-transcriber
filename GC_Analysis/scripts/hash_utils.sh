#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Print SHA-256 hash of the concatenated contents of the CAG specification and AGENTS.md
cag_agents_hash() {
    local spec_file="$ROOT_DIR/docs/CAG_spec.md"
    local agents_file="$ROOT_DIR/AGENTS.md"

    if [[ ! -f "$spec_file" ]]; then
        echo "CAG specification file not found: $spec_file" >&2
        return 1
    fi
    if [[ ! -f "$agents_file" ]]; then
        echo "AGENTS.md file not found: $agents_file" >&2
        return 1
    fi

    cat "$spec_file" "$agents_file" | sha256sum | awk '{print $1}'
}

# If the script is executed directly, run the function
if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
    cag_agents_hash
fi
