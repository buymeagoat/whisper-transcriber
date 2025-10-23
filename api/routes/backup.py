"""
Backup Management API - Admin Endpoints for Backup Operations

Provides REST API endpoints for backup management, monitoring, and recovery
operations. Integrated with the main FastAPI application.
"""

from datetime import datetime
from typing import Optional, Dict, List, Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from pydantic import BaseModel, Field
import logging

from app.backup.service import get_backup_service, BackupService

logger = logging.getLogger(__name__)

# Create backup management router
backup_router = APIRouter(prefix="/admin/backup", tags=["backup"])


# ===== Pydantic Models for API Requests/Responses =====

class BackupRequest(BaseModel):
    """Request model for creating backups."""
    backup_type: str = Field(default="full", description="Type of backup: 'full' or 'incremental'")
    upload_to_storage: bool = Field(default=True, description="Upload backup to configured storage backends")
    
    class Config:
        schema_extra = {
            "example": {
                "backup_type": "full",
                "upload_to_storage": True
            }
        }


class RecoveryRequest(BaseModel):
    """Request model for recovery operations."""
    recovery_type: str = Field(description="Type of recovery: 'database', 'files', or 'full'")
    backup_id: Optional[str] = Field(None, description="Specific backup ID to restore from")
    point_in_time: Optional[str] = Field(None, description="ISO timestamp for point-in-time recovery")
    file_patterns: Optional[List[str]] = Field(None, description="File patterns to restore")
    restore_to_original: bool = Field(True, description="Restore files to original locations")
    target_directory: Optional[str] = Field(None, description="Alternative restore directory")
    
    class Config:
        schema_extra = {
            "example": {
                "recovery_type": "database",
                "backup_id": "full_20251015_143000",
                "point_in_time": "2025-10-15T14:30:00",
                "restore_to_original": True
            }
        }


class BackupStatusResponse(BaseModel):
    """Response model for backup status."""
    timestamp: str
    service_running: bool
    backup_system: Dict[str, Any]
    configuration: Dict[str, Any]
    statistics: Dict[str, Any]


class BackupOperationResponse(BaseModel):
    """Response model for backup operations."""
    operation_id: str
    type: str
    success: bool
    started: str
    completed: Optional[str] = None
    total_size: Optional[int] = None
    error: Optional[str] = None


class RecoveryOperationResponse(BaseModel):
    """Response model for recovery operations."""
    recovery_id: str
    type: str
    success: bool
    started: str
    completed: Optional[str] = None
    error: Optional[str] = None


# ===== Helper Functions =====

def get_backup_service_instance() -> BackupService:
    """Get backup service instance with error handling."""
    try:
        return get_backup_service()
    except Exception as e:
        logger.error(f"Failed to get backup service: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Backup service unavailable: {str(e)}"
        )


# ===== API Endpoints =====

@backup_router.get("/status", response_model=BackupStatusResponse)
async def get_backup_status():
    """
    Get comprehensive backup system status.
    
    Returns current status of backup service, recent operations,
    configuration details, and system statistics.
    """
    try:
        backup_service = get_backup_service_instance()
        status = backup_service.get_service_status()
        
        return BackupStatusResponse(
            timestamp=datetime.utcnow().isoformat(),
            service_running=status.get("service", {}).get("running", False),
            backup_system=status.get("backup_system", {}),
            configuration=status.get("configuration", {}),
            statistics=status.get("service", {}).get("statistics", {})
        )
        
    except Exception as e:
        logger.error(f"Failed to get backup status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get backup status: {str(e)}"
        )


@backup_router.post("/create", response_model=BackupOperationResponse)
async def create_backup(
    request: BackupRequest,
    background_tasks: BackgroundTasks
):
    """
    Create a manual backup.
    
    Supports both full and incremental backups with optional
    upload to configured storage backends.
    """
    try:
        backup_service = get_backup_service_instance()
        
        # Execute backup in background task for large operations
        def run_backup():
            return backup_service.create_manual_backup(
                backup_type=request.backup_type,
                upload_to_storage=request.upload_to_storage
            )
        
        # For API responsiveness, we could run this in background
        # For now, execute synchronously for immediate feedback
        result = run_backup()
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Backup operation failed to start"
            )
        
        return BackupOperationResponse(
            operation_id=result.get("operation_id", "unknown"),
            type=result.get("type", request.backup_type),
            success=result.get("success", False),
            started=result.get("started", datetime.utcnow().isoformat()),
            completed=result.get("completed"),
            total_size=result.get("total_size"),
            error=result.get("error")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create backup: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create backup: {str(e)}"
        )


