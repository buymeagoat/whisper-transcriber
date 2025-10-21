#!/usr/bin/env python3
"""
T027 Advanced Features: API Key Management Routes
FastAPI routes for API key creation, management, and monitoring.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from api.orm_bootstrap import get_db
from api.services.api_key_service import (
    api_key_service,
    APIKeyCreateRequest,
    APIKeyResponse,
    APIKeyWithSecret,
    APIKeyUsageStats
)
from api.services.users import get_current_user
from api.models import User
from api.utils.logger import get_system_logger

logger = get_system_logger("api_keys_routes")

router = APIRouter(prefix="/api/keys", tags=["api-keys"])

class APIKeyListResponse(BaseModel):
    """Response for listing API keys."""
    api_keys: List[APIKeyResponse]
    total: int

class APIKeyRevokeRequest(BaseModel):
    """Request for revoking an API key."""
    reason: Optional[str] = Field(None, max_length=500, description="Reason for revocation")

@router.post("/", response_model=APIKeyWithSecret)
def create_api_key(
    request: APIKeyCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new API key for the authenticated user.
    
    **Important**: The API key secret is only shown once during creation.
    Make sure to save it securely.
    """
    try:
        api_key = api_key_service.create_api_key(
            db=db,
            user_id=str(current_user.id),
            request=request
        )
        
        logger.info(f"Created API key '{request.name}' for user {current_user.username}")
        return api_key
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create API key: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create API key"
        )

@router.get("/", response_model=APIKeyListResponse)
def list_api_keys(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    include_revoked: bool = Query(False, description="Include revoked keys in results")
):
    """
    List all API keys for the authenticated user.
    """
    try:
        api_keys = api_key_service.get_user_api_keys(
            db=db,
            user_id=str(current_user.id)
        )
        
        # Filter out revoked keys if requested
        if not include_revoked:
            api_keys = [key for key in api_keys if key.status != "revoked"]
        
        return APIKeyListResponse(
            api_keys=api_keys,
            total=len(api_keys)
        )
        
    except Exception as e:
        logger.error(f"Failed to list API keys: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve API keys"
        )

@router.get("/{key_id}", response_model=APIKeyResponse)
def get_api_key(
    key_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get details for a specific API key.
    """
    try:
        api_keys = api_key_service.get_user_api_keys(
            db=db,
            user_id=str(current_user.id)
        )
        
        # Find the specific key
        api_key = next((key for key in api_keys if key.key_id == key_id), None)
        
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found"
            )
        
        return api_key
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get API key {key_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve API key"
        )

@router.post("/{key_id}/revoke")
def revoke_api_key(
    key_id: str,
    request: APIKeyRevokeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Revoke an API key.
    
    Once revoked, the API key cannot be used and cannot be restored.
    """
    try:
        success = api_key_service.revoke_api_key(
            db=db,
            user_id=str(current_user.id),
            key_id=key_id,
            reason=request.reason
        )
        
        if success:
            logger.info(f"Revoked API key {key_id} for user {current_user.username}")
            return {"message": "API key revoked successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to revoke API key {key_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke API key"
        )

@router.get("/{key_id}/usage", response_model=APIKeyUsageStats)
def get_api_key_usage(
    key_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    days: int = Query(30, ge=1, le=365, description="Number of days of usage data to retrieve")
):
    """
    Get usage statistics for an API key.
    """
    try:
        # Verify the user owns this API key
        api_keys = api_key_service.get_user_api_keys(
            db=db,
            user_id=str(current_user.id)
        )
        
        user_key = next((key for key in api_keys if key.key_id == key_id), None)
        if not user_key:
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

@router.post("/{key_id}/regenerate", response_model=APIKeyWithSecret)
def regenerate_api_key(
    key_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Regenerate an API key.
    
    This creates a new API key with the same settings as the old one,
    and automatically revokes the old key.
    
    **Important**: The new API key secret is only shown once.
    """
    try:
        # Get the existing API key
        api_keys = api_key_service.get_user_api_keys(
            db=db,
            user_id=str(current_user.id)
        )
        
        existing_key = next((key for key in api_keys if key.key_id == key_id), None)
        if not existing_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found"
            )
        
        if existing_key.status == "revoked":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot regenerate a revoked API key"
            )
        
        # Create new API key with same settings
        expires_days = None
        if existing_key.expires_at:
            expires_days = (existing_key.expires_at - datetime.utcnow()).days
            expires_days = max(1, expires_days)  # At least 1 day
        
        new_key_request = APIKeyCreateRequest(
            name=f"{existing_key.name} (regenerated)",
            description=existing_key.description,
            permissions=existing_key.permissions,
            expires_days=expires_days,
            rate_limit_per_hour=existing_key.rate_limit_per_hour,
            daily_quota=existing_key.daily_quota,
            monthly_quota=existing_key.monthly_quota,
            allowed_ips=existing_key.allowed_ips
        )
        
        # Create new key
        new_api_key = api_key_service.create_api_key(
            db=db,
            user_id=str(current_user.id),
            request=new_key_request
        )
        
        # Revoke old key
        api_key_service.revoke_api_key(
            db=db,
            user_id=str(current_user.id),
            key_id=key_id,
            reason="Regenerated - replaced with new key"
        )
        
        logger.info(f"Regenerated API key {key_id} for user {current_user.username}")
        return new_api_key
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to regenerate API key {key_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to regenerate API key"
        )

@router.get("/permissions/available")
def get_available_permissions(
    current_user: User = Depends(get_current_user)
):
    """
    Get list of available API key permissions.
    """
    from api.models.api_keys import APIKeyPermission
    
    permissions = [
        {
            "value": perm.value,
            "description": {
                "read": "Read access to jobs and data",
                "write": "Create and modify jobs",
                "delete": "Delete jobs and data", 
                "admin": "Administrative access (requires admin role)",
                "batch": "Batch processing permissions",
                "analytics": "Access to usage analytics"
            }.get(perm.value, "")
        }
        for perm in APIKeyPermission
    ]
    
    # Filter admin permission if user is not admin
    if not current_user.is_admin:
        permissions = [p for p in permissions if p["value"] != "admin"]
    
    return {"permissions": permissions}