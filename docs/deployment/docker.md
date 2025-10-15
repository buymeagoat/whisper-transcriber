# Docker Deployment Guide

This guide covers deploying Whisper Transcriber using Docker and Docker Compose.

## Quick Deployment

### Prerequisites

- **Docker Engine** 20.10+
- **Docker Compose** 2.0+
- **4GB+ RAM** recommended
- **10GB+ disk space** for models and storage

### Basic Deployment

1. **Clone and configure**
   ```bash
   git clone https://github.com/buymeagoat/whisper-transcriber.git
   cd whisper-transcriber
   
   # Copy environment template
   cp config/.env.example .env
   ```

2. **Download Whisper models**
   ```bash
   # Create models directory
   mkdir -p models/
   
   # Download required models (choose based on quality/speed needs)
   wget https://openaipublic.azureedge.net/main/whisper/models/tiny.pt -O models/tiny.pt
   wget https://openaipublic.azureedge.net/main/whisper/models/small.pt -O models/small.pt
   wget https://openaipublic.azureedge.net/main/whisper/models/medium.pt -O models/medium.pt
   ```

3. **Start the application**
   ```bash
   docker-compose up -d
   ```

4. **Verify deployment**
   ```bash
   # Check service health
   curl http://localhost:8000/
   
   # View logs
   docker-compose logs -f
   ```

## Configuration

### Environment Variables

Edit `.env` file for your deployment:

```bash
# Core settings
REDIS_URL=redis://redis:6379/0
DATABASE_URL=sqlite:///app/data/app.db
WHISPER_MODEL_DIR=/app/models

# Performance settings (adjust for your hardware)
CELERY_CONCURRENCY=2              # Number of CPU cores
MAX_FILE_SIZE_MB=100              # Upload limit

# Optional settings
DEFAULT_WHISPER_MODEL=small       # Default transcription model
WHISPER_LANGUAGE=auto             # Auto-detect language
LOG_LEVEL=INFO                    # Logging level
```

### Docker Compose Configuration

The `docker-compose.yml` defines three services:

```yaml
services:
  redis:          # Task queue
  app:            # Web application  
  worker:         # Background transcription
```

## Service Architecture

### Container Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     Redis       │    │       App       │    │     Worker      │
│  (Task Queue)   │◄───┤  (Web Service)  ├───►│ (Transcription) │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   Shared        │
                    │   Volumes       │
                    └─────────────────┘
```

### Service Details

**Redis Container:**
- **Purpose**: Task queue for background jobs
- **Image**: `redis:7-alpine`
- **Persistence**: Volume-mounted data
- **Health**: Built-in Redis health checks

**App Container:**
- **Purpose**: FastAPI web service + React frontend
- **Build**: From local Dockerfile
- **Ports**: 8000 (HTTP)
- **Health**: HTTP endpoint checks

**Worker Container:**
- **Purpose**: Celery worker for transcription
- **Build**: Same image as app container
- **Command**: `celery -A app.worker worker`
- **Resources**: CPU-intensive transcription tasks

## Volume Management

### Persistent Data

```yaml
volumes:
  redis_data:     # Redis persistence
  app_data:       # SQLite database
```

### Bind Mounts

```yaml
volumes:
  - ./storage:/app/storage     # Uploaded files & transcripts
  - ./models:/app/models       # Whisper model files
```

## Network Configuration

### Internal Communication

Services communicate via Docker's internal network:
- **App ↔ Redis**: `redis://redis:6379/0`
- **Worker ↔ Redis**: Same Redis connection
- **Worker ↔ Database**: Shared SQLite file

### External Access

- **Port 8000**: Web interface and API
- **All other ports**: Internal only

## Health Checks

### Application Health

```bash
# Check all services
docker-compose ps

# Detailed health status
docker inspect whisper-app | grep Health -A 10
```

### Service-specific Checks

```bash
# App service
curl http://localhost:8000/

# Redis
docker exec whisper-redis redis-cli ping

# Worker (check logs)
docker logs whisper-worker --tail=20
```

## Scaling

### Horizontal Scaling

**Multiple workers:**
```bash
docker-compose up -d --scale worker=3
```

**Load balancer (optional):**
```yaml
nginx:
  image: nginx:alpine
  volumes:
    - ./nginx.conf:/etc/nginx/nginx.conf
  ports:
    - "80:80"
```

### Resource Allocation

**CPU limits:**
```yaml
worker:
  deploy:
    resources:
      limits:
        cpus: '2.0'
        memory: 4G
```

**Memory considerations:**
- **tiny model**: ~1GB per worker
- **small model**: ~2GB per worker  
- **medium model**: ~5GB per worker
- **large-v3 model**: ~10GB per worker

## Monitoring

### Container Monitoring

```bash
# Resource usage
docker stats

# Service status
docker-compose ps

# Recent logs
docker-compose logs --tail=50 -f
```

### Application Metrics

```bash
# Job queue status
curl http://localhost:8000/jobs

# Service health
curl http://localhost:8000/
```

### Log Management

**Log locations:**
```
app logs:     docker logs whisper-app
worker logs:  docker logs whisper-worker  
redis logs:   docker logs whisper-redis
```

**Log rotation:**
```yaml
services:
  app:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

## Backup and Recovery

### Data Backup

```bash
# Backup database and uploads
docker run --rm -v whisper-transcriber_app_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/whisper-backup-$(date +%Y%m%d).tar.gz /data

# Backup uploaded files
cp -r storage/ backup-storage-$(date +%Y%m%d)/
```

### Recovery

```bash
# Restore database
docker run --rm -v whisper-transcriber_app_data:/data -v $(pwd):/backup \
  alpine tar xzf /backup/whisper-backup-20250101.tar.gz -C /

# Restore uploads
cp -r backup-storage-20250101/ storage/
```

## Updates

### Application Updates

```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Dependency Updates

```bash
# Update base images
docker-compose pull

# Rebuild application
docker-compose build --pull
```

## Troubleshooting

### Common Issues

**Port conflicts:**
```bash
# Check port usage
sudo lsof -i :8000

# Use different port
PORT=8080 docker-compose up -d
```

**Out of disk space:**
```bash
# Clean Docker artifacts
docker system prune -f

# Check model files size
du -sh models/
```

**Memory issues:**
```bash
# Reduce worker concurrency
CELERY_CONCURRENCY=1 docker-compose up -d

# Use smaller model
DEFAULT_WHISPER_MODEL=tiny
```

### Debug Mode

```bash
# Enable debug logging
LOG_LEVEL=DEBUG docker-compose up -d

# Follow all logs
docker-compose logs -f
```

## Security Considerations

### Network Security

- **Firewall**: Only expose port 8000
- **Reverse proxy**: Use nginx for HTTPS
- **Internal networks**: Services communicate internally

### Data Security

- **Local storage**: No cloud dependencies
- **File permissions**: Secure volume mounts
- **Database**: SQLite file permissions

### Production Hardening

```bash
# Remove development tools
docker-compose down
docker system prune -f

# Use production environment
ENV=production docker-compose up -d
```
