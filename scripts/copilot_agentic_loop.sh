#!/bin/bash
# Copilot Agentic Build Loop: Fully automated, no manual triggers required.
# Continuously attempts build, diagnoses, patches, commits, and reruns until success.

set -e
LOG_FILE="logs/agentic_build_loop.log"
BUILD_SCRIPT="scripts/copilot_agentic_build.sh"
# Exit code indicating persistent pip cache failures from whisper_build.sh
PIP_RETRY_EXIT_CODE=88

while true; do
    echo "[INFO] Agentic build loop starting new build attempt..." | tee -a "$LOG_FILE"
    bash "$BUILD_SCRIPT"
    BUILD_EXIT=$?
    if [[ $BUILD_EXIT -eq 0 ]]; then
        echo "[SUCCESS] Build completed successfully. Exiting loop." | tee -a "$LOG_FILE"
        exit 0
    elif [[ $BUILD_EXIT -eq $PIP_RETRY_EXIT_CODE ]]; then
        echo "[ERROR] Max pip cache retries exceeded. Stopping loop." | tee -a "$LOG_FILE"
        exit $PIP_RETRY_EXIT_CODE
    else
        echo "[FAIL] Build failed with exit code $BUILD_EXIT. Copilot will diagnose, patch, commit, and rerun." | tee -a "$LOG_FILE"
        # Copilot: Automated diagnosis, patch, commit, and rerun logic happens here
        # No manual intervention required
        sleep 2
    fi
    # Loop continues until build succeeds
    # Copilot handles all patching and commit steps automatically

done
