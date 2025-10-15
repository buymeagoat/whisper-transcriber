# Celery worker for background transcription processing
# Integrates with the streamlined FastAPI application

import os
import asyncio
from celery import Celery
from pathlib import Path
import whisper
import logging
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import our models
from .main import Job, Base, ConnectionManager

# Setup
BASE_DIR = Path(__file__).parent.parent
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/app.db")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
WHISPER_MODEL_DIR = os.getenv("WHISPER_MODEL_DIR", BASE_DIR / "models")

# Database setup
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Celery setup
celery_app = Celery("whisper_transcriber", broker=REDIS_URL, backend=REDIS_URL)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=10,
)

# Connection manager for WebSocket updates
manager = ConnectionManager()

# Load Whisper models (lazy loading)
_whisper_models = {}

def get_whisper_model(model_name: str):
    """Load and cache Whisper models"""
    if model_name not in _whisper_models:
        logging.info(f"Loading Whisper model: {model_name}")
        _whisper_models[model_name] = whisper.load_model(model_name)
    return _whisper_models[model_name]

@celery_app.task(bind=True)
def transcribe_audio(self, job_id: str):
    """
    Background task to transcribe audio file
    """
    db = SessionLocal()
    try:
        # Get job from database
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            logging.error(f"Job {job_id} not found")
            return {"error": "Job not found"}

        # Update status to processing
        job.status = "processing"
        db.commit()

        # Send progress update
        asyncio.create_task(manager.send_progress(job_id, {
            "status": "processing",
            "progress": 10,
            "message": f"Loading {job.model_used} model..."
        }))

        # Load model
        model = get_whisper_model(job.model_used)
        
        # Send progress update
        asyncio.create_task(manager.send_progress(job_id, {
            "status": "processing", 
            "progress": 30,
            "message": "Model loaded, starting transcription..."
        }))

        # Get file path
        upload_path = Path("storage/uploads") / job.filename
        if not upload_path.exists():
            raise FileNotFoundError(f"Audio file not found: {upload_path}")

        # Transcribe audio
        logging.info(f"Starting transcription for {job_id} with model {job.model_used}")
        result = model.transcribe(str(upload_path))
        
        # Extract transcript
        transcript = result["text"].strip()
        
        # Calculate duration if available
        duration = result.get("duration")
        if duration:
            job.duration = int(duration)

        # Send progress update
        asyncio.create_task(manager.send_progress(job_id, {
            "status": "processing",
            "progress": 90,
            "message": "Transcription complete, finalizing..."
        }))

        # Update job with results
        job.transcript = transcript
        job.status = "completed"
        job.completed_at = datetime.utcnow()
        db.commit()

        # Send completion update
        asyncio.create_task(manager.send_progress(job_id, {
            "status": "completed",
            "progress": 100,
            "message": "Transcription completed successfully!",
            "transcript": transcript
        }))

        logging.info(f"Transcription completed for job {job_id}")
        
        # Clean up uploaded file (optional)
        try:
            upload_path.unlink()
            logging.info(f"Cleaned up uploaded file: {upload_path}")
        except Exception as e:
            logging.warning(f"Failed to clean up file {upload_path}: {e}")

        return {
            "job_id": job_id,
            "status": "completed",
            "transcript": transcript,
            "duration": job.duration
        }

    except Exception as e:
        logging.error(f"Transcription failed for job {job_id}: {str(e)}")
        
        # Update job with error
        job.status = "failed"
        job.error_message = str(e)
        db.commit()

        # Send error update
        asyncio.create_task(manager.send_progress(job_id, {
            "status": "failed",
            "progress": 0,
            "message": f"Transcription failed: {str(e)}"
        }))

        return {"error": str(e)}
    
    finally:
        db.close()

# Health check task
@celery_app.task
def health_check():
    """Simple health check task"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

# Celery worker startup
@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """Setup periodic tasks"""
    # Health check every 5 minutes
    sender.add_periodic_task(300.0, health_check.s(), name='health_check')

if __name__ == "__main__":
    # Run worker directly
    celery_app.worker_main(["worker", "--loglevel=info", "--concurrency=1"])
