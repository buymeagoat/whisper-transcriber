"""
WebSocket Job Integration for T025 Phase 4
Integrates WebSocket service with job processing for real-time status updates.
"""

import asyncio
from typing import Dict, Any, Optional, Coroutine
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import event

from api.models import Job, JobStatusEnum
from api.services.enhanced_websocket_service import get_websocket_service
from api.utils.logger import get_system_logger

logger = get_system_logger("websocket_job_integration")

class WebSocketJobNotifier:
    """Service to send WebSocket notifications for job status changes."""
    
    def __init__(self):
        self.websocket_service = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize the WebSocket job notifier."""
        try:
            self.websocket_service = await get_websocket_service()
            self._initialized = True
            logger.info("WebSocket job notifier initialized")
        except Exception as e:
            logger.error(f"Failed to initialize WebSocket job notifier: {e}")
            self._initialized = False
    
    async def notify_job_status_change(self, job: Job, previous_status: Optional[str] = None,
                                     progress: Optional[int] = None, message: str = ""):
        """Send WebSocket notification for job status change."""
        if not self._initialized or not self.websocket_service:
            return
        
        try:
            # Prepare notification data
            notification_data = {
                "job_id": job.id,
                "status": job.status.value,
                "progress": progress or job.progress or 0,
                "message": message or f"Job status changed to {job.status.value}",
                "previous_status": previous_status,
                "updated_at": job.updated_at.isoformat() if job.updated_at else datetime.utcnow().isoformat(),
                "user_id": job.user_id
            }
            
            # Add status-specific information
            if job.status == JobStatusEnum.COMPLETED:
                notification_data.update({
                    "download_url": f"/api/jobs/{job.id}/download" if job.transcript_file_path else None,
                    "completion_time": job.finished_at.isoformat() if job.finished_at else None
                })
            elif job.status == JobStatusEnum.FAILED:
                notification_data.update({
                    "error_message": job.error_message or "Job failed",
                    "failure_time": job.finished_at.isoformat() if job.finished_at else None
                })
            elif job.status == JobStatusEnum.PROCESSING:
                notification_data.update({
                    "started_at": job.started_at.isoformat() if job.started_at else None,
                    "estimated_completion": None  # Could add estimation logic
                })
            
            # Send job-specific notification
            await self.websocket_service.send_job_update(
                job_id=job.id,
                status=job.status.value,
                progress=notification_data["progress"],
                message=notification_data["message"],
                extra_data=notification_data
            )
            
            # Send user-specific notification
            await self.websocket_service.send_user_notification(
                user_id=job.user_id,
                notification_type="job_update",
                message=f"Job {job.id}: {notification_data['message']}",
                data=notification_data
            )
            
            logger.debug(f"WebSocket notification sent for job {job.id}: {job.status.value}")
            
        except Exception as e:
            logger.error(f"Failed to send WebSocket notification for job {job.id}: {e}")
    
    async def notify_job_progress(
        self,
        job_id: str,
        progress: int,
        message: str = "",
        user_id: Optional[str] = None,
    ):
        """Send WebSocket notification for job progress update."""
        if not self._initialized or not self.websocket_service:
            return
        
        try:
            progress_data = {
                "job_id": job_id,
                "progress": progress,
                "message": message or f"Progress: {progress}%",
                "timestamp": datetime.utcnow().isoformat(),
                "user_id": user_id
            }
            
            # Send progress update
            await self.websocket_service.send_job_update(
                job_id=job_id,
                status="processing",
                progress=progress,
                message=message,
                extra_data=progress_data
            )
            
            logger.debug(f"WebSocket progress notification sent for job {job_id}: {progress}%")
            
        except Exception as e:
            logger.error(f"Failed to send WebSocket progress notification for job {job_id}: {e}")
    
    async def notify_job_error(
        self,
        job_id: str,
        error_message: str,
        user_id: Optional[str] = None,
    ):
        """Send WebSocket notification for job error."""
        if not self._initialized or not self.websocket_service:
            return
        
        try:
            error_data = {
                "job_id": job_id,
                "error_message": error_message,
                "timestamp": datetime.utcnow().isoformat(),
                "user_id": user_id
            }
            
            # Send error notification
            await self.websocket_service.send_job_update(
                job_id=job_id,
                status="failed",
                progress=0,
                message=f"Error: {error_message}",
                extra_data=error_data
            )
            
            if user_id:
                await self.websocket_service.send_user_notification(
                    user_id=user_id,
                    notification_type="job_error",
                    message=f"Job {job_id} failed: {error_message}",
                    data=error_data
                )
            
            logger.debug(f"WebSocket error notification sent for job {job_id}")
            
        except Exception as e:
            logger.error(f"Failed to send WebSocket error notification for job {job_id}: {e}")

# Global job notifier instance
_job_notifier: Optional[WebSocketJobNotifier] = None

async def get_job_notifier() -> WebSocketJobNotifier:
    """Get the global WebSocket job notifier."""
    global _job_notifier
    
    if _job_notifier is None:
        _job_notifier = WebSocketJobNotifier()
        await _job_notifier.initialize()
    
    return _job_notifier

# SQLAlchemy event listeners for automatic notifications

def setup_job_event_listeners():
    """Set up SQLAlchemy event listeners for automatic WebSocket notifications."""
    
    @event.listens_for(Job, 'after_update')
    def job_after_update(mapper, connection, target):
        """Send WebSocket notification when job is updated."""
        # Ensure synchronous SQLAlchemy hooks can safely trigger async work
        _safe_async_schedule(_handle_job_update_async(target))
    
    @event.listens_for(Job, 'after_insert')
    def job_after_insert(mapper, connection, target):
        """Send WebSocket notification when job is created."""
        _safe_async_schedule(_handle_job_create_async(target))
    
    logger.info("WebSocket job event listeners set up")

def _safe_async_schedule(coro: Coroutine[Any, Any, Any]) -> None:
    """Schedule an async task, falling back to running it inline if needed."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # No running loop (likely during sync tests); execute inline for reliability
        asyncio.run(coro)
    else:
        loop.create_task(coro)

