"""
Job queue management for the Whisper Transcriber API.
"""

import asyncio
import uuid
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
from api.utils.logger import get_backend_logger

logger = get_backend_logger()

class JobStatus(Enum):
    """Job status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class Job:
    """Job representation."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: JobStatus = JobStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    task_name: str = ""
    task_args: Dict[str, Any] = field(default_factory=dict)
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    progress: float = 0.0

class ThreadJobQueue:
    """Simple thread-based job queue for local development."""
    
    def __init__(self):
        self.jobs: Dict[str, Job] = {}
        self.running = False
    
    def submit_job(self, task_name: str, **kwargs) -> str:
        """
        Submit a job to the queue.
        
        Args:
            task_name: Name of the task to execute
            **kwargs: Task arguments
        
        Returns:
            Job ID
        """
        job = Job(
            task_name=task_name,
            task_args=kwargs
        )
        self.jobs[job.id] = job
        logger.info(f"Job {job.id} submitted: {task_name}")
        
        # For development, execute immediately in background
        asyncio.create_task(self._execute_job(job.id))
        
        return job.id
    
    async def _execute_job(self, job_id: str):
        """Execute a job."""
        if job_id not in self.jobs:
            return
        
        job = self.jobs[job_id]
        job.status = JobStatus.RUNNING
        job.started_at = datetime.utcnow()
        
        try:
            logger.info(f"Executing job {job_id}: {job.task_name}")
            
            if job.task_name == "transcribe_audio":
                from api.app_state import handle_whisper
                audio_path = job.task_args.get("audio_path")
                model = job.task_args.get("model", "small")
                language = job.task_args.get("language")
                
                result = handle_whisper(audio_path, model=model, language=language)
                job.result = result
                
                if result.get("success"):
                    job.status = JobStatus.COMPLETED
                else:
                    job.status = JobStatus.FAILED
                    job.error = result.get("error", "Unknown error")
            
            else:
                job.status = JobStatus.FAILED
                job.error = f"Unknown task: {job.task_name}"
        
        except Exception as e:
            logger.error(f"Job {job_id} failed: {e}")
            job.status = JobStatus.FAILED
            job.error = str(e)
        
        finally:
            job.completed_at = datetime.utcnow()
            logger.info(f"Job {job_id} finished with status: {job.status.value}")
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """Get job by ID."""
        return self.jobs.get(job_id)
    
    def get_job_status(self, job_id: str) -> Optional[JobStatus]:
        """Get job status by ID."""
        job = self.get_job(job_id)
        return job.status if job else None
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a job."""
        if job_id in self.jobs:
            job = self.jobs[job_id]
            if job.status in [JobStatus.PENDING, JobStatus.RUNNING]:
                job.status = JobStatus.CANCELLED
                logger.info(f"Job {job_id} cancelled")
                return True
        return False
    
    def cleanup_old_jobs(self, max_age_hours: int = 24):
        """Clean up old completed jobs."""
        cutoff = datetime.utcnow().timestamp() - (max_age_hours * 3600)
        
        to_remove = []
        for job_id, job in self.jobs.items():
            if (job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED] and
                job.completed_at and job.completed_at.timestamp() < cutoff):
                to_remove.append(job_id)
        
        for job_id in to_remove:
            del self.jobs[job_id]
        
        if to_remove:
            logger.info(f"Cleaned up {len(to_remove)} old jobs")

# Global job queue instance
job_queue = ThreadJobQueue()
