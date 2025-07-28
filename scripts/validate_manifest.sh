#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
MANIFEST="$ROOT_DIR/cache/manifest.txt"
DOCKERFILE="$ROOT_DIR/Dockerfile"

MODE="summary"
while [[ $# -gt 0 ]]; do
    case "$1" in
        --json)
            MODE="json"
            shift
            ;;
        --summary)
            MODE="summary"
            shift
            ;;
        -h|--help)
            echo "Usage: $(basename "$0") [--json|--summary]" >&2
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            exit 1
            ;;
    esac
done

source "$SCRIPT_DIR/shared_checks.sh"

if [ ! -f "$MANIFEST" ]; then
    echo "Manifest $MANIFEST missing" >&2
    exit 1
fi

validate_manifest_schema "$MANIFEST" || echo "Warning: manifest missing expected fields" >&2

BASE_IMAGE=$(grep -m1 '^FROM ' "$DOCKERFILE" | awk '{print $2}')
manifest_codename=$(grep '^BASE_CODENAME=' "$MANIFEST" | cut -d= -f2-)
manifest_digest=$(grep '^BASE_DIGEST=' "$MANIFEST" | cut -d= -f2-)
timestamp=$(grep '^TIMESTAMP=' "$MANIFEST" | cut -d= -f2-)
manifest_pip_lock=$(grep '^pip_versions=' "$MANIFEST" | cut -d= -f2-)
manifest_npm_lock=$(grep '^npm_versions=' "$MANIFEST" | cut -d= -f2-)

image_digest=""
image_codename=""
if docker image inspect "$BASE_IMAGE" >/dev/null 2>&1; then
    image_digest=$(docker image inspect "$BASE_IMAGE" --format '{{index .RepoDigests 0}}' | awk -F@ '{print $2}')
    image_codename=$(docker run --rm "$BASE_IMAGE" bash -c 'source /etc/os-release && echo $VERSION_CODENAME')
fi

pip_hash=""
npm_hash=""
if [ -f "$ROOT_DIR/cache/pip/pip_versions.txt" ]; then
    pip_hash=$(sha256sum "$ROOT_DIR/cache/pip/pip_versions.txt" | awk '{print $1}')
fi
if [ -f "$ROOT_DIR/cache/npm/npm_versions.txt" ]; then
    npm_hash=$(sha256sum "$ROOT_DIR/cache/npm/npm_versions.txt" | awk '{print $1}')
fi

deltas=()
[ -n "$image_digest" ] && [ "$manifest_digest" != "$image_digest" ] && deltas+=("digest mismatch")
[ -n "$image_codename" ] && [ "$manifest_codename" != "$image_codename" ] && deltas+=("codename mismatch")
[ -n "$pip_hash" ] && [ "$manifest_pip_lock" != "$pip_hash" ] && deltas+=("pip_versions mismatch")
[ -n "$npm_hash" ] && [ "$manifest_npm_lock" != "$npm_hash" ] && deltas+=("npm_versions mismatch")

status="pass"
if [ ${#deltas[@]} -gt 0 ]; then
    status="fail"
fi

if [ "$MODE" = "json" ]; then
    printf '{"base_image":"%s","manifest_codename":"%s","image_codename":"%s","manifest_digest":"%s","image_digest":"%s","status":"%s","deltas":[' "$BASE_IMAGE" "$manifest_codename" "$image_codename" "$manifest_digest" "$image_digest" "$status"
    for i in "${!deltas[@]}"; do
        printf '"%s"' "${deltas[$i]}"
        if [ "$i" -lt $((${#deltas[@]}-1)) ]; then
            printf ','
        fi
    done
    printf ']}\n'
else
    echo "Base image: $BASE_IMAGE"
    echo "Manifest codename: $manifest_codename"
    echo "Docker image codename: $image_codename"
    echo "Manifest digest: $manifest_digest"
    echo "Image digest: $image_digest"
    echo "Timestamp: $timestamp"
    if [ ${#deltas[@]} -eq 0 ]; then
        echo "STATUS: PASS"
    else
        echo "STATUS: FAIL"
        for d in "${deltas[@]}"; do
            echo "- $d"
        done
    fi
fi
