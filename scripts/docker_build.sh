#!/usr/bin/env bash
set -euo pipefail

# Remove existing containers, images and volumes to start fresh
docker compose down -v --remove-orphans || true
docker system prune -af --volumes

# Update the repo
git fetch
git pull

# Install Python dependencies
pip install -r requirements.txt

# Install and build the frontend
cd frontend
npm install
npm run build
cd ..

# Verify Whisper model files exist
MODELS=(base.pt small.pt medium.pt large-v3.pt tiny.pt)
for m in "${MODELS[@]}"; do
    if [ ! -f "models/$m" ]; then
        echo "Missing models/$m. Populate the models/ directory before building." >&2
        exit 1
    fi
done

# Ensure .env with SECRET_KEY
if [ ! -f ".env" ]; then
    cp .env.example .env
fi

SECRET_KEY=$(grep -E '^SECRET_KEY=' .env | cut -d= -f2-)
if [ -z "$SECRET_KEY" ] || [ "$SECRET_KEY" = "CHANGE_ME" ]; then
    SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
    sed -i "s/^SECRET_KEY=.*/SECRET_KEY=$SECRET_KEY/" .env
    echo "Generated SECRET_KEY saved in .env"
fi

# Build the Docker image using the secret key
docker build --build-arg SECRET_KEY="$SECRET_KEY" -t whisper-app .

# Start the compose stack
docker compose up --build api worker broker db

