FROM python:3.11-slim

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
COPY alembic.ini .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY scripts/healthcheck.sh /usr/local/bin/healthcheck.sh
RUN chmod +x /usr/local/bin/healthcheck.sh
COPY scripts/server_entry.py ./scripts/server_entry.py
COPY scripts/docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

COPY api         ./api
COPY models      ./models
RUN --mount=type=secret,id=secret_key \
    SECRET_KEY=$(cat /run/secrets/secret_key) \
    python -c "from api.utils.model_validation import validate_models_dir; validate_models_dir()"
RUN mkdir -p uploads transcripts logs \
    && chown -R appuser:appuser /app
COPY frontend/dist ./api/static

# Default service type for healthcheck script
ENV SERVICE_TYPE=api


ENV VITE_API_HOST=http://localhost:8000
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=10s --retries=3 CMD /usr/local/bin/healthcheck.sh
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["python", "scripts/server_entry.py"]
