FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
      ffmpeg git && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Create a non-root user to run Celery workers
RUN groupadd -g 1000 appuser && \
    useradd -m -u 1000 -g appuser appuser

RUN mkdir -p /app && chown -R appuser:appuser /app

WORKDIR /app
ENV PYTHONPATH=/app
COPY requirements.txt .
COPY alembic.ini .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY api         ./api
COPY models      ./models
RUN python -c "from api.utils.model_validation import validate_models_dir; validate_models_dir()"
RUN mkdir -p uploads transcripts
COPY frontend/dist ./api/static

ENV VITE_API_HOST=http://localhost:8000
EXPOSE 8000
CMD ["uvicorn","api.main:app","--host","0.0.0.0","--port","8000"]
