FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
      ffmpeg git && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY api         ./api
RUN test -d /models \
 && test -f /models/base.pt \
 && test -f /models/large-v3.pt \
 && test -f /models/medium.pt \
 && test -f /models/small.pt \
 && test -f /models/tiny.pt \
 || (echo "Required model files missing in /models" >&2 && exit 1)
RUN mkdir -p uploads transcripts
COPY frontend/dist ./api/static

ENV VITE_API_HOST=http://localhost:8000
EXPOSE 8000
CMD ["uvicorn","api.main:app","--host","0.0.0.0","--port","8000"]
