#!/bin/bash
# AI Assistant Task Completion Wrapper
# This script should be called at the end of every development task

REPO_ROOT="/home/buymeagoat/dev/whisper-transcriber"
CLEANUP_SCRIPT="$REPO_ROOT/scripts/post_task_cleanup.sh"
VALIDATION_SCRIPT="$REPO_ROOT/scripts/validate_task_completion.sh"

echo "🤖 AI Assistant Task Completion"
echo "==============================="
echo ""

# Ensure we're in the repo
cd "$REPO_ROOT"

# Make scripts executable
chmod +x "$CLEANUP_SCRIPT"
chmod +x "$VALIDATION_SCRIPT"

# MANDATORY: Validate task completion requirements
echo "🔍 Running mandatory task completion validation..."
echo ""
if ! "$VALIDATION_SCRIPT"; then
    echo ""
    echo "❌ TASK COMPLETION VALIDATION FAILED"
    echo "   Cannot proceed with task completion until validation passes."
    echo "   Please address the issues above and try again."
    echo ""
    echo "Required actions:"
    echo "1. Update TASKS.md to mark completed task with ✅ **COMPLETED**"
    echo "2. Add or update comprehensive tests for the implemented functionality"
    echo "3. Run test suite and ensure all tests pass"
    echo "4. Document testing in change logs"
    echo ""
    echo "Then re-run: ./scripts/ai_task_complete.sh"
    exit 1
fi

echo ""
echo "✅ Task completion validation passed!"
echo ""

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
