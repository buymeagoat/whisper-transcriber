terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
  }
}

provider "aws" {
  region                      = var.aws_region
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true
  s3_force_path_style         = true

  default_tags {
    tags = {
      Application = var.project
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

locals {
  project_slug = replace(var.project, " ", "-")
  name_prefix  = "${local.project_slug}-${var.environment}"
}

resource "random_id" "uploads_bucket_suffix" {
  byte_length = 2
}

resource "aws_s3_bucket" "uploads" {
  bucket        = coalesce(var.uploads_bucket_name, "${local.name_prefix}-uploads-${random_id.uploads_bucket_suffix.hex}")
  force_destroy = var.force_destroy_uploads
}

resource "aws_s3_bucket_public_access_block" "uploads" {
  bucket = aws_s3_bucket.uploads.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_ecr_repository" "api" {
  name                 = "${local.name_prefix}-api"
  image_tag_mutability = "MUTABLE"

  encryption_configuration {
    encryption_type = "AES256"
  }

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true
}

resource "aws_subnet" "public" {
  count                   = length(var.public_subnet_cidrs)
  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.public_subnet_cidrs[count.index]
  availability_zone       = element(var.availability_zones, count.index)
  map_public_ip_on_launch = true
}

resource "aws_internet_gateway" "this" {
  vpc_id = aws_vpc.main.id
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.this.id
  }
}

resource "aws_route_table_association" "public" {
  count          = length(aws_subnet.public)
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

resource "aws_security_group" "service" {
  name        = "${local.name_prefix}-service"
  description = "Whisper Transcriber service access"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "Allow inbound HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = var.allowed_cidr_blocks
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_rds_cluster" "transcriber" {
  cluster_identifier           = "${local.name_prefix}-aurora"
  engine                       = "aurora-postgresql"
  engine_mode                  = "provisioned"
  engine_version               = var.db_engine_version
  master_username              = var.db_username
  master_password              = var.db_password
  database_name                = var.db_name
  backup_retention_period      = var.db_backup_retention_days
  preferred_backup_window      = "04:00-05:00"
  preferred_maintenance_window = "sun:06:00-sun:07:00"
  skip_final_snapshot          = true
  storage_encrypted            = true
  deletion_protection          = false
  vpc_security_group_ids       = [aws_security_group.service.id]
  db_subnet_group_name         = aws_rds_cluster_subnet_group.transcriber.name
}

resource "aws_rds_cluster_instance" "transcriber" {
  identifier          = "${local.name_prefix}-aurora-instance"
  cluster_identifier  = aws_rds_cluster.transcriber.id
  instance_class      = var.db_instance_class
  engine              = aws_rds_cluster.transcriber.engine
  engine_version      = aws_rds_cluster.transcriber.engine_version
  publicly_accessible = false
}

resource "aws_rds_cluster_subnet_group" "transcriber" {
  name       = "${local.name_prefix}-db-subnets"
  subnet_ids = aws_subnet.public[*].id
}

resource "aws_ecs_cluster" "transcriber" {
  name = "${local.name_prefix}-cluster"
}

resource "aws_ecs_task_definition" "api" {
  family                   = "${local.name_prefix}-api"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = tostring(var.task_cpu)
  memory                   = tostring(var.task_memory)
  execution_role_arn       = var.ecs_execution_role_arn
  task_role_arn            = var.ecs_task_role_arn

  container_definitions = jsonencode([
    {
      name      = "api"
      image     = "${aws_ecr_repository.api.repository_url}:${var.release_image_tag}"
      essential = true
      portMappings = [
        {
          containerPort = 8080
          hostPort      = 8080
          protocol      = "tcp"
        }
      ]
      environment = [
        {
          name  = "APP_ENV"
          value = var.environment
        },
        {
          name  = "DATABASE_URL"
          value = "postgresql://${var.db_username}:${var.db_password}@${aws_rds_cluster.transcriber.endpoint}:5432/${var.db_name}"
        },
        {
          name  = "UPLOADS_BUCKET"
          value = aws_s3_bucket.uploads.bucket
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = "/ecs/${local.name_prefix}-api"
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "api"
        }
      }
    }
  ])
}

resource "aws_ecs_service" "api" {
  name            = "${local.name_prefix}-svc"
  cluster         = aws_ecs_cluster.transcriber.id
  task_definition = aws_ecs_task_definition.api.arn
  desired_count   = var.desired_task_count
  launch_type     = "FARGATE"

  network_configuration {
    assign_public_ip = true
    security_groups  = [aws_security_group.service.id]
    subnets          = aws_subnet.public[*].id
  }

  deployment_minimum_healthy_percent = 50
  deployment_maximum_percent         = 200
}

output "uploads_bucket_name" {
  description = "Name of the S3 bucket used to store uploaded audio."
  value       = aws_s3_bucket.uploads.bucket
}

output "ecr_repository_url" {
  description = "URI of the container repository hosting the API image."
  value       = aws_ecr_repository.api.repository_url
}

output "database_endpoint" {
  description = "Writer endpoint for the Aurora cluster."
  value       = aws_rds_cluster.transcriber.endpoint
}

output "ecs_cluster_name" {
  description = "Name of the ECS cluster running API tasks."
  value       = aws_ecs_cluster.transcriber.name
}
