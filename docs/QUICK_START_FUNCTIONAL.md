# Quick Start - Functional Testing

This document provides exact commands to build, run, and test the whisper-transcriber application from a clean clone.

## Prerequisites

- Docker & Docker Compose
- Node.js 18+ (for e2e tests)
- Python 3.10+ (for smoke tests)
- curl (for probe script)

## Quick Start Commands

### 1. Clone and Setup
```bash
git clone <repo-url> whisper-transcriber
cd whisper-transcriber
```

### 2. Build and Run
```bash
# Build services
docker-compose build

# Start services
docker-compose up -d

# Wait for services to be ready (15-30 seconds)
sleep 20

# Verify services are running
docker-compose ps
```

### 3. Run Functional Tests

#### Cold Build Probe (Shell Script)
```bash
# Run comprehensive build and deployment probe
./scripts/cold_build_probe.sh
```

#### Smoke Tests (Python/pytest)
```bash
# Install test dependencies (if needed)
pip install pytest requests

# Run smoke tests
python -m pytest tests/test_smoke_functional.py -v

# Run specific test categories
python -m pytest tests/test_smoke_functional.py::TestAPIHealth -v
python -m pytest tests/test_smoke_functional.py::TestStaticAssets -v
```

#### E2E Tests (Playwright)
```bash
# Setup Playwright (one-time)
cd playwright
npm install
npx playwright install

# Run e2e tests
npm test

# Run with browser visible
npm run test:headed

# Debug mode
npm run test:debug
```

### 4. Manual Verification

#### API Health
```bash
curl http://localhost:8000/health
```

#### Static Assets
```bash
curl http://localhost:8000/static/index.html
curl http://localhost:8000/
```

#### SPA Routes
```bash
curl -I http://localhost:8000/dashboard
curl -I http://localhost:8000/login
```

#### Container Structure
```bash
# Check static files
docker exec whisper-transcriber-api-1 ls -la /app/api/static/

# Check models
docker exec whisper-transcriber-api-1 ls -la /app/models/

# Check migrations
docker exec whisper-transcriber-api-1 ls -la /app/api/migrations/versions/
```

### 5. Cleanup
```bash
# Stop and remove containers
docker-compose down -v

# Remove images (optional)
docker system prune -f
```

## Test Coverage

### Cold Build Probe (`scripts/cold_build_probe.sh`)
- ✅ Docker build and container startup
- ✅ API health endpoint accessibility
- ✅ Static asset serving
- ✅ Container file structure verification
- ✅ Basic authentication endpoint testing
- ✅ Database connectivity through API

### Smoke Tests (`tests/test_smoke_functional.py`)
- ✅ API health and documentation
- ✅ Static asset serving and SPA routing
- ✅ Database connectivity
- ✅ Authentication flow (registration/login)
- ✅ File upload endpoint availability
- ✅ Container structure verification
- ✅ Worker service accessibility
- ✅ Complete user flows (registration → login → protected access)

### E2E Tests (`playwright/logout_flow.spec.ts`)
- ✅ SPA loading and navigation
- ✅ Route handling and fallbacks
- ✅ User registration flow
- ✅ Login/logout flow with state management
- ✅ Protected route access control
- ✅ File upload interface
- ✅ Browser navigation (back/forward)
- ✅ Static asset loading verification

## Troubleshooting

### Services Won't Start
```bash
# Check logs
docker-compose logs

# Check specific service
docker-compose logs api
docker-compose logs worker
docker-compose logs db
```

### Tests Fail
```bash
# Check if services are running
curl http://localhost:8000/health

# Check container status
docker-compose ps

# Restart services
docker-compose restart
```

### Port Conflicts
```bash
# Check what's using port 8000
lsof -i :8000

# Use different ports (edit docker-compose.yml)
# Or stop conflicting services
```

## Expected Results

All tests should pass with a properly configured and built application. The key indicators of success:

- ✅ API health endpoint returns 200
- ✅ Static assets (CSS, JS, images) load correctly
- ✅ SPA routes serve index.html (not 404)
- ✅ Database connectivity works
- ✅ Authentication endpoints respond appropriately
- ✅ All required directories exist in containers
- ✅ Model files are present and accessible
- ✅ Migrations run successfully

If any test fails, check the specific error message and refer to the troubleshooting section above.
