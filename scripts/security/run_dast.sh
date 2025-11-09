#!/usr/bin/env bash

# Run an OWASP ZAP baseline scan against a running Whisper Transcriber instance.
# Usage: scripts/security/run_dast.sh [target-url] [zap-args...]

set -euo pipefail

TARGET_URL=${1:-"http://localhost:8000"}
shift || true

EXTRA_ARGS=("$@")
REPORT_ROOT=${REPORT_DIR:-"reports/security"}
TIMESTAMP=$(date +"%Y%m%d%H%M%S")
REPORT_PREFIX="zap-${TIMESTAMP}"

mkdir -p "${REPORT_ROOT}"

if ! command -v docker >/dev/null 2>&1; then
  echo "[DAST] docker is required to run OWASP ZAP" >&2
  exit 1
fi

ZAP_IMAGE=${ZAP_DOCKER_IMAGE:-"owasp/zap2docker-stable"}
REPORT_MOUNT=$(cd "${REPORT_ROOT}" && pwd)

echo "[DAST] Starting OWASP ZAP baseline scan against ${TARGET_URL}" >&2

docker run \
  --rm \
  --network host \
  -u "$(id -u):$(id -g)" \
  -v "${REPORT_MOUNT}:/zap/wrk" \
  "${ZAP_IMAGE}" \
  zap-baseline.py \
  -t "${TARGET_URL}" \
  -x "${REPORT_PREFIX}.xml" \
  -J "${REPORT_PREFIX}.json" \
  -w "${REPORT_PREFIX}.md" \
  "${EXTRA_ARGS[@]}"

RESULT=$?

if [[ ${RESULT} -ne 0 ]];
then
  echo "[DAST] OWASP ZAP reported findings. Review ${REPORT_ROOT}/${REPORT_PREFIX}.md" >&2
else
  echo "[DAST] Scan completed successfully. Reports in ${REPORT_ROOT}/${REPORT_PREFIX}.*" >&2
fi

exit ${RESULT}