@backup_router.post("/recovery", response_model=RecoveryOperationResponse)
async def create_recovery(request: RecoveryRequest):
    """
    Perform system recovery from backups.
    
    Supports database recovery, file recovery, and full system recovery
    with various configuration options.
    """
    try:
        backup_service = get_backup_service_instance()
        
        # Prepare recovery parameters
        recovery_kwargs = {}
        
        if request.backup_id:
            recovery_kwargs["backup_id"] = request.backup_id
        
        if request.point_in_time:
            recovery_kwargs["point_in_time"] = request.point_in_time
        
        if request.recovery_type == "files":
            if request.file_patterns:
                recovery_kwargs["file_patterns"] = request.file_patterns
            recovery_kwargs["restore_to_original"] = request.restore_to_original
            if request.target_directory:
                recovery_kwargs["target_directory"] = request.target_directory
        
        # Execute recovery operation
        result = backup_service.create_recovery(
            recovery_type=request.recovery_type,
            **recovery_kwargs
        )
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Recovery operation failed to start"
            )
        
        return RecoveryOperationResponse(
            recovery_id=result.get("recovery_id", "unknown"),
            type=result.get("type", request.recovery_type),
            success=result.get("success", False),
            started=result.get("started", datetime.utcnow().isoformat()),
            completed=result.get("completed"),
            error=result.get("error")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create recovery: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create recovery: {str(e)}"
        )


@backup_router.get("/list")
async def list_available_backups():
    """
    List all available backups for recovery.
    
    Returns categorized list of database backups, WAL backups,
    file backups, and full system backups.
    """
    try:
        backup_service = get_backup_service_instance()
        available_backups = backup_service.recovery_manager.list_available_backups()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "available_backups": available_backups
        }
        
    except Exception as e:
        logger.error(f"Failed to list available backups: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list available backups: {str(e)}"
        )


@backup_router.post("/cleanup")
async def cleanup_backups():
    """
    Clean up expired backups.
    
    Removes backups that have exceeded their retention period
    across all backup types and storage backends.
    """
    try:
        backup_service = get_backup_service_instance()
        result = backup_service.cleanup_backups()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "cleanup_result": result
        }
        
    except Exception as e:
        logger.error(f"Failed to cleanup backups: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cleanup backups: {str(e)}"
        )


@backup_router.post("/test")
async def test_backup_system():
    """
    Test backup and recovery system functionality.
    
    Performs comprehensive testing of backup creation, recovery procedures,
    and storage backend connectivity without affecting production data.
    """
    try:
        backup_service = get_backup_service_instance()
        test_result = backup_service.test_backup_system()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "test_result": test_result
        }
        
    except Exception as e:
        logger.error(f"Failed to test backup system: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to test backup system: {str(e)}"
        )


@backup_router.post("/validate-recovery")
async def validate_system_recovery():
    """
    Validate system state after recovery operations.
    
    Checks database integrity, file consistency, and overall
    system health to ensure recovery was successful.
    """
    try:
        backup_service = get_backup_service_instance()
        validation_result = backup_service.recovery_manager.validate_system_recovery()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "validation_result": validation_result
        }
        
    except Exception as e:
        logger.error(f"Failed to validate system recovery: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate system recovery: {str(e)}"
        )


@backup_router.get("/health")
async def backup_health_check():
    """
    Simple health check for backup system.
    
    Returns basic health status and connectivity information
    for monitoring and alerting systems.
    """
    try:
        backup_service = get_backup_service_instance()
        status = backup_service.get_service_status()
        
        # Simple health indicators
        is_healthy = (
            status.get("service", {}).get("running", False) and
            len(status.get("backup_system", {}).get("storage_backends", [])) > 0
        )
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "healthy": is_healthy,
            "service_running": status.get("service", {}).get("running", False),
            "storage_backends_count": len(status.get("backup_system", {}).get("storage_backends", [])),
            "last_successful_backup": status.get("service", {}).get("statistics", {}).get("last_full_backup")
        }
        
    except Exception as e:
        logger.error(f"Backup health check failed: {e}")
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "healthy": False,
            "error": str(e)
        }


# ===== Integration Helper Functions =====

def initialize_backup_service():
    """
    Initialize backup service with default configuration.
    Call this during application startup.
    """
    try:
        backup_service = get_backup_service()
        # Don't auto-start the service - let admin control when to start
        logger.info("Backup service initialized and ready")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize backup service: {e}")
        return False


def start_backup_service_if_configured():
    """
    Start backup service if properly configured.
    Call this during application startup if auto-start is desired.
    """
    try:
        backup_service = get_backup_service()
        
        # Check if service should auto-start
        status = backup_service.get_service_status()
        if status.get("configuration", {}).get("scheduling_enabled", False):
            backup_service.start()
            logger.info("Backup service started with scheduling enabled")
        else:
            logger.info("Backup service ready but not started (scheduling disabled)")
        
        return True
    except Exception as e:
        logger.error(f"Failed to start backup service: {e}")
        return False


def shutdown_backup_service():
    """
    Gracefully shutdown backup service.
    Call this during application shutdown.
    """
    try:
        backup_service = get_backup_service()
        backup_service.stop()
        logger.info("Backup service shutdown completed")
    except Exception as e:
        logger.error(f"Error during backup service shutdown: {e}")


# Export the router and helper functions
__all__ = [
    "backup_router",
    "initialize_backup_service", 
    "start_backup_service_if_configured",
    "shutdown_backup_service"
]
