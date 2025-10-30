#!/bin/bash
# Production startup script for Whisper Transcriber
# This script loads production environment variables and starts the application

set -euo pipefail

require_secret() {
    local name="$1"
    local description="$2"
    local value="${!name-}"

    if [ -z "${value}" ]; then
        echo "🚨 CRITICAL: ${name} (${description}) is not set for production!"
        exit 1
    fi

    case "${value,,}" in
        "change-me"|"changeme"|"default"|"placeholder"|"example"|"sample"|"localtest")
            echo "🚨 CRITICAL: ${name} (${description}) is using an insecure placeholder. Provide a rotated value before starting."
            exit 1
            ;;
    esac
}

echo "🚀 Starting Whisper Transcriber in PRODUCTION mode"

# Load production environment
if [ -f /app/.env.production ]; then
    echo "📋 Loading production environment from .env.production"
    export $(grep -v '^#' /app/.env.production | xargs)
else
    echo "⚠️  Production environment file not found, using environment variables"
fi

# Ensure critical production variables are set
export ENVIRONMENT=production
export DEBUG=false

# Validate that we have required secrets (values redacted)
require_secret "SECRET_KEY" "application signing key"
require_secret "JWT_SECRET_KEY" "JWT signing key"
require_secret "DATABASE_URL" "database connection string"
require_secret "REDIS_URL" "Redis connection string"
require_secret "ADMIN_BOOTSTRAP_PASSWORD" "bootstrap administrator password"

# Print configuration summary without exposing environment variables
echo "📊 Production configuration validated (environment values redacted)"
echo "   • Critical secrets present and verified for rotation"
echo "   • Network bindings and service endpoints loaded from environment"
echo "   • Detailed values intentionally withheld from logs"

# Create required directories
mkdir -p /app/data /app/logs /app/storage/uploads /app/storage/transcripts

# Start the application
echo "🚀 Starting application with production settings..."
exec python -m api.main
