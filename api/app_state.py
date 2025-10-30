"""
Application state management for the Whisper Transcriber API.
"""

import threading
import time
from datetime import datetime, timezone
from typing import Dict, Any

from celery.exceptions import CeleryError

from api.utils.logger import get_backend_logger, get_app_logger

# Loggers
backend_log = get_backend_logger()
app_log = get_app_logger()

# Timezone
LOCAL_TZ = timezone.utc

# Application state
app_state = {
    "startup_time": datetime.now(LOCAL_TZ),
    "cleanup_thread": None,
    "job_queue": None,
    "celery_connected": False
}

def initialize_job_queue():
    """Initialize the Celery-backed job queue."""

    from api.services.job_queue import CeleryJobQueue, job_queue as global_queue

    queue = global_queue if isinstance(global_queue, CeleryJobQueue) else CeleryJobQueue()
    app_state["job_queue"] = queue
    return queue

def handle_whisper(audio_file_path: str, **kwargs) -> Dict[str, Any]:
    """
    Handle whisper transcription.
    
    Args:
        audio_file_path: Path to audio file
        **kwargs: Additional arguments (model, language, etc.)
    
    Returns:
        Transcription result
    """
    try:
        # Import whisper here to avoid loading at startup
        import whisper
        
        model_name = kwargs.get("model", "small")
        language = kwargs.get("language", None)
        
        backend_log.info(f"Loading Whisper model: {model_name}")
        model = whisper.load_model(model_name)
        
        backend_log.info(f"Transcribing audio file: {audio_file_path}")
        result = model.transcribe(audio_file_path, language=language)
        
        return {
            "success": True,
            "text": result.get("text", ""),
            "language": result.get("language", language),
            "segments": result.get("segments", []),
            "model": model_name
        }
    
    except Exception as e:
        backend_log.error(f"Whisper transcription failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "text": "",
            "model": kwargs.get("model", "unknown")
        }

def cleanup_old_files():
    """Background cleanup of old files."""
    while True:
        try:
            app_log.info("Running cleanup of old files...")
            # TODO: Implement actual cleanup logic
            time.sleep(3600)  # Run every hour
        except Exception as e:
            app_log.error(f"Cleanup error: {e}")
            time.sleep(300)  # Wait 5 minutes on error

def start_cleanup_thread():
    """Start the background cleanup thread."""
    if app_state["cleanup_thread"] is None or not app_state["cleanup_thread"].is_alive():
        app_state["cleanup_thread"] = threading.Thread(
            target=cleanup_old_files, 
            daemon=True,
            name="cleanup-thread"
        )
        app_state["cleanup_thread"].start()
        app_log.info("Started cleanup thread")

def stop_cleanup_thread():
    """Stop the background cleanup thread."""
    if app_state["cleanup_thread"] and app_state["cleanup_thread"].is_alive():
        # Note: This is a simple implementation. In production, use proper threading events
        app_log.info("Cleanup thread will stop after current cycle")

def check_celery_connection() -> bool:
    """
    Check if Celery is available and connected.
    
    Returns:
        True if Celery is connected, False otherwise
    """
    try:
        from api.worker import celery_app

        with celery_app.connection_for_read():
            app_state["celery_connected"] = True
            return True
    except CeleryError as exc:
        backend_log.debug(f"Celery not available: {exc}")
    except Exception as exc:  # pragma: no cover - defensive
        backend_log.debug(f"Celery connection check failed: {exc}")

    app_state["celery_connected"] = False
    return False

def get_app_state() -> Dict[str, Any]:
    """Get current application state."""
    return {
        "startup_time": app_state["startup_time"].isoformat(),
        "cleanup_thread_active": (
            app_state["cleanup_thread"] is not None and 
            app_state["cleanup_thread"].is_alive()
        ),
        "celery_connected": app_state["celery_connected"],
        "uptime_seconds": (datetime.now(LOCAL_TZ) - app_state["startup_time"]).total_seconds()
    }
