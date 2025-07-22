# syntax=docker/dockerfile:1.4@sha256:9ba7531bd80fb0a858632727cf7a112fbfd19b17e94c4e84ced81e24ef1a0dbc
FROM python:3.11-slim

# Install dev requirements when building test images
ARG INSTALL_DEV=false

# Secret used for model validation during build
ARG SECRET_KEY

RUN apt-get update && apt-get install -y --no-install-recommends \
      ffmpeg git curl gosu && \
      apt-get clean && rm -rf /var/lib/apt/lists/*

# Create a non-root user to run Celery workers
RUN groupadd -g 1000 appuser && \
    useradd -m -u 1000 -g appuser appuser

RUN mkdir -p /app && chown -R appuser:appuser /app

WORKDIR /app
ENV PYTHONPATH=/app
COPY requirements.txt .
COPY requirements-dev.txt .
COPY alembic.ini .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt --retries 5 --resume-retries 3 --timeout 60 && \
    if [ "$INSTALL_DEV" = "true" ]; then \
        pip install --no-cache-dir -r requirements-dev.txt --retries 5 --resume-retries 3 --timeout 60; \
    fi

COPY scripts/healthcheck.sh /usr/local/bin/healthcheck.sh
RUN chmod +x /usr/local/bin/healthcheck.sh
COPY scripts/server_entry.py ./scripts/server_entry.py
COPY scripts/docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

COPY api         ./api
COPY models      ./models
COPY worker.py   ./worker.py
# Use BuildKit secrets when available, otherwise rely on the build argument
RUN --mount=type=secret,id=secret_key \
    bash -c 'if [ -f /run/secrets/secret_key ]; then export SECRET_KEY="$(cat /run/secrets/secret_key)"; fi; \ 
    python -c "from api.utils.model_validation import validate_models_dir; validate_models_dir()"'
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