async def _handle_job_update_async(job: Job):
    """Handle job update in async context."""
    try:
        job_notifier = await get_job_notifier()
        await job_notifier.notify_job_status_change(job)
    except Exception as e:
        logger.error(f"Error handling job update notification: {e}")

async def _handle_job_create_async(job: Job):
    """Handle job creation in async context."""
    try:
        job_notifier = await get_job_notifier()
        await job_notifier.notify_job_status_change(
            job, 
            message=f"Job {job.id} created and queued for processing"
        )
    except Exception as e:
        logger.error(f"Error handling job creation notification: {e}")

# Manual notification functions for use in job processing

async def notify_job_started(job_id: str, user_id: str):
    """Manually notify that a job has started processing."""
    try:
        job_notifier = await get_job_notifier()
        await job_notifier.notify_job_progress(
            job_id=job_id,
            progress=0,
            message="Job processing started",
            user_id=user_id
        )
    except Exception as e:
        logger.error(f"Error notifying job start: {e}")

async def notify_job_progress_update(
    job_id: str,
    progress: int,
    message: str = "",
    user_id: Optional[str] = None,
):
    """Manually notify job progress update."""
    try:
        job_notifier = await get_job_notifier()
        await job_notifier.notify_job_progress(
            job_id=job_id,
            progress=progress,
            message=message,
            user_id=user_id
        )
    except Exception as e:
        logger.error(f"Error notifying job progress: {e}")

async def notify_job_completed(job_id: str, user_id: str, download_url: Optional[str] = None):
    """Manually notify that a job has completed."""
    try:
        job_notifier = await get_job_notifier()
        
        completion_data = {
            "job_id": job_id,
            "download_url": download_url,
            "completion_time": datetime.utcnow().isoformat()
        }
        
        await job_notifier.websocket_service.send_job_update(
            job_id=job_id,
            status="completed",
            progress=100,
            message="Job completed successfully",
            extra_data=completion_data
        )
        
        await job_notifier.websocket_service.send_user_notification(
            user_id=user_id,
            notification_type="job_completed",
            message=f"Job {job_id} completed successfully",
            data=completion_data
        )
        
    except Exception as e:
        logger.error(f"Error notifying job completion: {e}")

async def notify_job_failed(job_id: str, error_message: str, user_id: str):
    """Manually notify that a job has failed."""
    try:
        job_notifier = await get_job_notifier()
        await job_notifier.notify_job_error(
            job_id=job_id,
            error_message=error_message,
            user_id=user_id
        )
    except Exception as e:
        logger.error(f"Error notifying job failure: {e}")

# System notification functions

async def notify_system_maintenance(message: str, maintenance_type: str = "scheduled"):
    """Send system maintenance notifications to all users."""
    try:
        websocket_service = await get_websocket_service()
        await websocket_service.broadcast_system_message(
            message=message,
            broadcast_type="maintenance",
            data={
                "maintenance_type": maintenance_type,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    except Exception as e:
        logger.error(f"Error sending maintenance notification: {e}")

async def notify_system_alert(alert_message: str, severity: str = "info"):
    """Send system alerts to admin users."""
    try:
        websocket_service = await get_websocket_service()
        await websocket_service.send_admin_alert(
            alert_type="system",
            message=alert_message,
            severity=severity,
            data={
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    except Exception as e:
        logger.error(f"Error sending system alert: {e}")

# Performance monitoring integration

async def notify_performance_alert(metric_type: str, current_value: float, threshold: float):
    """Send performance-related alerts to admins."""
    try:
        websocket_service = await get_websocket_service()
        await websocket_service.send_admin_alert(
            alert_type="performance",
            message=f"Performance alert: {metric_type} is {current_value} (threshold: {threshold})",
            severity="warning" if current_value > threshold * 1.2 else "info",
            data={
                "metric_type": metric_type,
                "current_value": current_value,
                "threshold": threshold,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    except Exception as e:
        logger.error(f"Error sending performance alert: {e}")
