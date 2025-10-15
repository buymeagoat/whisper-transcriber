# Troubleshooting Guide

Common issues and solutions for the Whisper Transcriber application.

## Installation Issues

### Docker Problems

**Error: Cannot connect to Docker daemon**
```bash
# Start Docker service
sudo systemctl start docker

# Add user to docker group
sudo usermod -aG docker $USER
# Log out and log back in
```

**Error: Docker Compose not found**
```bash
# Install Docker Compose plugin
sudo apt install docker-compose-plugin

# Or use standalone version
sudo apt install docker-compose
```

### Model Download Issues

**Error: Models not found**
```bash
# Verify models directory
ls -la models/
# Should contain: base.pt, small.pt, medium.pt, large-v3.pt, tiny.pt

# Download missing models
wget https://openaipublic.azureedge.net/main/whisper/models/tiny.pt -O models/tiny.pt
```

**Error: Insufficient disk space**
```bash
# Check available space
df -h

# Models require ~5GB total space
# Large-v3 model alone is ~2.9GB
```

## Runtime Issues

### Application Won't Start

**Error: Port 8000 already in use**
```bash
# Check what's using port 8000
sudo lsof -i :8000

# Kill the process or use different port
PORT=8080 docker-compose up -d
```

**Error: Redis connection failed**
```bash
# Check Redis container status
docker ps | grep redis

# Check Redis logs
docker logs whisper-redis

# Restart Redis
docker-compose restart redis
```

### Upload Issues

**Error: File too large**
```bash
# Increase upload limit in .env
MAX_FILE_SIZE_MB=200

# Restart application
docker-compose restart app worker
```

**Error: Unsupported file format**
```bash
# Check supported formats
ALLOWED_AUDIO_FORMATS=mp3,wav,m4a,flac,ogg,aac

# Convert file format
ffmpeg -i input.mp4 -acodec mp3 output.mp3
```

### Transcription Issues

**Error: Transcription stuck in "processing"**
```bash
# Check worker logs
docker logs whisper-worker

# Check worker status
docker ps | grep worker

# Restart worker
docker-compose restart worker
```

**Error: Transcription failed**
```bash
# Check file is valid audio
ffprobe your-audio-file.mp3

# Check available models
ls -la models/

# Try different model
# Use "tiny" for fastest processing
# Use "small" for good balance
```

### Performance Issues

**Slow transcription**
```bash
# Increase worker concurrency (match CPU cores)
CELERY_CONCURRENCY=4

# Use smaller model for speed
DEFAULT_WHISPER_MODEL=tiny

# Check system resources
docker stats
```

**High memory usage**
```bash
# Reduce concurrency
CELERY_CONCURRENCY=1

# Use smaller model
DEFAULT_WHISPER_MODEL=tiny

# Check memory per worker:
# tiny: ~1GB, small: ~2GB, medium: ~5GB, large-v3: ~10GB
```

## Web Interface Issues

### Can't Access Application

**Error: This site can't be reached**
```bash
# Check application is running
docker ps

# Check logs
docker logs whisper-app

# Verify port mapping
curl http://localhost:8000
```

**Error: 404 Not Found**
```bash
# Check web assets are built
docker exec whisper-app ls -la /app/web/dist/

# Rebuild if missing
docker-compose build app
```

### Upload Not Working

**Error: Network error**
```bash
# Check browser console for errors
# Open Developer Tools > Console

# Verify API is accessible
curl -X POST http://localhost:8000/api/health
```

**Error: Progress not updating**
```bash
# Check WebSocket connection
# Look for WebSocket errors in browser console

# Verify Redis is working
docker logs whisper-redis
```

## Database Issues

### SQLite Problems

**Error: Database is locked**
```bash
# Stop all containers
docker-compose down

# Remove lock file if exists
rm -f app.db-wal app.db-shm

# Restart
docker-compose up -d
```

**Error: Database file not found**
```bash
# Check database volume
docker volume ls | grep whisper

# Recreate database
docker-compose down -v
docker-compose up -d
```

## Logging and Debugging

### Enable Debug Logging

```bash
# Add to .env file
LOG_LEVEL=DEBUG
LOG_TO_STDOUT=true

# Restart application
docker-compose restart
```

### Check Application Health

```bash
# Health check endpoint
curl http://localhost:8000/health

# Check all services
docker-compose ps

# View logs
docker-compose logs -f
```

### Useful Commands

```bash
# View all logs
docker-compose logs

# Follow logs in real-time
docker-compose logs -f

# Check specific service
docker logs whisper-app
docker logs whisper-worker
docker logs whisper-redis

# Check resource usage
docker stats

# Execute command in container
docker exec -it whisper-app bash
```

## Getting Help

### Check Application Status

1. **Service Status**: `docker-compose ps`
2. **Application Health**: `curl http://localhost:8000/health`
3. **Recent Logs**: `docker-compose logs --tail=50`

### Before Reporting Issues

1. **Check logs** for error messages
2. **Verify system requirements** (Docker, disk space, memory)
3. **Test with minimal configuration** (default settings)
4. **Try restarting** the application

### Reporting Issues

Include this information:

1. **Error message** from logs
2. **Steps to reproduce** the problem
3. **System information** (OS, Docker version)
4. **Configuration** (relevant environment variables)
5. **File details** (format, size) if upload-related
