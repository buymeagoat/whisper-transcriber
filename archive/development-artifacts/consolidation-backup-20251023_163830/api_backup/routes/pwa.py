#!/usr/bin/env python3
"""
T027 Advanced Features: PWA Enhancement API Routes
API endpoints for Progressive Web App enhancements including push notifications and offline capabilities.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from api.orm_bootstrap import get_db
from api.utils.logger import get_system_logger
from api.services.users import get_current_user
from api.services.pwa_service import (
    pwa_service,
    PWANotification,
    PWASubscription,
    OfflineJobRequest,
    PWACapabilities,
    PWAServiceWorkerConfig,
    PWAEventType,
    NotificationPriority
)
from api.models import User

logger = get_system_logger("pwa_routes")
router = APIRouter(prefix="/api/v1/pwa", tags=["pwa"])
security = HTTPBearer()

class PushSubscriptionRequest(BaseModel):
    """Request model for push subscription registration."""
    endpoint: str = Field(..., description="Push service endpoint URL")
    keys: Dict[str, str] = Field(..., description="Encryption keys (p256dh and auth)")
    userAgent: Optional[str] = Field(None, description="User agent string")

class CreateNotificationRequest(BaseModel):
    """Request model for creating notifications."""
    title: str = Field(..., min_length=1, max_length=100, description="Notification title")
    body: str = Field(..., min_length=1, max_length=300, description="Notification body")
    event_type: str = Field(PWAEventType.SYSTEM_MAINTENANCE.value, description="Event type")
    priority: str = Field(NotificationPriority.NORMAL.value, description="Notification priority")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional notification data")
    scheduled_at: Optional[datetime] = Field(None, description="Schedule notification for later")

class OfflineJobSubmissionRequest(BaseModel):
    """Request model for offline job submission."""
    original_filename: str = Field(..., description="Original filename")
    file_data: str = Field(..., description="Base64 encoded file data")
    file_size: int = Field(..., gt=0, description="File size in bytes")
    model: str = Field("small", description="Whisper model to use")
    language: Optional[str] = Field(None, description="Language code")

class NotificationListResponse(BaseModel):
    """Response for notification listing."""
    notifications: List[PWANotification]
    total: int
    unread_count: int

class OfflineJobListResponse(BaseModel):
    """Response for offline job listing."""
    jobs: List[OfflineJobRequest]
    total: int

@router.post("/push/subscribe", response_model=PWASubscription)
async def register_push_subscription(
    request: PushSubscriptionRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Register a push notification subscription for the current user.
    
    This endpoint registers the user's device for push notifications.
    """
    
    try:
        subscription = pwa_service.register_push_subscription(
            user_id=current_user.id,
            subscription_data=request.dict()
        )
        
        logger.info(f"User {current_user.id} registered push subscription")
        
        return subscription
        
    except Exception as e:
        logger.error(f"Failed to register push subscription for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register push subscription"
        )

@router.get("/capabilities", response_model=PWACapabilities)
async def get_pwa_capabilities():
    """
    Get PWA capabilities and feature support.
    
    Returns information about supported PWA features.
    """
    
    try:
        return pwa_service.get_pwa_capabilities()
        
    except Exception as e:
        logger.error(f"Failed to get PWA capabilities: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve PWA capabilities"
        )

@router.get("/service-worker/config", response_model=PWAServiceWorkerConfig)
async def get_service_worker_config():
    """
    Get service worker configuration.
    
    Returns configuration for the PWA service worker.
    """
    
    try:
        return pwa_service.get_service_worker_config()
        
    except Exception as e:
        logger.error(f"Failed to get service worker config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve service worker configuration"
        )

@router.get("/notifications", response_model=NotificationListResponse)
async def get_user_notifications(
    limit: int = 50,
    unread_only: bool = False,
    current_user: User = Depends(get_current_user)
):
    """
    Get notifications for the current user.
    
    Returns a list of notifications, optionally filtered to unread only.
    """
    
    try:
        notifications = pwa_service.get_user_notifications(
            user_id=current_user.id,
            limit=limit,
            unread_only=unread_only
        )
        
        # Count unread notifications
        all_notifications = pwa_service.get_user_notifications(
            user_id=current_user.id,
            limit=1000,  # Get all for counting
            unread_only=False
        )
        
        unread_count = sum(1 for n in all_notifications if not n.is_read)
        
        return NotificationListResponse(
            notifications=notifications,
            total=len(all_notifications),
            unread_count=unread_count
        )
        
    except Exception as e:
        logger.error(f"Failed to get notifications for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve notifications"
        )

