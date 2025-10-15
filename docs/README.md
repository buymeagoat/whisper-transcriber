# Documentation

Welcome to the Whisper Transcriber documentation! This guide will help you install, configure, and use the streamlined transcription service.

## 🚀 Quick Start

New to Whisper Transcriber? Start here:

1. **[Installation Guide](user-guide/installation.md)** - Get up and running quickly
2. **[Getting Started](user-guide/getting-started.md)** - Your first transcription
3. **[Configuration](user-guide/configuration.md)** - Customize for your needs

## 📚 Documentation Sections

### 👥 User Guide
Perfect for end users who want to use the transcription service.

- **[Installation](user-guide/installation.md)** - Complete setup instructions
- **[Getting Started](user-guide/getting-started.md)** - Quick start tutorial  
- **[Configuration](user-guide/configuration.md)** - Environment variables and settings
- **[Troubleshooting](user-guide/troubleshooting.md)** - Common issues and solutions

### 💻 Developer Guide  
Technical documentation for developers and contributors.

- **[Architecture](developer-guide/architecture.md)** - Technical architecture and design
- **[API Reference](developer-guide/api-reference.md)** - Complete API documentation
- **[Contributing](developer-guide/contributing.md)** - Development workflow and guidelines
- **[Versioning](developer-guide/versioning.md)** - Release and versioning policy

### 🚀 Deployment Guide
Operations and deployment documentation for system administrators.

- **[Docker Deployment](deployment/docker.md)** - Docker and Docker Compose setup
- **[Production Deployment](deployment/production.md)** - Production environment setup
- **[Performance Optimization](deployment/performance.md)** - Performance tuning and scaling
- **[Monitoring](deployment/monitoring.md)** - Health checks and observability

## 🎯 What's Whisper Transcriber?

Whisper Transcriber is a **streamlined, mobile-first audio transcription service** designed for home servers and personal use.

### ✨ Key Features

- **📱 Mobile-First Design** - Touch-optimized interface that works great on phones
- **🎯 Drag-and-Drop Upload** - Simply drag audio files to start transcription
- **⚡ Real-Time Progress** - Watch transcription progress with live updates
- **🏠 Privacy-Focused** - Everything runs locally, no cloud services required
- **🐳 Easy Deployment** - One-command Docker Compose setup
- **🔄 Background Processing** - Upload and let it work while you do other things

### 🏗️ Architecture Overview

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

**Simple 3-service architecture:**
- **Web App**: React PWA frontend + FastAPI backend
- **Worker**: Celery background transcription processing  
- **Redis**: Task queue for job management

## 📖 Additional Resources

### Community & Support

- **[Contributing Guidelines](../CONTRIBUTING.md)** - How to contribute to the project
- **[Security Policy](../SECURITY.md)** - Security reporting and best practices
- **[Changelog](../CHANGELOG.md)** - Version history and changes
- **[License](../LICENSE)** - MIT License details

### Quick Links

- **GitHub Repository**: [buymeagoat/whisper-transcriber](https://github.com/buymeagoat/whisper-transcriber)
- **Issue Tracker**: Report bugs and request features
- **Discussions**: Ask questions and share ideas

## 🆘 Need Help?

### Common Questions

1. **Installation Issues**: Check [troubleshooting guide](user-guide/troubleshooting.md)
2. **Performance Problems**: See [performance optimization](deployment/performance.md)
3. **API Questions**: Refer to [API reference](developer-guide/api-reference.md)
4. **Development Setup**: Follow [contributing guide](developer-guide/contributing.md)

### Getting Support

1. **Check documentation** - Most questions are answered here
2. **Search existing issues** - Someone may have asked before
3. **Create an issue** - For bugs or feature requests
4. **Start a discussion** - For general questions

## 🎉 What's New in 2.0?

Version 2.0 represents a complete rewrite focused on simplicity and mobile-first design:

### Major Improvements
- **🏗️ Simplified Architecture** - SQLite + Redis instead of PostgreSQL + RabbitMQ
- **📱 Mobile-First UI** - React PWA with touch-optimized interface
- **⚡ Performance** - 82% fewer dependencies, faster startup
- **🏠 Home Server Focus** - Optimized for personal use and Raspberry Pi

### What Changed
- **Streamlined from 67 to 12 dependencies**
- **6 core API endpoints** instead of 15+ complex ones
- **Modern React PWA** instead of traditional web app
- **Docker Compose** for simple deployment

See the [changelog](../CHANGELOG.md) for complete details.

---

**Ready to get started?** Head to the [installation guide](user-guide/installation.md) and have your transcription service running in minutes! 🚀
