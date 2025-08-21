#!/usr/bin/env bash
set -euo pipefail

# Determine the cache directory used by the build scripts.
if [ -n "${CACHE_DIR:-}" ]; then
    base="$CACHE_DIR"
elif grep -qi microsoft /proc/version && [ -d /mnt/c ]; then
    base="/mnt/c/whisper_cache"
else
    base="/tmp/docker_cache"
fi
echo "Using cache directory: $base"

mkdir -p "$base/images"

echo "1. Checking host write access..."
if touch "$base/testfile" && rm "$base/testfile"; then
    echo "Host can write to $base"
else
    echo "Host cannot write to $base"
    exit 1
fi

echo "2. Checking Docker container access..."
if docker run --rm -v "$base:/cache" busybox sh -c 'touch /cache/testfile && rm /cache/testfile'; then
    echo "Docker container can write to $base"
else
    echo "Docker container cannot write to $base"
fi

echo "3. Checking docker save..."
if docker save busybox:latest -o "$base/images/test.tar"; then
    echo "docker save succeeded"
    rm -f "$base/images/test.tar"
else
    echo "docker save failed"
fi
