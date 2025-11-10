# syntax=docker/dockerfile:1.7

########################
# Frontend build stage #
########################
FROM node:25-alpine@sha256:7e467cc5aa91c87e94f93c4608cf234ca24aac3ec941f7f3db207367ccccdd11 AS frontend-builder

WORKDIR /frontend

# Copy only the files required for dependency resolution first
COPY frontend/package.json frontend/package-lock.json ./

RUN npm ci --silent

# Copy the remainder of the frontend source and build
COPY frontend/ ./
RUN npm run build

######################
# Python deps stage  #
######################
FROM python:3.13-slim-bookworm AS python-builder

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        ffmpeg \
        libmagic1 \
        && rm -rf /var/lib/apt/lists/*

ENV VIRTUAL_ENV=/opt/venv
RUN python -m venv "$VIRTUAL_ENV"
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

WORKDIR /tmp/build

# Copy application Python dependency manifests only
COPY requirements.txt ./

# Install Python dependencies into the virtual environment
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

##################
# Runtime stage  #
##################
FROM python:3.13-slim-bookworm AS production

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        ffmpeg \
        gosu \
        libmagic1 \
        && rm -rf /var/lib/apt/lists/*

ARG APP_UID=1000
ARG APP_GID=1000
RUN groupadd -r -g "$APP_GID" appuser && \
    useradd -r -u "$APP_UID" -g appuser -m -d /home/appuser -s /usr/sbin/nologin appuser

WORKDIR /app

# Copy in the Python environment built in the previous stage
COPY --from=python-builder /opt/venv /opt/venv

# Copy backend application code
COPY --chown=appuser:appuser api/ ./api/
COPY --chown=appuser:appuser models/ ./models/
COPY --chown=appuser:appuser alembic.ini ./

# Copy built frontend assets
COPY --from=frontend-builder --chown=appuser:appuser /frontend/dist/ ./api/static/

# Copy runtime scripts
COPY --chown=root:root scripts/healthcheck.sh /usr/local/bin/healthcheck.sh
COPY --chown=root:root scripts/docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod 755 /usr/local/bin/healthcheck.sh /usr/local/bin/docker-entrypoint.sh

# Prepare directories required at runtime
RUN mkdir -p /app/data /app/storage/uploads /app/storage/transcripts /app/logs && \
    chown -R appuser:appuser /app && \
    find /app -type d -exec chmod 750 {} \; && \
    find /app -type f -exec chmod 640 {} \;

ARG BUILD_VERSION=dev
ARG BUILD_SHA=unknown
ARG BUILD_DATE=unknown
RUN printf 'BUILD_VERSION=%s\nBUILD_SHA=%s\nBUILD_DATE=%s\n' "$BUILD_VERSION" "$BUILD_SHA" "$BUILD_DATE" > /etc/whisper-build.info && \
    chown appuser:appuser /etc/whisper-build.info && \
    chmod 640 /etc/whisper-build.info

ENV SERVICE_TYPE=app \
    VITE_API_HOST=http://localhost:8001

EXPOSE 8001

USER appuser

HEALTHCHECK --interval=5m --timeout=10s --start-period=30s --retries=3 \
    CMD /usr/local/bin/healthcheck.sh

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["python", "-m", "api.main"]

LABEL maintainer="whisper-transcriber" \
      org.opencontainers.image.source="https://github.com/buymeagoat/whisper-transcriber" \
      org.opencontainers.image.title="Whisper Transcriber" \
      org.opencontainers.image.description="Secure containerized audio transcription service"
