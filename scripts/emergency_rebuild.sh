#!/bin/bash

echo "🚨 EMERGENCY FRONTEND REBUILD"
echo "Stopping containers..."
docker compose down

echo "Removing frontend build cache..."
rm -rf frontend/dist/
rm -rf frontend/node_modules/.vite/

echo "Rebuilding containers with no cache..."
docker compose build --no-cache app

echo "Starting services..."
docker compose up -d

echo "Waiting for services to start..."
sleep 10

echo "Testing frontend..."
curl -s http://localhost:8000/ | head -5

echo "✅ Emergency rebuild complete"
echo "Try http://localhost:8000 in a new incognito window"