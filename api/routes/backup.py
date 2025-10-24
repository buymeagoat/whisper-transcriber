"""
Backup Management API - Admin Endpoints for Backup Operations

NOTE: Backup service is currently disabled during architecture consolidation.
This module provides a minimal stub interface until the backup service is migrated.
"""

from fastapi import APIRouter, HTTPException, status
import logging

logger = logging.getLogger(__name__)

# Create backup management router
backup_router = APIRouter(prefix="/admin/backup", tags=["backup"])

@backup_router.get("/status")
async def backup_status():
    """Get backup service status - currently disabled."""
    return {
        "status": "disabled",
        "message": "Backup service temporarily disabled during architecture consolidation",
        "available": False,
        "reason": "Service migration in progress"
    }

@backup_router.get("/health")
async def backup_health():
    """Backup service health check - disabled."""
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Backup service is temporarily unavailable during system consolidation"
    )
