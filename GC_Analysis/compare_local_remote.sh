#!/bin/bash
# compare_local_remote_pruned.sh
# Prune local files that are expected (venv, .git, .env, cache, etc.)

# List of patterns to exclude
EXCLUDES=(
  "./venv"
  "./.git"
  "./.env"
  "./.env.example"
  "./__pycache__"
  "./cache"
  "./uploads"
  "./transcripts"
  "./snapshots"
  "./node_modules"
  "./frontend/node_modules"
  "./.DS_Store"
  "./*.pyc"
)

# Build the exclude arguments for grep
EXCLUDE_ARGS=""
for pattern in "${EXCLUDES[@]}"; do
  EXCLUDE_ARGS+=" -e \"$pattern\""
done

# Get local files, prune excludes
find . -type f | grep -vE "$(IFS='|'; echo "${EXCLUDES[*]}")" | sort > local_files_pruned.txt

# Get remote files from git
git ls-files | sort > remote_files.txt

# Compare and output files present locally but not in remote
comm -23 local_files_pruned.txt remote_files.txt > local_vs_remote_diff_pruned.txt

echo "Pruned diff written to local_vs_remote_diff_pruned.txt"