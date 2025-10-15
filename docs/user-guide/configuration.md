# Configuration Guide

This guide covers all configuration options for the Whisper Transcriber streamlined application.

## Environment Variables

The application uses environment variables for configuration. Copy `config/.env.example` to `.env` and customize as needed.

### Core Settings

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `REDIS_URL` | No | `redis://localhost:6379/0` | Redis connection string for task queue |
| `DATABASE_URL` | No | `sqlite:///app/data/app.db` | SQLite database file path |
| `WHISPER_MODEL_DIR` | No | `/app/models` | Directory containing Whisper model files |

### Application Settings

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `PORT` | No | `8000` | TCP port for the web server |
| `CELERY_CONCURRENCY` | No | `2` | Number of worker processes (match CPU cores) |
| `MAX_FILE_SIZE_MB` | No | `100` | Maximum upload file size in megabytes |
| `ALLOWED_AUDIO_FORMATS` | No | `mp3,wav,m4a,flac` | Supported audio file formats |

### Whisper Settings

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `WHISPER_LANGUAGE` | No | `auto` | Default language for transcription |
| `WHISPER_TIMEOUT_SECONDS` | No | `3600` | Maximum time for transcription before timeout |
| `DEFAULT_WHISPER_MODEL` | No | `small` | Default model (tiny, small, medium, large-v3) |

### Logging

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `LOG_LEVEL` | No | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `LOG_TO_STDOUT` | No | `true` | Output logs to console |

## Configuration Files

### Docker Environment

When using Docker Compose, create a `.env` file in the project root:

```bash
# Core settings
REDIS_URL=redis://redis:6379/0
DATABASE_URL=sqlite:///app/data/app.db
WHISPER_MODEL_DIR=/app/models

# Performance settings
CELERY_CONCURRENCY=4
MAX_FILE_SIZE_MB=200

# Optional settings
WHISPER_LANGUAGE=en
LOG_LEVEL=INFO
```

### Development Environment

For local development without Docker:

```bash
# Local development settings
REDIS_URL=redis://localhost:6379/0
DATABASE_URL=sqlite:///./app.db
WHISPER_MODEL_DIR=./models

# Development settings
CELERY_CONCURRENCY=1
LOG_LEVEL=DEBUG
LOG_TO_STDOUT=true
```

## Model Configuration

### Required Models

Place these Whisper model files in the `models/` directory:

- `tiny.pt` - Fastest, lowest quality
- `small.pt` - Good balance of speed and quality  
- `medium.pt` - Higher quality, slower
- `large-v3.pt` - Best quality, slowest
- `base.pt` - Basic model

### Model Selection

Users can select models in the web interface, or set a default:

```bash
DEFAULT_WHISPER_MODEL=medium
```

## Performance Tuning

### CPU Optimization

Match `CELERY_CONCURRENCY` to your CPU cores:

```bash
# For 4-core system
CELERY_CONCURRENCY=4

# For 8-core system  
CELERY_CONCURRENCY=8
```

### Memory Considerations

Larger models require more RAM:

- `tiny`: ~1GB RAM per worker
- `small`: ~2GB RAM per worker
- `medium`: ~5GB RAM per worker  
- `large-v3`: ~10GB RAM per worker

### Storage Settings

```bash
# Increase upload limits for longer audio
MAX_FILE_SIZE_MB=500

# Support additional formats
ALLOWED_AUDIO_FORMATS=mp3,wav,m4a,flac,ogg,aac
```

## Troubleshooting Configuration

### Common Issues

**Redis Connection Failed**
```bash
# Check Redis is running
docker logs whisper-redis

# Verify connection string
REDIS_URL=redis://redis:6379/0
```

**Models Not Found**
```bash
# Verify model directory
ls -la models/
# Should show: base.pt, small.pt, medium.pt, large-v3.pt, tiny.pt
```

**Worker Not Processing Jobs**
```bash
# Check worker logs
docker logs whisper-worker

# Verify concurrency setting
CELERY_CONCURRENCY=2
```

### Debugging

Enable debug logging:

```bash
LOG_LEVEL=DEBUG
LOG_TO_STDOUT=true
```

Check application health:
```bash
curl http://localhost:8000/health
```
