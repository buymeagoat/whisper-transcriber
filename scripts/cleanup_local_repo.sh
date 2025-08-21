#!/bin/bash
# Cleanup script for local repository hygiene
# Removes files and directories not needed for builds or source control

set -e

# Remove Python cache and bytecode
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

# Remove log and temp files
find . -type f -name "*.log" -delete
find . -type f -name "*.tmp" -delete

# Remove Zone.Identifier files (Windows metadata)
find . -type f -name "*:Zone.Identifier" -delete

# Remove frontend build artifacts (unless needed for static hosting)
rm -rf frontend/dist/

# Remove uploads and transcripts (user data)
rm -rf uploads/
rm -rf transcripts/

# Remove local manifest if not needed for reproducibility
rm -f local_manifest.txt

# Remove snapshots if not needed for builds
rm -rf snapshots/

# Remove runtime logs and audit files
rm -rf logs/

echo "Local repository cleanup complete."
