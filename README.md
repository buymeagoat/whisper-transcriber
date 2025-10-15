# Whisper Transcriber

> **Streamlined, mobile-first transcription service built for home servers.**
> **For detailed setup, see [docs/streamlined/SETUP_GUIDE.md](docs/streamlined/SETUP_GUIDE.md).**

Modern self-hosted transcription service with a **FastAPI backend** and **React PWA frontend**. Upload audio files and get transcripts instantly with a beautiful, mobile-optimized interface.

**✨ Key Features:**
- 📱 **Mobile-first PWA** with offline capabilities
- 🎯 **Drag-and-drop uploads** with real-time progress
- 🔄 **Background processing** with Celery workers
- 🗃️ **SQLite database** for simplicity
- 🐳 **Docker Compose** deployment

## Quick Start

### Prerequisites
- **Docker & Docker Compose**
- **Whisper model files** in `models/` directory

### Installation
```bash
# 1. Clone repository
git clone https://github.com/buymeagoat/whisper-transcriber.git
cd whisper-transcriber

# 2. Download Whisper models (required)
# Place base.pt, small.pt, medium.pt, large-v3.pt, tiny.pt in models/

# 3. Start with Docker Compose
docker-compose up -d

# 4. Access the application
# http://localhost:8000
```

The application uses **SQLite** for data storage and **Redis** for task queue management.

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React PWA     │    │   FastAPI       │    │   Celery        │
│   (Mobile UI)   ├────┤   (Backend)     ├────┤   (Worker)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   SQLite +      │
                    │   Redis         │
                    └─────────────────┘
```

## Documentation

- **[Setup Guide](docs/streamlined/SETUP_GUIDE.md)** - Complete installation instructions
- **[Transformation Summary](docs/streamlined/TRANSFORMATION_SUMMARY.md)** - What changed
- **[Architecture Overview](docs/streamlined/RESTRUCTURE_PLAN.md)** - Technical details

## Contributing

This repository follows modern development practices:
- **Mobile-first design** with React PWA
- **Streamlined architecture** (12 dependencies vs 67 legacy)
- **Docker-first deployment** with health checks
- **SQLite for simplicity** (no complex DB setup)

## License

