FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
      ffmpeg git && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY api         ./api
RUN mkdir -p uploads transcripts
COPY frontend/dist ./api/static

ENV VITE_API_HOST=http://localhost:8000
EXPOSE 8000
CMD ["uvicorn","api.main:app","--host","0.0.0.0","--port","8000"]
