# Whisper Transcriber - Production

A production-ready audio transcription service using OpenAI Whisper.

## Quick Start

1. **Set up environment variables:**
   ```bash
   cp env.template .env
   # Edit .env with your production values
   ```

2. **Build and run with Docker:**
   ```bash
   docker-compose up --build
   ```

3. **Access the application:**
   - Web Interface: http://localhost:8001
   - API Documentation: http://localhost:8001/docs

## Configuration

Required environment variables in `.env`:
- `SECRET_KEY` - Application secret key
- `JWT_SECRET_KEY` - JWT token signing key  
- `REDIS_PASSWORD` - Redis authentication password

## Production Deployment

The application runs as three Docker containers:
- **app** - FastAPI backend + React frontend (port 8001)
- **worker** - Celery worker for transcription tasks
- **redis** - Task queue and cache

## API Usage

Upload audio files via the web interface or API:
```bash
curl -X POST -F "file=@audio.wav" http://localhost:8001/upload
```

## Supported Audio Formats

- WAV, MP3, M4A, FLAC
- Maximum file size: 100MB

## Models

Available Whisper models:
- tiny, small, medium, large, large-v3

Default model: small (best balance of speed/accuracy)