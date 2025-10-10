# syntax=docker/dockerfile:1.4@sha256:9ba7531bd80fb0a858632727cf7a112fbfd19b17e94c4e84ced81e24ef1a0dbc
FROM python:3.11-bookworm

# Install dev requirements when building test images
ARG INSTALL_DEV=false


COPY cache/apt /tmp/apt
RUN apt-get update || (cat /etc/resolv.conf && ping -c 3 deb.debian.org && exit 1) && \
    dpkg -i /tmp/apt/*.deb || apt-get install -f -y && \
    rm -rf /tmp/apt && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install gosu for dropping privileges in entrypoint
RUN apt-get update && apt-get install -y gosu && rm -rf /var/lib/apt/lists/*

# Create a non-root user to run Celery workers
RUN groupadd -g 1000 appuser && \
    useradd -m -u 1000 -g appuser appuser

RUN mkdir -p /app && chown -R appuser:appuser /app

WORKDIR /app
ENV PYTHONPATH=/app
COPY requirements.txt .
COPY requirements-dev.txt .
COPY alembic.ini .
COPY cache/pip ./wheels
RUN pip install --no-cache-dir --no-index --find-links ./wheels --upgrade pip && \
    pip install --no-index --find-links ./wheels -r requirements.txt && \
    if [ "$INSTALL_DEV" = "true" ]; then \
        pip install --no-index --find-links ./wheels -r requirements-dev.txt; \
    fi && rm -rf ./wheels

COPY scripts/healthcheck.sh /usr/local/bin/healthcheck.sh
RUN chmod +x /usr/local/bin/healthcheck.sh
COPY scripts/server_entry.py ./scripts/server_entry.py
COPY scripts/docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

COPY api         ./api
COPY models      ./models
COPY api/worker.py   ./api/worker.py
# Validate models with environment variables
RUN SECRET_KEY=build-time-secret AUTH_USERNAME=build-user AUTH_PASSWORD=build-pass \
    python -c "from api.utils.model_validation import validate_models_dir; validate_models_dir()"
RUN mkdir -p uploads transcripts logs \
    && chown -R appuser:appuser /app
COPY frontend/dist ./api/static

# Default service type for healthcheck script
ENV SERVICE_TYPE=api


ENV VITE_API_HOST=http://localhost:8000
EXPOSE 8000
HEALTHCHECK --interval=5m --timeout=10s --retries=3 CMD /usr/local/bin/healthcheck.sh
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["python", "scripts/server_entry.py"]
