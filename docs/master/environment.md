# Environment Variables

This page lists all configurable environment variables.

## Core App Config

| Variable Name | Required? | Default Value | Used In | Description |
| --- | --- | --- | --- | --- |
| DB_URL | No | postgresql+psycopg2://whisper:whisper@db:5432/whisper | api/settings.py, docker-compose.yml | Database connection string |
| PORT | No | 8000 | api/settings.py, scripts/server_entry.py | TCP port for Uvicorn |
| VITE_API_HOST | No | http://localhost:8000 | api/settings.py, docker-compose.yml | Base URL for the API used by the web UI |
| VITE_DEFAULT_TRANSCRIPT_FORMAT | No | txt | api/settings.py | Default transcript download format |
| JOB_QUEUE_BACKEND | No | thread | api/settings.py, docker-compose.yml | Queue implementation to use |
| MAX_CONCURRENT_JOBS | No | 2 | api/settings.py | Worker thread count for internal queue |
| MODEL_DIR | No | models/ | api/settings.py | Directory of Whisper models |
| WHISPER_BIN | No | whisper | api/settings.py | Path to Whisper CLI |
| WHISPER_LANGUAGE | No | en | api/settings.py | Default language passed to Whisper |
| WHISPER_TIMEOUT_SECONDS | No | 0 | api/settings.py | Max seconds to wait for Whisper before failing |
| OPENAI_API_KEY | No | None | api/settings.py | API key enabling transcript analysis |
| OPENAI_MODEL | No | gpt-3.5-turbo | api/settings.py | Model used when analysis is enabled |

## Logging & Monitoring

| Variable Name | Required? | Default Value | Used In | Description |
| --- | --- | --- | --- | --- |
| LOG_LEVEL | No | DEBUG | api/settings.py | Logging level for backend loggers |
| LOG_FORMAT | No | plain | api/settings.py | plain or json log format |
| LOG_TO_STDOUT | No | False | api/settings.py | Mirror logs to container console |
| LOG_MAX_BYTES | No | 10000000 | api/settings.py | Log file rotation size |
| LOG_BACKUP_COUNT | No | 3 | api/settings.py | Number of rotated log files to keep |
| TIMEZONE | No | UTC | api/settings.py | Local timezone for log timestamps |
| API_HEALTH_TIMEOUT | No | 300 | scripts/* | Seconds scripts wait for API to become healthy |
| DB_CONNECT_ATTEMPTS | No | 10 | api/settings.py | How many times to retry DB connection |
| BROKER_CONNECT_ATTEMPTS | No | 20 | api/settings.py | How many times to ping the Celery broker |
| BROKER_PING_TIMEOUT | No | 60 | scripts/docker-entrypoint.sh | Seconds worker waits for RabbitMQ |

## Queue / Concurrency

| Variable Name | Required? | Default Value | Used In | Description |
| --- | --- | --- | --- | --- |
