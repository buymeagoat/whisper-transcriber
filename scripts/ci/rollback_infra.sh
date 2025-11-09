#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(git rev-parse --show-toplevel)"
TF_DIR="$ROOT_DIR/deploy/terraform"
ANSIBLE_DIR="$ROOT_DIR/deploy/ansible"
TF_VARS_FILE="${TF_VARS_FILE:-$TF_DIR/environments/ci.tfvars}"
PLAN_ONLY=false
ROLLBACK_TARGET="${ROLLBACK_TARGET:-ci-rollback}"
ROLLBACK_PREVIOUS="${ROLLBACK_PREVIOUS:-ci-previous}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --var-file)
      shift
      TF_VARS_FILE="$1"
      ;;
    --plan-only)
      PLAN_ONLY=true
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 1
      ;;
  esac
  shift
done

export AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID:-test}"
export AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY:-test}"
export AWS_SESSION_TOKEN="${AWS_SESSION_TOKEN:-test-token}"
export AWS_DEFAULT_REGION="${AWS_DEFAULT_REGION:-us-east-1}"

pushd "$TF_DIR" >/dev/null
terraform init -backend=false -input=false
terraform plan \
  -lock=false \
  -input=false \
  -refresh=false \
  -var-file="$TF_VARS_FILE" \
  -var "release_image_tag=${ROLLBACK_TARGET}" \
  -var "rollback_image_tag=${ROLLBACK_PREVIOUS}" \
  -out="$TF_DIR/.rollback-plan"
popd >/dev/null

if [[ "$PLAN_ONLY" == "false" ]]; then
  echo "Skipping actual apply; rollback automation is validated through plan output." >&2
fi

pushd "$ANSIBLE_DIR" >/dev/null
ansible-playbook site.yml --tags rollback --check -e "deploy_env=ci"
popd >/dev/null
