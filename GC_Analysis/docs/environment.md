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
| CELERY_BROKER_URL | No | amqp://guest:guest@broker:5672// | api/settings.py, docker-compose.yml | Celery broker URL when JOB_QUEUE_BACKEND=broker |
| CELERY_BACKEND_URL | No | rpc:// | api/settings.py, docker-compose.yml | Celery result backend |
| MAX_CONCURRENT_JOBS | No | 2 | api/settings.py | Worker thread count |
| JOB_QUEUE_BACKEND | No | thread | api/settings.py | Queue backend type |

## Storage

| Variable Name | Required? | Default Value | Used In | Description |
| --- | --- | --- | --- | --- |
| STORAGE_BACKEND | No | local | api/settings.py | Storage implementation |
| LOCAL_STORAGE_DIR | No | project root | api/settings.py | Base directory for local storage |
| AWS_ACCESS_KEY_ID | No | None | api/settings.py | Access key for S3 backend |
| AWS_SECRET_ACCESS_KEY | No | None | api/settings.py | Secret key for S3 backend |
| S3_BUCKET | No | None | api/settings.py | Bucket name for cloud storage |
| MAX_UPLOAD_SIZE | No | 2147483648 | api/settings.py | Maximum upload file size |

## Security / Auth

| Variable Name | Required? | Default Value | Used In | Description |
| --- | --- | --- | --- | --- |
| SECRET_KEY | Yes | None | api/settings.py, .env.example | Secret used to sign JWTs |
| ACCESS_TOKEN_EXPIRE_MINUTES | No | 60 | api/settings.py | JWT lifetime in minutes |
| ALLOW_REGISTRATION | No | True | api/settings.py | Enable public /register endpoint |
| AUTH_USERNAME | No | admin | api/settings.py | Legacy static username (deprecated) |
| AUTH_PASSWORD | No | admin | api/settings.py | Legacy static password (deprecated) |
| CORS_ORIGINS | No | * | api/settings.py | Allowed CORS origins |
| ENABLE_SERVER_CONTROL | No | False | api/settings.py | Allow /admin/shutdown and /admin/restart |

## Advanced Debug / Build

| Variable Name | Required? | Default Value | Used In | Description |
| --- | --- | --- | --- | --- |
| CLEANUP_ENABLED | No | True | api/settings.py | Periodic cleanup of old transcripts |
| CLEANUP_DAYS | No | 30 | api/settings.py | Days to keep transcripts |
| CLEANUP_INTERVAL_SECONDS | No | 86400 | api/settings.py | Cleanup task interval |
| CACHE_DIR | No | /tmp/docker_cache | design_scope.md, scripts/* | Directory for build cache. In WSL, override with /mnt/wsl/shared/docker_cache for reliability. |
| SKIP_PRESTAGE | No | 0 | design_scope.md, scripts/* | Skip cache refresh during build |

