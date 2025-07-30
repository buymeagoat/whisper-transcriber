#!/bin/bash
#
# setup_runtime_dirs.sh
#
# Purpose:
#   Creates and anchors essential runtime directories in the Git repository using .gitkeep files.
#   Updates .gitignore to exclude dynamic contents but preserve the directory structure in version control.
#
# Directories Handled:
#   - cache/
#   - logs/
#   - models/
#   - transcripts/
#   - uploads/
#
# What This Script Does:
#   - Recreates these directories if missing (e.g., after rebase or fresh clone)
#   - Inserts .gitkeep placeholders into each
#   - Forces Git to track .gitkeep files, bypassing .gitignore rules if needed
#   - Appends rules to .gitignore to ignore all contents except .gitkeep in each directory
#
# Outcome:
#   Ensures Codex Analyst GPT (CPG) and project contributors always have a complete structural baseline
#   without committing volatile files or large outputs.
#
# Usage:
#   Run from any directory:
#       bash scripts/setup_runtime_dirs.sh
#
# Maintainer:
#   Codex Process Governance


# Absolute project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT" || exit 1

# Directories to ensure exist and are git-tracked via .gitkeep
DIRS=(cache logs models transcripts uploads)

echo "Ensuring runtime directories exist and are git-tracked with .gitkeep..."

for dir in "${DIRS[@]}"; do
    DIR_PATH="$PROJECT_ROOT/$dir"
    
    # Fix permission issues proactively
    if [ -d "$DIR_PATH" ] && [ ! -w "$DIR_PATH" ]; then
        echo "Fixing permissions on $DIR_PATH..."
        sudo chown -R "$USER:$USER" "$DIR_PATH"
    fi

    mkdir -p "$DIR_PATH"
    touch "$DIR_PATH/.gitkeep"
    git add -f "$dir/.gitkeep"
done

# Patch .gitignore if needed
GITIGNORE="$PROJECT_ROOT/.gitignore"
for dir in "${DIRS[@]}"; do
    if ! grep -Fxq "$dir/*" "$GITIGNORE"; then
        echo "$dir/*" >> "$GITIGNORE"
        echo "!$dir/.gitkeep" >> "$GITIGNORE"
    fi
done

git add .gitignore

echo ""
echo "✅ All runtime directories ensured."
echo "📝 .gitignore updated to include folder skeleton rules."
echo "📦 Run the following to commit and push:"
echo ""
echo "    git commit -m 'Preserve runtime directories with .gitkeep anchors'"
echo "    git push origin main"
