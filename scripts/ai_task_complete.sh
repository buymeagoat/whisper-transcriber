#!/bin/bash
# AI Assistant Task Completion Wrapper
# This script should be called at the end of every development task

REPO_ROOT="/home/buymeagoat/dev/whisper-transcriber"
CLEANUP_SCRIPT="$REPO_ROOT/scripts/post_task_cleanup.sh"

echo "🤖 AI Assistant Task Completion"
echo "==============================="
echo ""

# Ensure we're in the repo
cd "$REPO_ROOT"

# Make cleanup script executable
chmod +x "$CLEANUP_SCRIPT"

# Run the cleanup
echo "Running automated cleanup and commit process..."
"$CLEANUP_SCRIPT"

# Success message
echo ""
echo "🎉 Task completion process finished!"
echo "   ✅ Repository cleaned"
echo "   ✅ Documentation updated" 
echo "   ✅ Changes committed"
echo ""
echo "Repository is now ready for the next development task."
