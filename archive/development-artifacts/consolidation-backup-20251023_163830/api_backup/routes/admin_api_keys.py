#!/usr/bin/env python3
"""
T027 Advanced Features: Admin API Key Management Routes
Administrative routes for API key oversight and management.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from pydantic import BaseModel, Field

from api.orm_bootstrap import get_db
from api.services.api_key_service import api_key_service, APIKeyUsageStats
from api.services.users import get_current_admin
from api.models import User
from api.extended_models.api_keys import APIKey, APIKeyUsageLog, APIKeyStatus
from api.utils.logger import get_system_logger

logger = get_system_logger("admin_api_keys")

router = APIRouter(prefix="/admin/api-keys", tags=["admin", "api-keys"])

class AdminAPIKeyResponse(BaseModel):
    """Extended API key response for admin users."""
    key_id: str
    key_prefix: str
    name: str
    description: Optional[str]
    user_id: str
    username: Optional[str]  # User's username for display
    permissions: List[str]
    status: str
    created_at: datetime
    expires_at: Optional[datetime]
    last_used_at: Optional[datetime]
    usage_count: int
    last_used_ip: Optional[str]
    rate_limit_per_hour: Optional[int]
    daily_quota: Optional[int]
    monthly_quota: Optional[int]
    allowed_ips: Optional[List[str]]
    is_active: bool

class AdminAPIKeyListResponse(BaseModel):
    """Response for admin API key listing."""
    api_keys: List[AdminAPIKeyResponse]
    total: int
    page: int
    page_size: int

class APIKeySystemStats(BaseModel):
    """System-wide API key statistics."""
    total_keys: int
    active_keys: int
    revoked_keys: int
    expired_keys: int
    suspended_keys: int
    total_requests_24h: int
    total_requests_7d: int
    total_requests_30d: int
    top_users: List[Dict[str, Any]]
    top_endpoints: List[Dict[str, Any]]
    error_rate_24h: float

class AdminAPIKeyRevokeRequest(BaseModel):
    """Admin request for revoking an API key."""
    reason: str = Field(..., min_length=1, max_length=500, description="Required reason for admin revocation")
    notify_user: bool = Field(True, description="Whether to notify the user of revocation")

@router.get("/", response_model=AdminAPIKeyListResponse)
def list_all_api_keys(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Number of items per page"),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    search: Optional[str] = Query(None, description="Search by key name or user")
):
    """
    List all API keys in the system with admin oversight.
    """
    try:
        # Build query
        query = db.query(APIKey).join(User, User.id == APIKey.user_id, isouter=True)
        
        # Apply filters
        if status_filter:
            query = query.filter(APIKey.status == status_filter)
        
        if user_id:
            query = query.filter(APIKey.user_id == user_id)
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    APIKey.name.ilike(search_term),
                    User.username.ilike(search_term)
                )
            )
        
        # Get total count
        total = query.count()
        
        # Apply pagination and ordering
        api_keys = query.order_by(desc(APIKey.created_at)).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
        
        # Convert to response format
        response_keys = []
        for key in api_keys:
            # Get associated user
            user = db.query(User).filter(User.id == key.user_id).first()
            
            response_keys.append(AdminAPIKeyResponse(
                key_id=key.key_id,
                key_prefix=key.key_prefix,
                name=key.name,
                description=key.description,
                user_id=key.user_id,
                username=user.username if user else "Unknown",
                permissions=key.permissions_list,
                status=key.status,
                created_at=key.created_at,
                expires_at=key.expires_at,
                last_used_at=key.last_used_at,
                usage_count=key.usage_count,
                last_used_ip=key.last_used_ip,
                rate_limit_per_hour=key.rate_limit_per_hour,
                daily_quota=key.daily_quota,
                monthly_quota=key.monthly_quota,
                allowed_ips=key.allowed_ips,
                is_active=key.is_active
            ))
        
        return AdminAPIKeyListResponse(
            api_keys=response_keys,
            total=total,
            page=page,
            page_size=page_size
        )
        
    except Exception as e:
        logger.error(f"Failed to list API keys for admin: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve API keys"
        )

@router.get("/stats", response_model=APIKeySystemStats)
def get_api_key_system_stats(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Get system-wide API key statistics.
    """
    try:
        # Basic key counts
        total_keys = db.query(APIKey).count()
        active_keys = db.query(APIKey).filter(APIKey.status == APIKeyStatus.ACTIVE.value).count()
        revoked_keys = db.query(APIKey).filter(APIKey.status == APIKeyStatus.REVOKED.value).count()
        expired_keys = db.query(APIKey).filter(APIKey.status == APIKeyStatus.EXPIRED.value).count()
        suspended_keys = db.query(APIKey).filter(APIKey.status == APIKeyStatus.SUSPENDED.value).count()
        
        # Time ranges for usage stats
        now = datetime.utcnow()
        last_24h = now - timedelta(hours=24)
        last_7d = now - timedelta(days=7)
        last_30d = now - timedelta(days=30)
        
        # Request counts
        total_requests_24h = db.query(APIKeyUsageLog).filter(
            APIKeyUsageLog.timestamp >= last_24h
        ).count()
        
        total_requests_7d = db.query(APIKeyUsageLog).filter(
            APIKeyUsageLog.timestamp >= last_7d
        ).count()
        
        total_requests_30d = db.query(APIKeyUsageLog).filter(
            APIKeyUsageLog.timestamp >= last_30d
        ).count()
        
        # Error rate (24h)
        error_count_24h = db.query(APIKeyUsageLog).filter(
            and_(
                APIKeyUsageLog.timestamp >= last_24h,
                APIKeyUsageLog.status_code >= 400
            )
        ).count()
        
        error_rate_24h = (error_count_24h / total_requests_24h * 100) if total_requests_24h > 0 else 0.0
        
        # Top users by usage (30d)
        top_users_query = db.query(
            APIKey.user_id,
            User.username,
            func.count(APIKeyUsageLog.id).label('request_count')
        ).join(
            APIKeyUsageLog, APIKeyUsageLog.api_key_id == APIKey.id
        ).join(
            User, User.id == APIKey.user_id
        ).filter(
            APIKeyUsageLog.timestamp >= last_30d
        ).group_by(
            APIKey.user_id, User.username
        ).order_by(
            desc('request_count')
        ).limit(10).all()
        
        top_users = [
            {
                "user_id": user.user_id,
                "username": user.username,
                "request_count": user.request_count
            }
            for user in top_users_query
        ]
        
        # Top endpoints (30d)
        top_endpoints_query = db.query(
            APIKeyUsageLog.endpoint,
            func.count(APIKeyUsageLog.id).label('request_count')
        ).filter(
            APIKeyUsageLog.timestamp >= last_30d
        ).group_by(
            APIKeyUsageLog.endpoint
        ).order_by(
            desc('request_count')
        ).limit(10).all()
        
        top_endpoints = [
            {
                "endpoint": endpoint.endpoint,
                "request_count": endpoint.request_count
            }
            for endpoint in top_endpoints_query
        ]
        
        return APIKeySystemStats(
            total_keys=total_keys,
            active_keys=active_keys,
            revoked_keys=revoked_keys,
            expired_keys=expired_keys,
            suspended_keys=suspended_keys,
            total_requests_24h=total_requests_24h,
            total_requests_7d=total_requests_7d,
            total_requests_30d=total_requests_30d,
            top_users=top_users,
            top_endpoints=top_endpoints,
            error_rate_24h=round(error_rate_24h, 2)
        )
        
    except Exception as e:
        logger.error(f"Failed to get API key system stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system statistics"
        )

