# Deployment Manifests

This directory centralises the infrastructure-as-code definitions that support the Whisper Transcriber platform.

> **Dormant status:** Container-first deployment artefacts remain for future ECS/ECR work but are disabled by default in favour
> of host-based installs. Set `CONTAINER_BUILDS_ENABLED=1` when reviving the Docker rollout.

- [`terraform/`](./terraform/) provisions the core AWS infrastructure (networking, storage, compute, container registry, and database services).
- [`ansible/`](./ansible/) configures the application stack on top of the provisioned compute capacity and orchestrates roll-forward/roll-back deploys.

## Getting Started

1. Copy [`terraform/terraform.tfvars.example`](./terraform/terraform.tfvars.example) to `terraform/environments/<env>.tfvars` and customise the values for your account.
2. Run the Terraform plan pipeline locally (see [`scripts/ci/run_infra_checks.sh`](../scripts/ci/run_infra_checks.sh)) to validate the manifests.
3. Apply the Terraform plan when you are ready to create/update infrastructure.
4. Use the Ansible playbook in [`ansible/site.yml`](./ansible/site.yml) to render host configuration or execute a rollback using
   the tags described below. The Docker Compose bundle generation is archived and only executes when
   `CONTAINER_BUILDS_ENABLED=1`; systemd unit templates are the primary deployment vehicle.

## Terraform Parameters

| Variable | Description | Example |
| --- | --- | --- |
| `project` | Human readable project name used for tagging and naming resources. | `whisper-transcriber` |
| `environment` | Short identifier for the deployment environment. | `dev`, `staging`, `prod` |
| `aws_region` | AWS region hosting the stack. | `us-east-1` |
| `uploads_bucket_name` | Optional override for the upload S3 bucket name. Leave `null` to generate automatically. | `whisper-transcriber-prod-uploads` |
| `force_destroy_uploads` | Allow Terraform to delete non-empty S3 buckets (useful in dev/test). | `false` |
| `vpc_cidr` | CIDR for the VPC. | `10.40.0.0/16` |
| `public_subnet_cidrs` | CIDR blocks for public subnets used by ECS services. | `["10.40.10.0/24", "10.40.11.0/24"]` |
| `availability_zones` | AZs mapped to the subnets. | `["us-east-1a", "us-east-1b"]` |
| `allowed_cidr_blocks` | CIDR ranges allowed through the service security group. | `["0.0.0.0/0"]` |
| `db_username` | Database administrator username. | `transcriber` |
| `db_password` | Database administrator password. | `change-me` |
| `db_name` | Primary application database name. | `whisper_transcriber_dev` |
| `db_engine_version` | Aurora PostgreSQL engine version. | `15.4` |
| `db_instance_class` | Aurora instance class. | `db.serverless` |
| `db_backup_retention_days` | Automated backup retention period. | `7` |
| `task_cpu` | CPU units assigned to the ECS task (1024 = 1 vCPU). | `1024` |
| `task_memory` | Memory assigned to the ECS task in MiB. | `2048` |
| `desired_task_count` | Desired number of ECS service tasks. | `2` |
| `ecs_execution_role_arn` | IAM role used by ECS to pull images and emit logs. | `arn:aws:iam::123456789012:role/whisper-execution` |
| `ecs_task_role_arn` | IAM role granted to the running task. | `arn:aws:iam::123456789012:role/whisper-task` |
| `release_image_tag` | Container tag promoted during a deploy. | `main-2025-11-08` |
| `rollback_image_tag` | Container tag used when rolling back. | `main-2025-11-01` |
| `secret_key_parameter_arn` | ARN for the runtime `SECRET_KEY` secret (SSM or Secrets Manager). | `arn:aws:ssm:...:parameter/whisper/prod/SECRET_KEY` |
| `jwt_secret_key_parameter_arn` | ARN for the runtime `JWT_SECRET_KEY` secret. | `arn:aws:ssm:...:parameter/whisper/prod/JWT_SECRET_KEY` |
| `admin_bootstrap_password_parameter_arn` | ARN for the runtime `ADMIN_BOOTSTRAP_PASSWORD` secret. | `arn:aws:ssm:...:parameter/whisper/prod/ADMIN_BOOTSTRAP_PASSWORD` |
| `redis_url_parameter_arn` | ARN for the runtime `REDIS_URL` secret. | `arn:aws:ssm:...:parameter/whisper/prod/REDIS_URL` |
| `redis_password_parameter_arn` | ARN for the runtime `REDIS_PASSWORD` secret. | `arn:aws:ssm:...:parameter/whisper/prod/REDIS_PASSWORD` |
| `metrics_token_parameter_arn` | ARN for the runtime `METRICS_TOKEN` secret used by Prometheus scrapers. | `arn:aws:ssm:...:parameter/whisper/prod/METRICS_TOKEN` |
| `worker_desired_count` | Number of Celery worker tasks provisioned alongside the API. | `2` |
| `worker_task_cpu` | CPU units allocated to each Celery worker task. | `1024` |
| `worker_task_memory` | Memory allocated to each Celery worker task in MiB. | `2048` |

## Ansible Parameters

All Ansible defaults live in [`ansible/group_vars/all.yml`](./ansible/group_vars/all.yml). Override them per environment using inventory variables or the `-e` flag.

| Variable | Description |
| --- | --- |
| `deploy_env` | Environment identifier aligned with Terraform. |
| `project` | Name used for directory layout and Compose project. |
| `deployment_root` | Path on the target host where deployment artefacts are stored. |
| `deploy_user` / `deploy_group` | Owner of generated files. |
| `compose_project_name` | Legacy identifier used while the Compose bundle is replaced. |
| `container_image` | Legacy image reference used until host-based deployment tasks land. |
| `desired_release_tag` | Target release identifier (currently mirrors legacy image tags). |
| `rollback_release_tag` | Rollback identifier (mirrors legacy image tags). |
| `db_*` variables | Connection metadata required by the service. |
| `uploads_bucket` | Bucket where the API stores incoming audio. |
| `redis_password` | Password injected into Redis connection strings. |
| `secret_key` / `jwt_secret_key` | Application signing keys rendered into the `.env` file. |
| `admin_bootstrap_password` | Bootstrap password used for the initial administrator. |
| `metrics_token` | Shared secret distributed to trusted Prometheus scrapers. |

The Terraform service definition now provisions an API service **and** a Celery worker service so that queued transcription jobs
are processed automatically. Host-based installs should likewise ensure the worker unit is enabled and reading the same `.env`
file as the API.

### Playbook Tags

- `deploy`: Render updated configuration and declare the target release.
- `plan`: Dry-run friendly subset used during CI validation.
- `rollback`: Document and simulate the rollback workflow.

Execute a dry-run deployment:

```bash
ansible-playbook -i ansible/inventory.yml ansible/site.yml --tags deploy,plan --check -e "deploy_env=staging"
```

Simulate a rollback:

```bash
ansible-playbook -i ansible/inventory.yml ansible/site.yml --tags rollback --check -e "deploy_env=staging"
```
