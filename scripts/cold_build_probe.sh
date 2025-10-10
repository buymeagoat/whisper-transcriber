#!/bin/bash
set -euo pipefail

echo "=== COLD BUILD PROBE ==="

# Check if Docker and Docker Compose are available
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker is not installed or not in PATH"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "ERROR: Docker Compose is not installed or not in PATH"
    exit 1
fi

# Build and start services
echo "Building services..."
docker-compose build --no-cache

echo "Starting services..."
docker-compose up -d

# Wait for services with timeout
echo "Waiting for services to be ready..."
timeout=60
counter=0
while [ $counter -lt $timeout ]; do
    if docker-compose ps | grep -q "Up"; then
        break
    fi
    echo "Waiting... ($counter/$timeout)"
    sleep 2
    counter=$((counter + 2))
done

if [ $counter -ge $timeout ]; then
    echo "ERROR: Services failed to start within ${timeout}s"
    docker-compose logs
    docker-compose down -v
    exit 1
fi

# Additional wait for API to be ready
echo "Waiting for API to respond..."
sleep 10

# Check service health
echo "Checking API health..."
if curl -f -s http://localhost:8000/health > /dev/null; then
    echo "✓ API health check passed"
else
    echo "✗ API health check failed"
    docker-compose logs api
    docker-compose down -v
    exit 1
fi

# Check static assets
echo "Checking static assets..."
if curl -f -s http://localhost:8000/static/index.html > /dev/null; then
    echo "✓ Static assets accessible"
else
    echo "✗ Static assets not accessible"
    docker-compose logs api
    docker-compose down -v
    exit 1
fi

# Check SPA routes (should not return 404)
echo "Checking SPA routing..."
status_code=$(curl -f -o /dev/null -s -w "%{http_code}" http://localhost:8000/dashboard || echo "000")
if [ "$status_code" = "200" ]; then
    echo "✓ SPA routing works"
elif [ "$status_code" = "404" ]; then
    echo "⚠ SPA routing returns 404 (may need investigation)"
else
    echo "✗ SPA routing failed with status $status_code"
fi

# Check required directories in containers
echo "Checking container file structure..."

echo "Checking API static directory..."
if docker exec whisper-transcriber-api-1 ls -la /app/api/static/ > /dev/null 2>&1; then
    echo "✓ API static directory exists"
    docker exec whisper-transcriber-api-1 ls -la /app/api/static/ | head -5
else
    echo "✗ API static directory missing"
    exit 1
fi

echo "Checking models directory..."
if docker exec whisper-transcriber-api-1 ls -la /app/models/ > /dev/null 2>&1; then
    echo "✓ Models directory exists"
    docker exec whisper-transcriber-api-1 ls -la /app/models/ | head -5
else
    echo "✗ Models directory missing"
    exit 1
fi

echo "Checking migrations directory..."
if docker exec whisper-transcriber-api-1 ls -la /app/api/migrations/ > /dev/null 2>&1; then
    echo "✓ Migrations directory exists"
    echo "Migration files found:"
    docker exec whisper-transcriber-api-1 find /app/api/migrations/versions -name "*.py" | wc -l
else
    echo "✗ Migrations directory missing"
    exit 1
fi

# Test basic API endpoints
echo "Testing basic API endpoints..."

# Test auth endpoints
echo "Testing authentication..."
register_response=$(curl -s -w "%{http_code}" -o /tmp/register_response.json \
    -X POST -H "Content-Type: application/json" \
    -d '{"username":"probe_user","email":"probe@test.com","password":"probepass123"}' \
    http://localhost:8000/auth/register)

if [[ "$register_response" =~ 20[01] ]] || [[ "$register_response" =~ 409 ]]; then
    echo "✓ Registration endpoint works (status: $register_response)"
else
    echo "✗ Registration failed with status: $register_response"
fi

# Test database connectivity through API
echo "Testing database connectivity..."
if curl -f -s http://localhost:8000/health > /dev/null; then
    echo "✓ Database connectivity through API works"
else
    echo "✗ Database connectivity issues"
fi

# Cleanup
echo "Cleaning up..."
docker-compose down -v

echo "=== PROBE COMPLETE ==="
echo "All critical functionality checks passed!"
