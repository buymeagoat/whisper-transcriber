# 🚀 Setup Guide - Whisper Transcriber

Welcome to your streamlined, mobile-first transcription service! This guide will get you up and running in minutes.

## 🎯 What You're Building

A modern transcription service with:
- **Beautiful mobile-first interface** that works on phones, tablets, and desktops
- **Drag-and-drop upload** with real-time progress
- **Multiple Whisper models** for different speed/quality needs
- **Home server deployment** perfect for personal use
- **Future AI integration** ready for your next features

## 📋 Prerequisites

### Hardware Requirements
- **Minimum**: 2GB RAM, 10GB storage
- **Recommended**: 4GB+ RAM, 20GB+ storage
- **CPU**: Any modern x64 processor (ARM64 supported)
- **Network**: Internet for initial model downloads

### Software Requirements
```bash
# Install Docker and Docker Compose
# Ubuntu/Debian:
sudo apt update
sudo apt install docker.io docker-compose-plugin

# macOS:
brew install docker docker-compose

# Verify installation
docker --version
docker compose version
```

## 🏗️ Installation

### Step 1: Clone and Prepare
```bash
# Clone the repository
git clone https://github.com/yourusername/whisper-transcriber.git
cd whisper-transcriber

# Create environment file
cp .env.streamlined .env

# Create necessary directories
mkdir -p storage/uploads storage/transcripts models
```

### Step 2: Configure Environment
Edit `.env` to customize your installation:

```bash
# Basic configuration (required)
SECRET_KEY=$(openssl rand -hex 32)  # Generate secure key
PORT=8000

# Model selection (choose based on your hardware)
DEFAULT_MODEL=small  # Options: tiny, small, medium, large-v3

# Resource limits (adjust for your system)
CELERY_CONCURRENCY=2    # Number of CPU cores for transcription
MAX_FILE_SIZE=104857600 # 100MB max upload
```

### Step 3: Launch Services
```bash
# Start all services in background
docker compose up -d

# Check status
docker compose ps

# View logs (optional)
docker compose logs -f app
```

### Step 4: Verify Installation
```bash
# Test API health
curl http://localhost:8000/

# Expected response:
{
  "service": "Whisper Transcriber",
  "version": "2.0.0", 
  "status": "online"
}
```

## 🎨 First Use

### Web Interface
1. **Open your browser**: http://localhost:8000
2. **Choose a model**: Start with "Small" for balanced performance
3. **Upload audio**: Drag and drop or click to select
4. **Watch progress**: Real-time updates via WebSocket
5. **Download transcript**: Multiple formats available

### Mobile Setup
1. **Visit on mobile**: http://your-server-ip:8000
2. **Add to home screen**: Use browser's "Add to Home Screen" 
3. **Enjoy native app feel**: PWA with offline capabilities

## 🔧 Configuration Options

### Model Selection Guide
```bash
# Tiny - Ultra fast, basic quality (39MB)
DEFAULT_MODEL=tiny      # Good for: Quick tests, voice memos

# Small - Fast, good quality (244MB) 
DEFAULT_MODEL=small     # Good for: General use, meetings

# Medium - Balanced (769MB)
DEFAULT_MODEL=medium    # Good for: Professional transcripts

# Large - Best quality, slower (1550MB)
DEFAULT_MODEL=large-v3  # Good for: Critical accuracy needs
```

### Performance Tuning
```bash
# CPU optimization
CELERY_CONCURRENCY=4    # Match your CPU cores

# Memory optimization  
MAX_FILE_SIZE=52428800  # 50MB for lower memory usage

# Storage optimization
AUTO_CLEANUP=true       # Delete files after transcription
```

### Security Options
```bash
# Enable authentication (optional)
ENABLE_AUTH=true
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-secure-password

# CORS for custom domains
CORS_ORIGINS=https://yourdomain.com,https://transcribe.yourdomain.com
```

## 🌐 External Access

### Local Network Access
```bash
# Find your server IP
ip addr show | grep inet

# Update .env for network access
CORS_ORIGINS=http://192.168.1.100:8000  # Replace with your IP

# Restart services
docker compose restart
```

