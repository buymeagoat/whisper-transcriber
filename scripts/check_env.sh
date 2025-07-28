#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
APT_CACHE="$ROOT_DIR/cache/apt"

# Verify DNS resolution for package mirrors
if ! getent hosts archive.ubuntu.com >/dev/null 2>&1; then
    echo "DNS resolution failed for archive.ubuntu.com" >&2
    exit 1
fi

# Determine base image from Dockerfile
BASE_IMAGE=$(grep -m1 '^FROM ' "$ROOT_DIR/Dockerfile" | awk '{print $2}')

# Extract VERSION_CODENAME from the base image
if command -v docker >/dev/null 2>&1; then
    BASE_CODENAME=$(docker run --rm "$BASE_IMAGE" bash -c 'source /etc/os-release && echo $VERSION_CODENAME')
else
    BASE_CODENAME="${BASE_IMAGE##*-}"
fi

if [ -z "$BASE_CODENAME" ]; then
    echo "Failed to determine VERSION_CODENAME from base image" >&2
    exit 1
fi

HOST_ARCH="$(dpkg --print-architecture)"

# Ensure cached APT packages correspond to the codename
if [ ! -d "$APT_CACHE" ]; then
    echo "APT cache directory $APT_CACHE missing" >&2
    exit 1
fi

if [ ! -f "$APT_CACHE/deb_list.txt" ]; then
    echo "Package list $APT_CACHE/deb_list.txt missing" >&2
    exit 1
fi

mismatch=0
while read -r deb; do
    [ -z "$deb" ] && continue
    if [[ "$deb" != *"$BASE_CODENAME"* ]]; then
        echo "Package $deb does not match codename $BASE_CODENAME" >&2
        mismatch=1
    fi
    pkg_arch=$(dpkg-deb -f "$APT_CACHE/$deb" Architecture)
    if [ "$pkg_arch" != "$HOST_ARCH" ]; then
        echo "Package $deb architecture $pkg_arch does not match host $HOST_ARCH" >&2
        mismatch=1
    fi
    if [ ! -f "$APT_CACHE/$deb" ]; then
        echo "Missing file $APT_CACHE/$deb" >&2
        mismatch=1
    fi
done < "$APT_CACHE/deb_list.txt"

if [ $mismatch -ne 0 ]; then
    echo "Cached packages do not align with $BASE_CODENAME or $HOST_ARCH" >&2
    exit 1
fi

# Check that the cached base image digest matches the current one
if command -v docker >/dev/null 2>&1; then
    docker pull --quiet "$BASE_IMAGE" >/dev/null
    current_digest=$(docker image inspect "$BASE_IMAGE" --format '{{index .RepoDigests 0}}' | awk -F@ '{print $2}')
    manifest="$ROOT_DIR/cache/manifest.txt"
    if [ ! -f "$manifest" ]; then
        echo "Manifest $manifest missing" >&2
        exit 1
    fi
    stored_digest=$(grep '^BASE_DIGEST=' "$manifest" | cut -d= -f2-)
    if [ -z "$stored_digest" ]; then
        echo "BASE_DIGEST not found in $manifest" >&2
        exit 1
    fi
    if [ "$stored_digest" != "$current_digest" ]; then
        echo "Base image digest mismatch: cached $stored_digest vs $current_digest" >&2
        if [ "${ALLOW_DIGEST_MISMATCH:-0}" != "1" ]; then
            exit 1
        else
            echo "ALLOW_DIGEST_MISMATCH=1 set - continuing despite mismatch" >&2
        fi
    fi
fi

printf 'Environment OK for codename %s\n' "$BASE_CODENAME"
