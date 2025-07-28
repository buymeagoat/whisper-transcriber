# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-07-28
### Added
- Build helper scripts with offline support and environment validation
- Security enhancements for secret handling and authentication

### Changed
- Documentation updates for external users and troubleshooting
- Improved Docker build reliability

### Fixed
- Various script errors and dependency checks

## [0.6.0] - 2025-07-20
### Added
- Start and build scripts for Docker images
- Diagnostics for container health and image caching
- Option to verify or stage dependencies before builds

### Changed
- Offline asset checks and caching improvements
- Updated test scripts with container checks

### Fixed
- Node installation and caching issues

## [0.5.0] - 2025-07-10
### Added
- Cleanup tasks and configuration API
- Admin user management and settings page
- Concurrency controls with Celery worker integration
- Job status WebSocket and frontend components

### Changed
- Improved error handling and health checks

### Fixed
- File path sanitization and log retrieval security

## [0.4.0] - 2025-07-01
### Added
- JWT authentication with role-based access
- Metrics endpoint and system log streaming
- Docker Compose setup for PostgreSQL and RabbitMQ

### Changed
- Storage abstraction for local and S3 backends
- Job queue refactor with concurrency management

### Fixed
- Database bootstrap and migration issues

## [0.3.0] - 2025-06-24
### Added
- Pydantic response schemas and model validation
- Celery job queue and cloud storage support
- WebSocket progress updates and admin controls

### Changed
- API routes organized into modules
- Dockerfile optimized for model checks

### Fixed
- Whisper binary detection and missing uploads cleanup

## [0.2.0] - 2025-06-18
### Added
- Metadata retrieval route and frontend configuration via environment
- Logging improvements and upload page UX updates
- Database path override and configuration options

### Changed
- Replaced print statements with structured logging

### Fixed
- Obsolete tests and duplicate database setup

## [0.1.0] - 2025-06-05
### Added
- Initial project structure with FastAPI backend and React frontend
- Basic audio upload and transcription pipeline