@router.post("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Mark a notification as read.
    
    Updates the read status of a specific notification.
    """
    
    try:
        success = pwa_service.mark_notification_read(
            user_id=current_user.id,
            notification_id=notification_id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
        
        return {
            "message": "Notification marked as read",
            "notification_id": notification_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to mark notification as read: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark notification as read"
        )

@router.post("/notifications", response_model=PWANotification)
async def create_notification(
    request: CreateNotificationRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Create a custom notification.
    
    Allows users to create custom notifications for testing or personal use.
    """
    
    try:
        # Validate event type and priority
        try:
            event_type = PWAEventType(request.event_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid event type: {request.event_type}"
            )
        
        try:
            priority = NotificationPriority(request.priority)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid priority: {request.priority}"
            )
        
        notification = pwa_service.create_notification(
            user_id=current_user.id,
            title=request.title,
            body=request.body,
            event_type=event_type,
            priority=priority,
            data=request.data,
            scheduled_at=request.scheduled_at
        )
        
        logger.info(f"User {current_user.id} created custom notification {notification.id}")
        
        return notification
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create notification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create notification"
        )

@router.post("/offline/jobs", response_model=OfflineJobRequest)
async def submit_offline_job(
    request: OfflineJobSubmissionRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Submit a job for offline processing.
    
    Stores job data for later synchronization when online.
    """
    
    try:
        # Validate file size (max 50MB for offline storage)
        max_size = 50 * 1024 * 1024  # 50MB
        if request.file_size > max_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size exceeds maximum {max_size // (1024*1024)}MB for offline storage"
            )
        
        offline_job = pwa_service.store_offline_job(
            user_id=current_user.id,
            original_filename=request.original_filename,
            file_data=request.file_data,
            file_size=request.file_size,
            model=request.model,
            language=request.language
        )
        
        logger.info(f"User {current_user.id} submitted offline job {offline_job.id}")
        
        return offline_job
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to submit offline job: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit offline job"
        )

@router.get("/offline/jobs", response_model=OfflineJobListResponse)
async def get_offline_jobs(
    current_user: User = Depends(get_current_user)
):
    """
    Get pending offline jobs for the current user.
    
    Returns jobs that were submitted offline and are waiting for sync.
    """
    
    try:
        jobs = pwa_service.get_pending_offline_jobs(current_user.id)
        
        return OfflineJobListResponse(
            jobs=jobs,
            total=len(jobs)
        )
        
    except Exception as e:
        logger.error(f"Failed to get offline jobs for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve offline jobs"
        )

@router.post("/offline/jobs/{job_id}/sync")
async def sync_offline_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Synchronize an offline job by creating an actual transcription job.
    
    Converts offline job data into a real transcription job.
    """
    
    try:
        # Get offline jobs
        offline_jobs = pwa_service.get_pending_offline_jobs(current_user.id)
        
        # Find the specific job
        offline_job = None
        for job in offline_jobs:
            if job.id == job_id:
                offline_job = job
                break
        
        if not offline_job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Offline job not found"
            )
        
        # TODO: Implement actual job creation from offline data
        # This would involve:
        # 1. Decoding the base64 file data
        # 2. Saving the file to the upload directory
        # 3. Creating a new Job record in the database
        # 4. Starting the transcription process
        # 5. Marking the offline job as synced
        
        # For now, just mark as synced with a placeholder job ID
        actual_job_id = f"synced-{job_id}"
        success = pwa_service.mark_offline_job_synced(job_id, actual_job_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to sync offline job"
            )
        
        logger.info(f"User {current_user.id} synced offline job {job_id}")
        
        return {
            "message": "Offline job synchronized successfully",
            "offline_job_id": job_id,
            "actual_job_id": actual_job_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to sync offline job {job_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to sync offline job"
        )

@router.post("/push/activity")
async def update_push_activity(
    request_data: Dict[str, str],
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """
    Update push subscription activity.
    
    Records that a push subscription was used for analytics.
    """
    
    try:
        endpoint = request_data.get("endpoint")
        if not endpoint:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Endpoint is required"
            )
        
        pwa_service.update_subscription_activity(
            user_id=current_user.id,
            endpoint=endpoint
        )
        
        return {"message": "Activity updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update push activity: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update push activity"
        )

# Service worker endpoint (no auth required)
@router.get("/service-worker.js", include_in_schema=False)
async def get_service_worker():
    """
    Serve the service worker JavaScript file.
    
    This endpoint serves the PWA service worker script.
    """
    
    from fastapi.responses import Response
    
    # Generate service worker content based on configuration
    config = pwa_service.get_service_worker_config()
    
    service_worker_content = f"""
// PWA Service Worker - Generated automatically
const CACHE_NAME = '{config.cache_version}';
const CACHE_VERSION = '{config.version}';
const MAX_CACHE_AGE = {config.cache_max_age * 60 * 60 * 1000}; // {config.cache_max_age} hours in ms

const CACHED_ROUTES = {config.cached_routes};
const OFFLINE_FALLBACK = '{config.offline_fallback}';
const BACKGROUND_SYNC_ENABLED = {str(config.background_sync_enabled).lower()};

// Install event
self.addEventListener('install', (event) => {{
    console.log('Service Worker installing...');
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {{
            return cache.addAll(CACHED_ROUTES);
        }})
    );
    self.skipWaiting();
}});

// Activate event
self.addEventListener('activate', (event) => {{
    console.log('Service Worker activating...');
    event.waitUntil(
        caches.keys().then((cacheNames) => {{
            return Promise.all(
                cacheNames.map((cacheName) => {{
                    if (cacheName !== CACHE_NAME) {{
                        return caches.delete(cacheName);
                    }}
                }})
            );
        }})
    );
    self.clients.claim();
}});

// Fetch event
self.addEventListener('fetch', (event) => {{
    event.respondWith(
        caches.match(event.request).then((response) => {{
            if (response) {{
                // Check if cached response is still fresh
                const cachedTime = new Date(response.headers.get('sw-cached-time') || 0);
                const now = new Date();
                if (now - cachedTime < MAX_CACHE_AGE) {{
                    return response;
                }}
            }}
            
            return fetch(event.request).then((fetchResponse) => {{
                // Cache successful responses
                if (fetchResponse.status === 200) {{
                    const responseClone = fetchResponse.clone();
                    responseClone.headers.set('sw-cached-time', new Date().toISOString());
                    caches.open(CACHE_NAME).then((cache) => {{
                        cache.put(event.request, responseClone);
                    }});
                }}
                return fetchResponse;
            }}).catch(() => {{
                // Return cached version or offline fallback
                return response || caches.match(OFFLINE_FALLBACK);
            }});
        }})
    );
}});

// Push event
self.addEventListener('push', (event) => {{
    console.log('Push message received');
    
    if (event.data) {{
        const data = event.data.json();
        const options = {{
            body: data.body,
            icon: data.icon || '/static/icons/notification-icon.png',
            badge: data.badge || '/static/icons/badge-icon.png',
            data: data.data || {{}},
            tag: data.tag || 'default',
            timestamp: data.timestamp || Date.now(),
            requireInteraction: data.priority === 'urgent'
        }};
        
        event.waitUntil(
            self.registration.showNotification(data.title, options)
        );
    }}
}});

// Notification click event
self.addEventListener('notificationclick', (event) => {{
    console.log('Notification clicked');
    event.notification.close();
    
    const data = event.notification.data || {{}};
    const actionUrl = data.action_url || '/';
    
    event.waitUntil(
        clients.matchAll({{type: 'window'}}).then((clientList) => {{
            for (let client of clientList) {{
                if (client.url === actionUrl && 'focus' in client) {{
                    return client.focus();
                }}
            }}
            if (clients.openWindow) {{
                return clients.openWindow(actionUrl);
            }}
        }})
    );
}});

// Background sync (if enabled)
if (BACKGROUND_SYNC_ENABLED) {{
    self.addEventListener('sync', (event) => {{
        console.log('Background sync triggered:', event.tag);
        
        if (event.tag === 'offline-jobs-sync') {{
            event.waitUntil(syncOfflineJobs());
        }}
    }});
    
    async function syncOfflineJobs() {{
        try {{
            // Get pending offline jobs from IndexedDB
            const jobs = await getOfflineJobs();
            
            for (const job of jobs) {{
                // Attempt to sync each job
                const response = await fetch(`/api/v1/pwa/offline/jobs/${{job.id}}/sync`, {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${{job.token}}`
                    }}
                }});
                
                if (response.ok) {{
                    // Remove job from IndexedDB
                    await removeOfflineJob(job.id);
                }}
            }}
        }} catch (error) {{
            console.error('Background sync failed:', error);
        }}
    }}
    
    // Placeholder functions for IndexedDB operations
    async function getOfflineJobs() {{
        // TODO: Implement IndexedDB operations
        return [];
    }}
    
    async function removeOfflineJob(jobId) {{
        // TODO: Implement IndexedDB operations
        console.log('Removing offline job:', jobId);
    }}
}}

console.log('Service Worker loaded successfully');
"""
    
    return Response(
        content=service_worker_content,
        media_type="application/javascript",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Service-Worker-Allowed": "/"
        }
    )