@router.post("/{key_id}/revoke")
def admin_revoke_api_key(
    key_id: str,
    request: AdminAPIKeyRevokeRequest,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Revoke an API key as an administrator.
    """
    try:
        # Find the API key
        api_key = db.query(APIKey).filter(APIKey.key_id == key_id).first()
        
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found"
            )
        
        if api_key.status == APIKeyStatus.REVOKED.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="API key is already revoked"
            )
        
        # Revoke the key
        api_key.status = APIKeyStatus.REVOKED.value
        api_key.revoked_at = datetime.utcnow()
        api_key.revoked_by = str(current_admin.id)
        api_key.revoked_reason = f"Admin revocation by {current_admin.username}: {request.reason}"
        
        db.commit()
        
        # Log the admin action
        logger.info(f"Admin {current_admin.username} revoked API key {key_id}. Reason: {request.reason}")
        
        # TODO: Send notification to user if request.notify_user is True
        
        return {"message": "API key revoked successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to revoke API key {key_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke API key"
        )

@router.post("/{key_id}/suspend")
def suspend_api_key(
    key_id: str,
    reason: str = Query(..., description="Reason for suspension"),
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Suspend an API key temporarily.
    """
    try:
        # Find the API key
        api_key = db.query(APIKey).filter(APIKey.key_id == key_id).first()
        
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found"
            )
        
        if api_key.status != APIKeyStatus.ACTIVE.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Can only suspend active API keys"
            )
        
        # Suspend the key
        api_key.status = APIKeyStatus.SUSPENDED.value
        
        # Add suspension info to metadata
        suspension_info = {
            "suspended_at": datetime.utcnow().isoformat(),
            "suspended_by": current_admin.username,
            "suspension_reason": reason
        }
        
        if api_key.metadata:
            api_key.metadata.update(suspension_info)
        else:
            api_key.metadata = suspension_info
        
        db.commit()
        
        logger.info(f"Admin {current_admin.username} suspended API key {key_id}. Reason: {reason}")
        
        return {"message": "API key suspended successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to suspend API key {key_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to suspend API key"
        )

