#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(git rev-parse --show-toplevel)"
TF_DIR="$ROOT_DIR/deploy/terraform"
ANSIBLE_DIR="$ROOT_DIR/deploy/ansible"
TF_VARS_FILE="${TF_VARS_FILE:-$TF_DIR/environments/ci.tfvars}"

export AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID:-test}"
export AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY:-test}"
export AWS_SESSION_TOKEN="${AWS_SESSION_TOKEN:-test-token}"
export AWS_DEFAULT_REGION="${AWS_DEFAULT_REGION:-us-east-1}"

pushd "$TF_DIR" >/dev/null
terraform init -backend=false -input=false
terraform fmt -check
terraform validate
terraform plan \
  -lock=false \
  -input=false \
  -refresh=false \
  -var-file="$TF_VARS_FILE" \
  -out="$TF_DIR/.terraform-plan"
popd >/dev/null

pushd "$ANSIBLE_DIR" >/dev/null
ansible-playbook site.yml --tags plan,deploy --check -e "deploy_env=ci"
popd >/dev/null
