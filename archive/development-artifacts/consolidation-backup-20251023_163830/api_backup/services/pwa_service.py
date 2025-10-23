#!/usr/bin/env python3
"""
T027 Advanced Features: Mobile PWA Enhancement Service
Service for enhanced mobile Progressive Web App features including offline capabilities.
"""

import json
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum

from fastapi import HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from api.utils.logger import get_system_logger
from api.models import Job, User
from api.paths import storage

logger = get_system_logger("pwa_service")

class PWAEventType(Enum):
    """PWA event types."""
    JOB_COMPLETED = "job_completed"
    JOB_FAILED = "job_failed"
    BATCH_COMPLETED = "batch_completed"
    SYSTEM_MAINTENANCE = "system_maintenance"
    STORAGE_WARNING = "storage_warning"

class NotificationPriority(Enum):
    """Notification priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

class PWANotification(BaseModel):
    """PWA notification model."""
    id: str
    user_id: str
    title: str
    body: str
    icon: Optional[str] = None
    badge: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    priority: str = NotificationPriority.NORMAL.value
    event_type: str
    created_at: datetime
    scheduled_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    clicked_at: Optional[datetime] = None
    is_read: bool = False

class PWASubscription(BaseModel):
    """PWA push subscription model."""
    user_id: str
    endpoint: str
    p256dh_key: str
    auth_key: str
    user_agent: str
    created_at: datetime
    last_used: Optional[datetime] = None
    is_active: bool = True

class OfflineJobRequest(BaseModel):
    """Offline job request model."""
    id: str
    user_id: str
    original_filename: str
    file_data: str  # Base64 encoded
    file_size: int
    model: str
    language: Optional[str] = None
    created_at: datetime
    sync_status: str = "pending"  # pending, synced, failed

class PWACapabilities(BaseModel):
    """PWA capabilities information."""
    offline_storage: bool
    push_notifications: bool
    background_sync: bool
    file_system_access: bool
    web_share: bool
    install_prompt: bool
    version: str

class PWAServiceWorkerConfig(BaseModel):
    """Service worker configuration."""
    version: str
    cache_version: str
    cached_routes: List[str]
    offline_fallback: str
    background_sync_enabled: bool
    max_offline_jobs: int
    cache_max_age: int  # hours

class PWAEnhancementService:
    """Service for PWA mobile enhancements."""
    
    def __init__(self):
        self.pwa_data_dir = Path(storage.UPLOAD_DIR) / "pwa"
        self.pwa_data_dir.mkdir(exist_ok=True)
        
        self.subscriptions_file = self.pwa_data_dir / "subscriptions.json"
        self.notifications_file = self.pwa_data_dir / "notifications.json"
        self.offline_jobs_file = self.pwa_data_dir / "offline_jobs.json"
        
        # Initialize data files
        self._ensure_data_files()
        
        # PWA configuration
        self.config = PWAServiceWorkerConfig(
            version="1.0.0",
            cache_version="v1",
            cached_routes=[
                "/",
                "/static/",
                "/api/v1/jobs/list",
                "/api/v1/user/settings",
                "/api/v1/health"
            ],
            offline_fallback="/offline.html",
            background_sync_enabled=True,
            max_offline_jobs=10,
            cache_max_age=24  # 24 hours
        )
    
    def _ensure_data_files(self):
        """Ensure PWA data files exist."""
        
        for file_path in [self.subscriptions_file, self.notifications_file, self.offline_jobs_file]:
            if not file_path.exists():
                with open(file_path, "w") as f:
                    json.dump([], f)
    
    def _load_data(self, file_path: Path) -> List[Dict]:
        """Load data from JSON file."""
        
        try:
            with open(file_path, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load data from {file_path}: {e}")
            return []
    
    def _save_data(self, file_path: Path, data: List[Dict]):
        """Save data to JSON file."""
        
        try:
            with open(file_path, "w") as f:
                json.dump(data, f, default=str, indent=2)
        except Exception as e:
            logger.error(f"Failed to save data to {file_path}: {e}")
    
    def register_push_subscription(
        self,
        user_id: str,
        subscription_data: Dict[str, str]
    ) -> PWASubscription:
        """Register a new push subscription."""
        
        # Load existing subscriptions
        subscriptions = self._load_data(self.subscriptions_file)
        
        # Create new subscription
        subscription = PWASubscription(
            user_id=user_id,
            endpoint=subscription_data["endpoint"],
            p256dh_key=subscription_data.get("keys", {}).get("p256dh", ""),
            auth_key=subscription_data.get("keys", {}).get("auth", ""),
            user_agent=subscription_data.get("userAgent", ""),
            created_at=datetime.utcnow()
        )
        
        # Remove existing subscription for this user/endpoint
        subscriptions = [
            s for s in subscriptions
            if not (s.get("user_id") == user_id and s.get("endpoint") == subscription["endpoint"])
        ]
        
        # Add new subscription
        subscriptions.append(subscription.dict())
        
        # Save subscriptions
        self._save_data(self.subscriptions_file, subscriptions)
        
        logger.info(f"Registered push subscription for user {user_id}")
        return subscription
    
    def create_notification(
        self,
        user_id: str,
        title: str,
        body: str,
        event_type: PWAEventType,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        data: Optional[Dict[str, Any]] = None,
        scheduled_at: Optional[datetime] = None
    ) -> PWANotification:
        """Create a new notification."""
        
        notification = PWANotification(
            id=str(uuid.uuid4()),
            user_id=user_id,
            title=title,
            body=body,
            icon="/static/icons/notification-icon.png",
            badge="/static/icons/badge-icon.png",
            data=data or {},
            priority=priority.value,
            event_type=event_type.value,
            created_at=datetime.utcnow(),
            scheduled_at=scheduled_at
        )
        
        # Load existing notifications
        notifications = self._load_data(self.notifications_file)
        
        # Add new notification
        notifications.append(notification.dict())
        
        # Save notifications
        self._save_data(self.notifications_file, notifications)
        
        logger.info(f"Created notification {notification.id} for user {user_id}")
        
        # Send push notification if immediate
        if not scheduled_at:
            self._send_push_notification(notification)
        
        return notification
    
    def _send_push_notification(self, notification: PWANotification):
        """Send push notification to user's subscribed devices."""
        
        # Load subscriptions
        subscriptions = self._load_data(self.subscriptions_file)
        
        # Find user subscriptions
        user_subscriptions = [
            s for s in subscriptions
            if s.get("user_id") == notification.user_id and s.get("is_active", True)
        ]
        
        if not user_subscriptions:
            logger.info(f"No active subscriptions for user {notification.user_id}")
            return
        
        # Prepare notification payload
        payload = {
            "title": notification.title,
            "body": notification.body,
            "icon": notification.icon,
            "badge": notification.badge,
            "data": notification.data or {},
            "tag": f"notification-{notification.id}",
            "timestamp": int(notification.created_at.timestamp() * 1000)
        }
        
        # Note: In a real implementation, you would use a push service like:
        # - Web Push Protocol
        # - pywebpush library
        # - Firebase Cloud Messaging
        # For now, we'll just log the notification
        
        logger.info(f"Sending push notification to {len(user_subscriptions)} devices for user {notification.user_id}")
        logger.debug(f"Notification payload: {json.dumps(payload, indent=2)}")
        
        # Mark as sent
        notifications = self._load_data(self.notifications_file)
        for notif in notifications:
            if notif.get("id") == notification.id:
                notif["sent_at"] = datetime.utcnow().isoformat()
                break
        
        self._save_data(self.notifications_file, notifications)
    
    def get_user_notifications(
        self,
        user_id: str,
        limit: int = 50,
        unread_only: bool = False
    ) -> List[PWANotification]:
        """Get notifications for a user."""
        
        notifications = self._load_data(self.notifications_file)
        
        # Filter by user
        user_notifications = [
            n for n in notifications
            if n.get("user_id") == user_id
        ]
        
        # Filter by read status if requested
        if unread_only:
            user_notifications = [
                n for n in user_notifications
                if not n.get("is_read", False)
            ]
        
        # Sort by creation date (newest first)
        user_notifications.sort(
            key=lambda x: x.get("created_at", ""),
            reverse=True
        )
        
        # Apply limit
        user_notifications = user_notifications[:limit]
        
        # Convert to models
        return [PWANotification(**n) for n in user_notifications]
    
    def mark_notification_read(self, user_id: str, notification_id: str) -> bool:
        """Mark a notification as read."""
        
        notifications = self._load_data(self.notifications_file)
        
        for notification in notifications:
            if (notification.get("id") == notification_id and 
                notification.get("user_id") == user_id):
                notification["is_read"] = True
                notification["clicked_at"] = datetime.utcnow().isoformat()
                self._save_data(self.notifications_file, notifications)
                return True
        
        return False
    
    def store_offline_job(
        self,
        user_id: str,
        original_filename: str,
        file_data: str,
        file_size: int,
        model: str,
        language: Optional[str] = None
    ) -> OfflineJobRequest:
        """Store an offline job request for later synchronization."""
        
        offline_job = OfflineJobRequest(
            id=str(uuid.uuid4()),
            user_id=user_id,
            original_filename=original_filename,
            file_data=file_data,
            file_size=file_size,
            model=model,
            language=language,
            created_at=datetime.utcnow()
        )
        
        # Load existing offline jobs
        offline_jobs = self._load_data(self.offline_jobs_file)
        
        # Check limit per user
        user_jobs = [j for j in offline_jobs if j.get("user_id") == user_id]
        if len(user_jobs) >= self.config.max_offline_jobs:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Maximum {self.config.max_offline_jobs} offline jobs allowed"
            )
        
        # Add new job
        offline_jobs.append(offline_job.dict())
        
        # Save offline jobs
        self._save_data(self.offline_jobs_file, offline_jobs)
        
        logger.info(f"Stored offline job {offline_job.id} for user {user_id}")
        return offline_job
    
    def get_pending_offline_jobs(self, user_id: str) -> List[OfflineJobRequest]:
        """Get pending offline jobs for a user."""
        
        offline_jobs = self._load_data(self.offline_jobs_file)
        
        user_jobs = [
            j for j in offline_jobs
            if j.get("user_id") == user_id and j.get("sync_status") == "pending"
        ]
        
        return [OfflineJobRequest(**j) for j in user_jobs]
    
    def mark_offline_job_synced(self, job_id: str, actual_job_id: str) -> bool:
        """Mark an offline job as synced."""
        
        offline_jobs = self._load_data(self.offline_jobs_file)
        
        for job in offline_jobs:
            if job.get("id") == job_id:
                job["sync_status"] = "synced"
                job["actual_job_id"] = actual_job_id
                job["synced_at"] = datetime.utcnow().isoformat()
                self._save_data(self.offline_jobs_file, offline_jobs)
                return True
        
        return False
    
    def get_pwa_capabilities(self) -> PWACapabilities:
        """Get PWA capabilities information."""
        
        return PWACapabilities(
            offline_storage=True,
            push_notifications=True,
            background_sync=True,
            file_system_access=False,  # Not widely supported yet
            web_share=True,
            install_prompt=True,
            version=self.config.version
        )
    
    def get_service_worker_config(self) -> PWAServiceWorkerConfig:
        """Get service worker configuration."""
        
        return self.config
    
    def update_subscription_activity(self, user_id: str, endpoint: str):
        """Update subscription last used time."""
        
        subscriptions = self._load_data(self.subscriptions_file)
        
        for subscription in subscriptions:
            if (subscription.get("user_id") == user_id and 
                subscription.get("endpoint") == endpoint):
                subscription["last_used"] = datetime.utcnow().isoformat()
                break
        
        self._save_data(self.subscriptions_file, subscriptions)
    
    def cleanup_old_data(self, days: int = 30):
        """Clean up old PWA data."""
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        cleanup_count = 0
        
        # Clean up old notifications
        notifications = self._load_data(self.notifications_file)
        old_count = len(notifications)
        
        notifications = [
            n for n in notifications
            if datetime.fromisoformat(n.get("created_at", "")) > cutoff_date
        ]
        
        if len(notifications) < old_count:
            self._save_data(self.notifications_file, notifications)
            cleanup_count += old_count - len(notifications)
            logger.info(f"Cleaned up {old_count - len(notifications)} old notifications")
        
        # Clean up old offline jobs
        offline_jobs = self._load_data(self.offline_jobs_file)
        old_count = len(offline_jobs)
        
        offline_jobs = [
            j for j in offline_jobs
            if (datetime.fromisoformat(j.get("created_at", "")) > cutoff_date or
                j.get("sync_status") == "pending")
        ]
        
        if len(offline_jobs) < old_count:
            self._save_data(self.offline_jobs_file, offline_jobs)
            cleanup_count += old_count - len(offline_jobs)
            logger.info(f"Cleaned up {old_count - len(offline_jobs)} old offline jobs")
        
        return cleanup_count
    
    # Job event handlers
    def on_job_completed(self, job: Job, user: User):
        """Handle job completion event."""
        
        self.create_notification(
            user_id=user.id,
            title="Transcription Complete",
            body=f"Your file '{job.original_filename}' has been transcribed successfully.",
            event_type=PWAEventType.JOB_COMPLETED,
            priority=NotificationPriority.NORMAL,
            data={
                "job_id": job.id,
                "filename": job.original_filename,
                "action_url": f"/jobs/{job.id}"
            }
        )
    
    def on_job_failed(self, job: Job, user: User, error_message: str):
        """Handle job failure event."""
        
        self.create_notification(
            user_id=user.id,
            title="Transcription Failed",
            body=f"Failed to transcribe '{job.original_filename}': {error_message}",
            event_type=PWAEventType.JOB_FAILED,
            priority=NotificationPriority.HIGH,
            data={
                "job_id": job.id,
                "filename": job.original_filename,
                "error": error_message,
                "action_url": f"/jobs/{job.id}"
            }
        )
    
    def on_batch_completed(self, batch_id: str, user_id: str, stats: Dict[str, int]):
        """Handle batch completion event."""
        
        self.create_notification(
            user_id=user_id,
            title="Batch Processing Complete",
            body=f"Batch completed: {stats['successful']}/{stats['total']} files successful.",
            event_type=PWAEventType.BATCH_COMPLETED,
            priority=NotificationPriority.NORMAL,
            data={
                "batch_id": batch_id,
                "stats": stats,
                "action_url": f"/batch/{batch_id}"
            }
        )

# Create singleton instance
pwa_service = PWAEnhancementService()