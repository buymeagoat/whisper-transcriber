#!/usr/bin/env python3
"""
T027 Advanced Features: PWA Service Tests
Tests for Progressive Web App enhancement functionality.
"""

import pytest
import uuid
import json
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from api.services.pwa_service import (
    PWAEnhancementService,
    PWANotification,
    PWASubscription,
    OfflineJobRequest,
    PWACapabilities,
    PWAServiceWorkerConfig,
    PWAEventType,
    NotificationPriority
)

class TestPWAEnhancementService:
    """Test cases for PWAEnhancementService."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.service = PWAEnhancementService()
        self.test_user_id = "test-user-123"
        
        # Create test directory
        self.test_dir = Path("/tmp/test_pwa_service")
        self.test_dir.mkdir(exist_ok=True)
        
        # Patch storage directory to use test directory
        self.service.pwa_data_dir = self.test_dir
        self.service.subscriptions_file = self.test_dir / "subscriptions.json"
        self.service.notifications_file = self.test_dir / "notifications.json"
        self.service.offline_jobs_file = self.test_dir / "offline_jobs.json"
        
        # Initialize test data files
        self.service._ensure_data_files()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def test_register_push_subscription(self):
        """Test registering a push subscription."""
        subscription_data = {
            "endpoint": "https://push.service.com/endpoint123",
            "keys": {
                "p256dh": "test-p256dh-key",
                "auth": "test-auth-key"
            },
            "userAgent": "Mozilla/5.0 Test Browser"
        }
        
        subscription = self.service.register_push_subscription(
            user_id=self.test_user_id,
            subscription_data=subscription_data
        )
        
        assert subscription.user_id == self.test_user_id
        assert subscription.endpoint == subscription_data["endpoint"]
        assert subscription.p256dh_key == subscription_data["keys"]["p256dh"]
        assert subscription.auth_key == subscription_data["keys"]["auth"]
        assert subscription.is_active is True
        
        # Verify data was saved
        subscriptions = self.service._load_data(self.service.subscriptions_file)
        assert len(subscriptions) == 1
        assert subscriptions[0]["user_id"] == self.test_user_id
    
    def test_register_duplicate_subscription(self):
        """Test registering duplicate subscription replaces existing."""
        subscription_data = {
            "endpoint": "https://push.service.com/endpoint123",
            "keys": {
                "p256dh": "old-key",
                "auth": "old-auth"
            }
        }
        
        # Register first subscription
        self.service.register_push_subscription(
            user_id=self.test_user_id,
            subscription_data=subscription_data
        )
        
        # Register same endpoint with new keys
        subscription_data["keys"]["p256dh"] = "new-key"
        subscription_data["keys"]["auth"] = "new-auth"
        
        subscription = self.service.register_push_subscription(
            user_id=self.test_user_id,
            subscription_data=subscription_data
        )
        
        # Verify only one subscription exists with new keys
        subscriptions = self.service._load_data(self.service.subscriptions_file)
        assert len(subscriptions) == 1
        assert subscriptions[0]["p256dh_key"] == "new-key"
        assert subscriptions[0]["auth_key"] == "new-auth"
    
    def test_create_notification(self):
        """Test creating a notification."""
        notification = self.service.create_notification(
            user_id=self.test_user_id,
            title="Test Notification",
            body="This is a test notification",
            event_type=PWAEventType.JOB_COMPLETED,
            priority=NotificationPriority.HIGH,
            data={"job_id": "job-123"}
        )
        
        assert notification.user_id == self.test_user_id
        assert notification.title == "Test Notification"
        assert notification.body == "This is a test notification"
        assert notification.event_type == PWAEventType.JOB_COMPLETED.value
        assert notification.priority == NotificationPriority.HIGH.value
        assert notification.data["job_id"] == "job-123"
        assert notification.is_read is False
        
        # Verify data was saved
        notifications = self.service._load_data(self.service.notifications_file)
        assert len(notifications) == 1
        assert notifications[0]["id"] == notification.id
    
    def test_get_user_notifications(self):
        """Test getting user notifications."""
        # Create multiple notifications
        for i in range(5):
            self.service.create_notification(
                user_id=self.test_user_id,
                title=f"Notification {i}",
                body=f"Body {i}",
                event_type=PWAEventType.JOB_COMPLETED
            )
        
        # Create notification for different user
        self.service.create_notification(
            user_id="other-user",
            title="Other User Notification",
            body="Should not appear",
            event_type=PWAEventType.JOB_COMPLETED
        )
        
        # Get notifications
        notifications = self.service.get_user_notifications(self.test_user_id)
        
        assert len(notifications) == 5
        assert all(n.user_id == self.test_user_id for n in notifications)
        
        # Check ordering (newest first)
        titles = [n.title for n in notifications]
        assert titles == ["Notification 4", "Notification 3", "Notification 2", "Notification 1", "Notification 0"]
    
    def test_get_user_notifications_unread_only(self):
        """Test getting only unread notifications."""
        # Create notifications
        notifications = []
        for i in range(3):
            notif = self.service.create_notification(
                user_id=self.test_user_id,
                title=f"Notification {i}",
                body=f"Body {i}",
                event_type=PWAEventType.JOB_COMPLETED
            )
            notifications.append(notif)
        
        # Mark one as read
        self.service.mark_notification_read(self.test_user_id, notifications[1].id)
        
        # Get unread notifications
        unread_notifications = self.service.get_user_notifications(
            self.test_user_id,
            unread_only=True
        )
        
        assert len(unread_notifications) == 2
        assert all(not n.is_read for n in unread_notifications)
        assert notifications[1].id not in [n.id for n in unread_notifications]
    
    def test_mark_notification_read(self):
        """Test marking notification as read."""
        notification = self.service.create_notification(
            user_id=self.test_user_id,
            title="Test",
            body="Test",
            event_type=PWAEventType.JOB_COMPLETED
        )
        
        # Mark as read
        success = self.service.mark_notification_read(
            user_id=self.test_user_id,
            notification_id=notification.id
        )
        
        assert success is True
        
        # Verify in data file
        notifications = self.service._load_data(self.service.notifications_file)
        updated_notification = next(n for n in notifications if n["id"] == notification.id)
        assert updated_notification["is_read"] is True
        assert updated_notification["clicked_at"] is not None
    
    def test_mark_notification_read_wrong_user(self):
        """Test marking notification as read with wrong user."""
        notification = self.service.create_notification(
            user_id=self.test_user_id,
            title="Test",
            body="Test",
            event_type=PWAEventType.JOB_COMPLETED
        )
        
        # Try to mark as read with different user
        success = self.service.mark_notification_read(
            user_id="other-user",
            notification_id=notification.id
        )
        
        assert success is False
    
    def test_store_offline_job(self):
        """Test storing an offline job."""
        offline_job = self.service.store_offline_job(
            user_id=self.test_user_id,
            original_filename="test.wav",
            file_data="base64encodeddata",
            file_size=1024,
            model="small",
            language="en"
        )
        
        assert offline_job.user_id == self.test_user_id
        assert offline_job.original_filename == "test.wav"
        assert offline_job.file_data == "base64encodeddata"
        assert offline_job.file_size == 1024
        assert offline_job.sync_status == "pending"
        
        # Verify data was saved
        offline_jobs = self.service._load_data(self.service.offline_jobs_file)
        assert len(offline_jobs) == 1
        assert offline_jobs[0]["id"] == offline_job.id
    
    def test_store_offline_job_exceeds_limit(self):
        """Test storing offline job when limit is exceeded."""
        from fastapi import HTTPException
        
        # Store maximum allowed jobs
        for i in range(self.service.config.max_offline_jobs):
            self.service.store_offline_job(
                user_id=self.test_user_id,
                original_filename=f"test{i}.wav",
                file_data="data",
                file_size=1024,
                model="small"
            )
        
        # Try to store one more
        with pytest.raises(HTTPException) as exc_info:
            self.service.store_offline_job(
                user_id=self.test_user_id,
                original_filename="overflow.wav",
                file_data="data",
                file_size=1024,
                model="small"
            )
        
        assert exc_info.value.status_code == 400
        assert "maximum" in str(exc_info.value.detail).lower()
    
    def test_get_pending_offline_jobs(self):
        """Test getting pending offline jobs."""
        # Store jobs for test user
        jobs = []
        for i in range(3):
            job = self.service.store_offline_job(
                user_id=self.test_user_id,
                original_filename=f"test{i}.wav",
                file_data="data",
                file_size=1024,
                model="small"
            )
            jobs.append(job)
        
        # Store job for different user
        self.service.store_offline_job(
            user_id="other-user",
            original_filename="other.wav",
            file_data="data",
            file_size=1024,
            model="small"
        )
        
        # Mark one job as synced
        self.service.mark_offline_job_synced(jobs[1].id, "actual-job-123")
        
        # Get pending jobs
        pending_jobs = self.service.get_pending_offline_jobs(self.test_user_id)
        
        assert len(pending_jobs) == 2  # Synced job should not appear
        assert all(job.user_id == self.test_user_id for job in pending_jobs)
        assert all(job.sync_status == "pending" for job in pending_jobs)
    
    def test_mark_offline_job_synced(self):
        """Test marking offline job as synced."""
        offline_job = self.service.store_offline_job(
            user_id=self.test_user_id,
            original_filename="test.wav",
            file_data="data",
            file_size=1024,
            model="small"
        )
        
        # Mark as synced
        success = self.service.mark_offline_job_synced(
            offline_job.id,
            "actual-job-123"
        )
        
        assert success is True
        
        # Verify in data file
        offline_jobs = self.service._load_data(self.service.offline_jobs_file)
        updated_job = next(j for j in offline_jobs if j["id"] == offline_job.id)
        assert updated_job["sync_status"] == "synced"
        assert updated_job["actual_job_id"] == "actual-job-123"
        assert updated_job["synced_at"] is not None
    
    def test_get_pwa_capabilities(self):
        """Test getting PWA capabilities."""
        capabilities = self.service.get_pwa_capabilities()
        
        assert isinstance(capabilities, PWACapabilities)
        assert capabilities.offline_storage is True
        assert capabilities.push_notifications is True
        assert capabilities.background_sync is True
        assert capabilities.version is not None
    
    def test_get_service_worker_config(self):
        """Test getting service worker configuration."""
        config = self.service.get_service_worker_config()
        
        assert isinstance(config, PWAServiceWorkerConfig)
        assert config.version is not None
        assert config.cache_version is not None
        assert len(config.cached_routes) > 0
        assert config.background_sync_enabled is True
    
    def test_cleanup_old_data(self):
        """Test cleaning up old PWA data."""
        # Create old notification
        old_notification = PWANotification(
            id=str(uuid.uuid4()),
            user_id=self.test_user_id,
            title="Old Notification",
            body="Old body",
            event_type=PWAEventType.JOB_COMPLETED.value,
            created_at=datetime.utcnow() - timedelta(days=35)
        )
        
        # Create recent notification
        recent_notification = self.service.create_notification(
            user_id=self.test_user_id,
            title="Recent Notification",
            body="Recent body",
            event_type=PWAEventType.JOB_COMPLETED
        )
        
        # Manually add old notification to file
        notifications = self.service._load_data(self.service.notifications_file)
        notifications.append(old_notification.dict())
        self.service._save_data(self.service.notifications_file, notifications)
        
        # Create old offline job
        old_job = OfflineJobRequest(
            id=str(uuid.uuid4()),
            user_id=self.test_user_id,
            original_filename="old.wav",
            file_data="data",
            file_size=1024,
            model="small",
            created_at=datetime.utcnow() - timedelta(days=35),
            sync_status="synced"
        )
        
        # Manually add old job to file
        offline_jobs = self.service._load_data(self.service.offline_jobs_file)
        offline_jobs.append(old_job.dict())
        self.service._save_data(self.service.offline_jobs_file, offline_jobs)
        
        # Run cleanup
        cleaned_count = self.service.cleanup_old_data(days=30)
        
        assert cleaned_count >= 2
        
        # Verify old data was removed
        notifications = self.service._load_data(self.service.notifications_file)
        offline_jobs = self.service._load_data(self.service.offline_jobs_file)
        
        notification_ids = [n["id"] for n in notifications]
        job_ids = [j["id"] for j in offline_jobs]
        
        assert old_notification.id not in notification_ids
        assert recent_notification.id in notification_ids
        assert old_job.id not in job_ids
    
    def test_on_job_completed(self):
        """Test job completed event handler."""
        from api.models import Job, User
        
        # Create mock job and user
        job = Mock(spec=Job)
        job.id = "job-123"
        job.original_filename = "test.wav"
        
        user = Mock(spec=User)
        user.id = self.test_user_id
        
        # Handle job completed event
        self.service.on_job_completed(job, user)
        
        # Verify notification was created
        notifications = self.service.get_user_notifications(self.test_user_id)
        assert len(notifications) == 1
        
        notification = notifications[0]
        assert "complete" in notification.title.lower()
        assert job.original_filename in notification.body
        assert notification.event_type == PWAEventType.JOB_COMPLETED.value
        assert notification.data["job_id"] == job.id
    
    def test_on_job_failed(self):
        """Test job failed event handler."""
        from api.models import Job, User
        
        # Create mock job and user
        job = Mock(spec=Job)
        job.id = "job-123"
        job.original_filename = "test.wav"
        
        user = Mock(spec=User)
        user.id = self.test_user_id
        
        error_message = "Transcription failed due to audio format"
        
        # Handle job failed event
        self.service.on_job_failed(job, user, error_message)
        
        # Verify notification was created
        notifications = self.service.get_user_notifications(self.test_user_id)
        assert len(notifications) == 1
        
        notification = notifications[0]
        assert "failed" in notification.title.lower()
        assert error_message in notification.body
        assert notification.event_type == PWAEventType.JOB_FAILED.value
        assert notification.priority == NotificationPriority.HIGH.value
    
    def test_on_batch_completed(self):
        """Test batch completed event handler."""
        batch_id = "batch-123"
        stats = {"total": 10, "successful": 8, "failed": 2}
        
        # Handle batch completed event
        self.service.on_batch_completed(batch_id, self.test_user_id, stats)
        
        # Verify notification was created
        notifications = self.service.get_user_notifications(self.test_user_id)
        assert len(notifications) == 1
        
        notification = notifications[0]
        assert "batch" in notification.title.lower()
        assert "8/10" in notification.body
        assert notification.event_type == PWAEventType.BATCH_COMPLETED.value
        assert notification.data["batch_id"] == batch_id
        assert notification.data["stats"] == stats

if __name__ == "__main__":
    pytest.main([__file__])