@router.post("/{key_id}/unsuspend")
def unsuspend_api_key(
    key_id: str,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Unsuspend a suspended API key.
    """
    try:
        # Find the API key
        api_key = db.query(APIKey).filter(APIKey.key_id == key_id).first()
        
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found"
            )
        
        if api_key.status != APIKeyStatus.SUSPENDED.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="API key is not currently suspended"
            )
        
        # Check if key would be expired
        if api_key.expires_at and api_key.expires_at < datetime.utcnow():
            api_key.status = APIKeyStatus.EXPIRED.value
        else:
            api_key.status = APIKeyStatus.ACTIVE.value
        
        # Add unsuspension info to metadata
        if api_key.metadata:
            api_key.metadata.update({
                "unsuspended_at": datetime.utcnow().isoformat(),
                "unsuspended_by": current_admin.username
            })
        
        db.commit()
        
        logger.info(f"Admin {current_admin.username} unsuspended API key {key_id}")
        
        return {"message": "API key unsuspended successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to unsuspend API key {key_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to unsuspend API key"
        )

@router.get("/{key_id}/usage", response_model=APIKeyUsageStats)
def get_api_key_usage_admin(
    key_id: str,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
    days: int = Query(30, ge=1, le=365, description="Number of days of usage data")
):
    """
    Get detailed usage statistics for any API key (admin access).
    """
    try:
        # Verify the API key exists
        api_key = db.query(APIKey).filter(APIKey.key_id == key_id).first()
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found"
            )
        
        # Get usage statistics
        usage_stats = api_key_service.get_api_key_usage_stats(
            db=db,
            api_key_id=key_id,
            days=days
        )
        
        return usage_stats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get usage stats for API key {key_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve usage statistics"
        )

@router.post("/cleanup/expired")
def cleanup_expired_keys(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Clean up expired API keys by marking them as expired.
    """
    try:
        expired_count = api_key_service.cleanup_expired_keys(db)
        
        logger.info(f"Admin {current_admin.username} cleaned up {expired_count} expired API keys")
        
        return {
            "message": f"Cleaned up {expired_count} expired API keys",
            "expired_count": expired_count
        }
        
    except Exception as e:
        logger.error(f"Failed to cleanup expired keys: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cleanup expired keys"
        )