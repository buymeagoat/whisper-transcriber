# syntax=docker/dockerfile:1.7
# Multi-stage build: Stage 1 - Build Frontend
FROM node:18-alpine AS frontend-builder

# Set working directory for frontend
WORKDIR /frontend

# Copy frontend dependency files
COPY frontend/package*.json ./

# Install Node.js dependencies with clean slate
RUN npm ci --production=false --silent

# Copy frontend source code
COPY frontend/ ./

# Build the frontend for production
RUN npm run build

# Verify build output exists
RUN ls -la dist/ && echo "Frontend build completed"

# Multi-stage build: Stage 2 - Build Backend
FROM python:3.11-slim-bookworm AS backend-builder

# Security: Create non-root user early to establish proper ownership
RUN groupadd -r -g 1000 appuser && \
    useradd -r -u 1000 -g appuser -m -d /home/appuser -s /sbin/nologin appuser

# Install system dependencies needed for Python packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        ca-certificates \
        ffmpeg \
        && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy Python dependencies
COPY requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Multi-stage build: Stage 3 - Production Image
FROM python:3.11-slim-bookworm AS production

# Security: Create non-root user
RUN groupadd -r -g 1000 appuser && \
    useradd -r -u 1000 -g appuser -m -d /home/appuser -s /sbin/nologin appuser

# Install runtime dependencies only
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        ca-certificates \
        gosu \
        && rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/* /tmp/* /var/tmp/*

# Security: Create secure application directory structure
RUN mkdir -p /app /app/data /app/storage /app/storage/uploads /app/storage/transcripts /app/logs && \
    chown -R appuser:appuser /app && \
    chmod -R 750 /app

WORKDIR /app

# Security: Set secure Python environment variables
ENV PYTHONPATH=/app \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Copy Python packages from builder stage
COPY --from=backend-builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=backend-builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=appuser:appuser api/ ./api/
COPY --chown=appuser:appuser models/ ./models/
COPY --chown=root:root alembic.ini ./

# Copy built frontend from frontend-builder stage
COPY --from=frontend-builder --chown=appuser:appuser /frontend/dist/ ./api/static/

# Verify frontend files were copied
RUN ls -la /app/api/static/ && echo "Frontend files copied successfully"

# Copy and secure script files
COPY --chown=root:root scripts/healthcheck.sh /usr/local/bin/healthcheck.sh
COPY --chown=root:root scripts/docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod 755 /usr/local/bin/healthcheck.sh /usr/local/bin/docker-entrypoint.sh

# Security: Set final ownership and permissions for application files
RUN chown -R appuser:appuser /app && \
    find /app -type d -exec chmod 750 {} \; && \
    find /app -type f -exec chmod 640 {} \;

# Security: Set service configuration with secure defaults
ENV SERVICE_TYPE=app \
    VITE_API_HOST=http://localhost:8001

# Security: Use non-privileged port
EXPOSE 8001

# Security: Switch to non-root user for all subsequent operations
USER appuser

# Security: Configure healthcheck with proper timeouts
HEALTHCHECK --interval=5m --timeout=10s --start-period=30s --retries=3 \
    CMD /usr/local/bin/healthcheck.sh

# Security: Use secure entrypoint and command
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["python", "-m", "api.main"]

# Security: Add image metadata for security scanning
LABEL maintainer="whisper-transcriber" \
      description="Secure Whisper Transcriber Application" \
      version="2.0.0" \
      security.scan="enabled" \
      org.opencontainers.image.source="https://github.com/buymeagoat/whisper-transcriber" \
      org.opencontainers.image.title="Whisper Transcriber" \
      org.opencontainers.image.description="Secure containerized audio transcription service"
