variable "project" {
  description = "Human friendly name for the deployment."
  type        = string
  default     = "whisper-transcriber"
}

variable "environment" {
  description = "Deployment environment identifier (e.g. dev, staging, prod)."
  type        = string
}

variable "aws_region" {
  description = "AWS region where the infrastructure will live."
  type        = string
  default     = "us-east-1"
}

variable "uploads_bucket_name" {
  description = "Optional override for the S3 bucket that stores uploaded audio."
  type        = string
  default     = null
}

variable "force_destroy_uploads" {
  description = "Whether to allow Terraform to delete non-empty upload buckets."
  type        = bool
  default     = false
}

variable "vpc_cidr" {
  description = "CIDR block for the primary VPC."
  type        = string
  default     = "10.40.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "List of CIDR blocks for public subnets."
  type        = list(string)
  default     = ["10.40.10.0/24", "10.40.11.0/24"]
}

variable "availability_zones" {
  description = "AWS availability zones used for the public subnets."
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"]
}

variable "allowed_cidr_blocks" {
  description = "CIDR blocks allowed to reach the service load balancer."
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "db_username" {
  description = "Database admin username."
  type        = string
  default     = "transcriber"
}

variable "db_password" {
  description = "Database admin password."
  type        = string
  sensitive   = true
}

variable "db_name" {
  description = "Name of the primary application database."
  type        = string
  default     = "whisper_transcriber"
}

variable "db_engine_version" {
  description = "Aurora PostgreSQL engine version."
  type        = string
  default     = "15.4"
}

variable "db_instance_class" {
  description = "Instance class for the Aurora writer node."
  type        = string
  default     = "db.serverless"
}

variable "db_backup_retention_days" {
  description = "Number of days to retain automated backups."
  type        = number
  default     = 7
}

variable "task_cpu" {
  description = "CPU units allocated to the ECS task."
  type        = number
  default     = 1024
}

variable "task_memory" {
  description = "Memory (MiB) allocated to the ECS task."
  type        = number
  default     = 2048
}

variable "desired_task_count" {
  description = "Desired number of API task replicas."
  type        = number
  default     = 2
}

variable "ecs_execution_role_arn" {
  description = "IAM role used by ECS to pull images and write logs."
  type        = string
}

variable "ecs_task_role_arn" {
  description = "IAM role attached to the running task for runtime permissions."
  type        = string
}

variable "release_image_tag" {
  description = "Container image tag that should be deployed."
  type        = string
  default     = "latest"
}

variable "rollback_image_tag" {
  description = "Container image tag that represents the last known good release."
  type        = string
  default     = "previous"
}

variable "secret_key_parameter_arn" {
  description = "ARN of the secret containing the SECRET_KEY value."
  type        = string
}

variable "jwt_secret_key_parameter_arn" {
  description = "ARN of the secret containing the JWT_SECRET_KEY value."
  type        = string
}

variable "admin_bootstrap_password_parameter_arn" {
  description = "ARN of the secret containing the ADMIN_BOOTSTRAP_PASSWORD value."
  type        = string
}

variable "redis_url_parameter_arn" {
  description = "ARN of the secret containing the REDIS_URL value."
  type        = string
}

variable "redis_password_parameter_arn" {
  description = "ARN of the secret containing the REDIS_PASSWORD value."
  type        = string
}

variable "metrics_token_parameter_arn" {
  description = "ARN of the secret containing the METRICS_TOKEN used to protect /metrics."
  type        = string
}

variable "worker_desired_count" {
  description = "Desired number of Celery worker tasks."
  type        = number
  default     = 1
}

variable "worker_task_cpu" {
  description = "CPU units allocated to the Celery worker task."
  type        = number
  default     = 1024
}

variable "worker_task_memory" {
  description = "Memory (MiB) allocated to the Celery worker task."
  type        = number
  default     = 2048
}
