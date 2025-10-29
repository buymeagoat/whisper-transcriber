#!/bin/bash
# Production startup script for Whisper Transcriber
# This script loads production environment variables and starts the application

set -e

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

# Validate that we have required secrets
if [ -z "$SECRET_KEY" ] || [ "$SECRET_KEY" = "" ]; then
    echo "🚨 CRITICAL: SECRET_KEY is not set for production!"
    exit 1
fi

if [ -z "$JWT_SECRET_KEY" ] || [ "$JWT_SECRET_KEY" = "" ]; then
    echo "🚨 CRITICAL: JWT_SECRET_KEY is not set for production!"
    exit 1
fi

# Print configuration summary (without secrets)
echo "📊 Production Configuration:"
echo "   Environment: $ENVIRONMENT"
echo "   Debug: $DEBUG"
echo "   API Host: ${API_HOST:-0.0.0.0}"
echo "   API Port: ${API_PORT:-8000}"
echo "   Database: ${DATABASE_URL:-sqlite:///app/data/whisper_production.db}"
echo "   Secret Key: [SET - ${#SECRET_KEY} characters]"
echo "   JWT Key: [SET - ${#JWT_SECRET_KEY} characters]"

# Create required directories
mkdir -p /app/data /app/logs /app/storage/uploads /app/storage/transcripts

# Start the application
echo "🚀 Starting application with production settings..."
exec python -m api.main