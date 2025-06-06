# ───────────────────────────────────────────────────────────────
# 1. Base image with Python and ffmpeg
FROM python:3.11-slim

# 2. System dependencies for Whisper + ffmpeg
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 3. Working directory inside container
WORKDIR /app

# 4. Copy dependency definitions
COPY requirements.txt ./

# 5. Install Python dependencies
RUN pip install --upgrade pip && pip install -r requirements.txt

# 6. Copy all project files
COPY . .

# 7. Expose FastAPI's default port
EXPOSE 8000

# 8. Run the FastAPI app via Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
