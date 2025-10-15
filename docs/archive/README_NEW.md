# 🎙️ Whisper Transcriber

**Modern, Mobile-First Audio Transcription Service**

Transform your audio files into accurate text with a beautiful, responsive interface that works seamlessly on desktop and mobile devices.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Docker](https://img.shields.io/badge/docker-ready-blue.svg)
![Mobile](https://img.shields.io/badge/mobile-optimized-green.svg)
![PWA](https://img.shields.io/badge/PWA-enabled-purple.svg)

## ✨ Features

### 🚀 Core Functionality
- **High-Accuracy Transcription** powered by OpenAI Whisper
- **Multiple Model Options** (tiny, small, medium, large-v3) for speed/quality balance
- **Real-time Progress** with WebSocket updates
- **Multiple Audio Formats** (MP3, WAV, M4A, FLAC, OGG)

### 📱 Mobile-First Design
- **Progressive Web App** (PWA) with offline capabilities
- **Responsive Interface** that adapts to any screen size
- **Touch-Optimized** drag-and-drop upload
- **Mobile Gestures** for intuitive navigation

### 🏠 Home Server Ready
- **Simple Deployment** with Docker Compose
- **SQLite Database** for easy maintenance
- **Local Storage** - no cloud dependencies
- **Lightweight Architecture** perfect for Raspberry Pi

### 🎯 User Experience
- **Zero Learning Curve** - intuitive interface
- **Instant Results** - view transcripts immediately
- **Smart History** - manage past transcriptions
- **Share & Export** - multiple download formats

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- 2GB+ RAM (4GB recommended for large models)
- 10GB+ storage for models and transcripts

### 1. Clone and Start
```bash
git clone https://github.com/yourusername/whisper-transcriber.git
cd whisper-transcriber

# Start all services
docker-compose up -d

# Check status
docker-compose ps
```

### 2. Access the Application
- **Web Interface**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### 3. First Upload
1. Visit the web interface
2. Choose your model (start with "Small" for balanced speed/quality)
3. Drag & drop an audio file or click to upload
4. Watch real-time progress
5. Download your transcript!

## 🏗️ Architecture

### Streamlined Stack
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React PWA     │    │   FastAPI       │    │   Redis         │
│   (Frontend)    │◄──►│   (Backend)     │◄──►│   (Queue)       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                       ┌─────────────────┐    ┌─────────────────┐
                       │   SQLite        │    │   Celery        │
                       │   (Database)    │    │   (Worker)      │
                       └─────────────────┘    └─────────────────┘
```

### API Endpoints
```
POST /transcribe          # Upload audio file
GET  /jobs/{id}          # Check job status  
GET  /jobs/{id}/download # Download transcript
GET  /jobs               # List recent jobs
WS   /ws/jobs/{id}       # Real-time progress
```

## 📱 Mobile Experience

### PWA Features
- **Add to Home Screen** for app-like experience
- **Offline Support** for viewing history
- **Background Sync** when connection returns
- **Push Notifications** for job completion

### Mobile Optimizations
- **Large Touch Targets** (44px+) for easy interaction
- **Gesture Navigation** with swipe support
- **Adaptive UI** that responds to device orientation
- **Camera Integration** for direct audio recording

## 🔧 Configuration

### Environment Variables
```bash
# Database
DATABASE_URL=sqlite:///app/data/app.db

# Redis
REDIS_URL=redis://redis:6379/0

# Whisper Models
WHISPER_MODEL_DIR=/app/models

# Server
PORT=8000
```

### Model Configuration
The application supports multiple Whisper models:

| Model | Size | Speed | Quality | Use Case |
|-------|------|-------|---------|----------|
| tiny | 39MB | Fastest | Basic | Quick drafts |
| small | 244MB | Fast | Good | General use |
| medium | 769MB | Balanced | Better | Professional |
| large-v3 | 1550MB | Slow | Best | High accuracy |

## 🛠️ Development

### Local Development
```bash
# Backend
cd app
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend  
cd web
npm install
npm run dev

# Worker
celery -A worker worker --loglevel=info
```

### File Structure
```
whisper-transcriber/
├── app/                    # Backend (FastAPI)
│   ├── main.py            # Main application
│   ├── worker.py          # Celery worker
│   └── requirements.txt   # Python dependencies
├── web/                   # Frontend (React)
│   ├── src/
│   │   ├── components/    # React components
│   │   └── App.jsx       # Main app
│   └── package.json      # Node dependencies
├── storage/              # Local file storage
│   ├── uploads/          # Temporary audio files
│   └── transcripts/      # Output files
├── docker-compose.yml    # Production deployment
└── README.md            # This file
```

## 🚀 Deployment

### Production Setup
```bash
# Clone repository
git clone https://github.com/yourusername/whisper-transcriber.git
cd whisper-transcriber

# Create production environment
cp .env.example .env
# Edit .env with your settings

# Start with SSL (optional)
docker-compose --profile production up -d

# Without SSL
docker-compose up -d
```

### Raspberry Pi Deployment
The application works great on Raspberry Pi 4+ with 4GB+ RAM:

```bash
# Optimize for Pi
echo "WHISPER_MODEL=small" >> .env
echo "CELERY_CONCURRENCY=1" >> .env

# Start services
docker-compose up -d
```

## 📊 Monitoring

### Health Checks
- **Application**: http://localhost:8000/
- **Redis**: `docker-compose exec redis redis-cli ping`
- **Worker**: `docker-compose logs worker`

### Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f app
docker-compose logs -f worker
```

## 🔮 Future Enhancements

### AI Integration Ready
The architecture is designed for easy AI integration:

```python
# Plugin system for AI analysis
class AIPlugin:
    def analyze(self, transcript: str) -> dict:
        pass

# Webhook support for external AI services
@app.post("/webhooks/ai-analysis")
async def ai_webhook(data: dict):
    pass
```

### Planned Features
- 🤖 **AI Summary Generation**
- 🔍 **Smart Search** across transcripts
- 🏷️ **Auto-tagging** and categorization
- 📧 **Email Integration** for results
- 🌐 **Multi-language** support
- 📊 **Analytics Dashboard**

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **OpenAI Whisper** for the amazing transcription models
- **FastAPI** for the excellent web framework
- **React** for the powerful frontend library
- **Tailwind CSS** for beautiful styling
- **Docker** for simplified deployment

## 📞 Support

- 📚 **Documentation**: [Full docs](docs/)
- 🐛 **Issues**: [GitHub Issues](https://github.com/yourusername/whisper-transcriber/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/yourusername/whisper-transcriber/discussions)
- 📧 **Email**: support@whisper-transcriber.com

---

<p align="center">
  <strong>Built with ❤️ for modern transcription needs</strong>
</p>