### Domain Setup (Optional)
```bash
# With reverse proxy (Nginx example)
server {
    listen 80;
    server_name transcribe.yourdomain.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    # WebSocket support
    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## 📱 Mobile Optimization

### PWA Installation
1. **Chrome/Edge**: Menu → "Install app" or "Add to home screen"
2. **Safari**: Share → "Add to Home Screen"
3. **Firefox**: Menu → "Install" 

### Mobile Features
- **Offline transcript viewing**: Previously downloaded transcripts work offline
- **Background uploads**: Start upload, switch apps, get notification when done
- **Touch gestures**: Swipe, pinch, tap optimized for mobile use
- **Voice recording**: Direct audio capture (browser dependent)

## 🔍 Monitoring & Maintenance

### Health Checks
```bash
# Application status
curl http://localhost:8000/

# Service status
docker compose ps

# Resource usage
docker stats

# Disk usage
du -h storage/
```

### Log Management
```bash
# View live logs
docker compose logs -f

# Specific service logs
docker compose logs app
docker compose logs worker
docker compose logs redis

# Save logs to file
docker compose logs > transcriber-logs.txt
```

### Backup & Restore
```bash
# Backup transcripts and database
tar -czf backup-$(date +%Y%m%d).tar.gz storage/ app.db

# Restore from backup
tar -xzf backup-20241010.tar.gz
```

## 🚨 Troubleshooting

### Common Issues

**Issue**: "Connection refused" error
```bash
# Check if services are running
docker compose ps

# Restart services
docker compose restart

# Check port availability
netstat -tulpn | grep 8000
```

**Issue**: "Out of memory" during transcription
```bash
# Use smaller model
DEFAULT_MODEL=tiny

# Reduce concurrency
CELERY_CONCURRENCY=1

# Restart services
docker compose restart
```

**Issue**: Upload failures
```bash
# Check file size
MAX_FILE_SIZE=52428800  # Reduce to 50MB

# Check available disk space
df -h

# Check supported formats
# Supported: mp3, wav, m4a, flac, ogg, wma
```

**Issue**: Slow transcription
```bash
# Check CPU usage during transcription
top -p $(pgrep -f celery)

# Consider hardware upgrade for larger models
# Use GPU acceleration (future feature)
```

### Reset Installation
```bash
# Stop services
docker compose down

# Remove containers and volumes (WARNING: destroys data)
docker compose down -v

# Remove images
docker system prune -a

# Start fresh
docker compose up -d
```

## 📈 Scaling & Performance

### Resource Monitoring
```bash
# Monitor during transcription
docker stats

# Expected resource usage:
# tiny model:   ~500MB RAM
# small model:  ~1GB RAM  
# medium model: ~2GB RAM
# large model:  ~4GB RAM
```

### Performance Optimization
```bash
# Multiple workers for high volume
CELERY_CONCURRENCY=4

# SSD storage for better I/O
# Move storage/ to SSD mount

# Dedicated GPU (future enhancement)
# Will dramatically improve speed
```

## 🔮 Next Steps

### Customization Ideas
1. **Custom branding**: Update web/src/App.jsx with your logo/colors
2. **Additional formats**: Add SRT subtitle export
3. **Webhooks**: Integrate with other services
4. **User management**: Multi-user support
5. **Analytics**: Usage statistics dashboard

### AI Integration Preparation
The architecture is ready for AI features:
```python
# Example: Add AI summary endpoint
@app.post("/ai/summarize")
async def ai_summarize(transcript: str):
    # Your AI integration here
    return {"summary": ai_summary}
```

## 💬 Community & Support

- **Documentation**: Full docs in `docs/` directory
- **Issues**: Report problems via GitHub Issues
- **Discussions**: Feature requests and community chat
- **Updates**: Watch repository for new releases

---

**🎉 Congratulations!** You now have a modern, mobile-first transcription service running on your home server. Upload an audio file and watch the magic happen!

Need help? Check the troubleshooting section above or create an issue on GitHub.
