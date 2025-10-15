# syntax=docker/dockerfile:1.7
# Use specific SHA256 digest for security and reproducibility
FROM python:3.11-slim-bookworm@sha256:a96504e4e5a0e6cacf4fe789411497efb870c29ccd5b6c8082dcaaa9e2a34145

# Security: Install dev requirements when building test images
ARG INSTALL_DEV=false

# Security: Create non-root user early to establish proper ownership
RUN groupadd -r -g 1000 appuser && \
    useradd -r -u 1000 -g appuser -m -d /home/appuser -s /sbin/nologin appuser

# Security: Use slim image and minimize installed packages
COPY cache/apt /tmp/apt
RUN apt-get update && \
    # Security: Only install essential packages
    apt-get install -y --no-install-recommends \
        curl \
        ca-certificates \
        gosu && \
    # Install cached packages if available
    (dpkg -i /tmp/apt/*.deb || apt-get install -f -y --no-install-recommends) && \
    # Security: Clean up package cache and temporary files
    rm -rf /tmp/apt /var/lib/apt/lists/* /var/cache/apt/archives/* /tmp/* /var/tmp/*

# Security: Create secure application directory structure
RUN mkdir -p /app /app/data /app/storage /app/storage/uploads /app/storage/transcripts /app/logs && \
    # Security: Set proper ownership and permissions
    chown -R appuser:appuser /app && \
    # Security: Restrict permissions (750 for directories, 640 for files)
    chmod -R 750 /app

WORKDIR /app

# Security: Set secure Python environment variables
ENV PYTHONPATH=/app \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Security: Copy only necessary files as root, then change ownership
COPY --chown=root:root requirements.txt requirements-dev.txt alembic.ini ./
COPY --chown=root:root cache/pip ./wheels/

# Security: Install Python packages with security considerations
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir --find-links ./wheels -r requirements.txt && \
    if [ "$INSTALL_DEV" = "true" ]; then \
        pip install --no-cache-dir --find-links ./wheels -r requirements-dev.txt; \
    fi && \
    # Security: Remove installation cache and temporary files
    rm -rf ./wheels ~/.cache /root/.cache /tmp/* /var/tmp/*

# Security: Copy and secure script files
COPY --chown=root:root scripts/healthcheck.sh /usr/local/bin/healthcheck.sh
COPY --chown=root:root scripts/docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod 755 /usr/local/bin/healthcheck.sh /usr/local/bin/docker-entrypoint.sh

# Security: Copy application code with proper ownership
COPY --chown=appuser:appuser app/ ./app/
COPY --chown=appuser:appuser models/ ./models/

# Security: Copy frontend assets if available (optional)
COPY --chown=appuser:appuser web/dist ./app/static/ 2>/dev/null || true

# Security: Set final ownership and permissions for application files
RUN chown -R appuser:appuser /app && \
    # Security: Make directories readable/executable, files readable only
    find /app -type d -exec chmod 750 {} \; && \
    find /app -type f -exec chmod 640 {} \;

# Security: Set service configuration with secure defaults
ENV SERVICE_TYPE=app \
    VITE_API_HOST=http://localhost:8000

# Security: Use non-privileged port
EXPOSE 8000

# Security: Switch to non-root user for all subsequent operations
USER appuser

# Security: Configure healthcheck with proper timeouts
HEALTHCHECK --interval=5m --timeout=10s --start-period=30s --retries=3 \
    CMD /usr/local/bin/healthcheck.sh

# Security: Use secure entrypoint and command
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["python", "-m", "app.main"]

# Security: Add image metadata for security scanning
LABEL maintainer="whisper-transcriber" \
      description="Secure Whisper Transcriber Application" \
      version="2.0.0" \
      security.scan="enabled" \
      org.opencontainers.image.source="https://github.com/buymeagoat/whisper-transcriber" \
      org.opencontainers.image.title="Whisper Transcriber" \
      org.opencontainers.image.description="Secure containerized audio transcription service"
