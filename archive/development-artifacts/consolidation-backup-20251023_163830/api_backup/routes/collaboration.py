"""
T036: Real-time Collaboration Features - WebSocket Routes
API routes for WebSocket-based collaborative editing functionality.
"""

import json
import logging
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from ..orm_bootstrap import get_db
from ..services.collaboration import handle_websocket_connection, get_collaboration_stats
from ..services.users import get_current_user
from ..models import User
from ..utils.logger import get_logger

logger = get_logger("collaboration_routes")

router = APIRouter(prefix="/collaboration", tags=["collaboration"])


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: int,
    token: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for real-time collaboration.
    
    Args:
        websocket: WebSocket connection
        user_id: ID of the connecting user
        token: Authentication token (optional for development)
        db: Database session
    """
    try:
        # Authenticate user (in production, implement proper JWT validation)
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="User not found")
            return
        
        # Handle the WebSocket connection
        await handle_websocket_connection(websocket, user.id, user.username)
    
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        try:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason="Internal server error")
        except:
            pass


@router.get("/stats")
async def get_collaboration_statistics(
    current_user: User = Depends(get_current_user)
):
    """
    Get current collaboration system statistics.
    
    Returns:
        Dictionary containing collaboration metrics
    """
    try:
        # Check if user is admin (optional restriction)
        if current_user.role != "admin":
            # For non-admin users, return limited stats
            stats = get_collaboration_stats()
            return {
                "active_connections": stats["active_connections"],
                "active_document_sessions": stats["active_document_sessions"]
            }
        
        # Full stats for admin users
        return get_collaboration_stats()
    
    except Exception as e:
        logger.error(f"Error getting collaboration stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve collaboration statistics"
        )


@router.get("/health")
async def collaboration_health_check():
    """
    Health check endpoint for collaboration service.
    
    Returns:
        Health status of the collaboration system
    """
    try:
        stats = get_collaboration_stats()
        
        return {
            "status": "healthy",
            "service": "collaboration",
            "timestamp": "2025-10-22T14:20:00Z",
            "metrics": {
                "active_connections": stats["active_connections"],
                "active_sessions": stats["active_document_sessions"],
                "total_participants": stats["total_participants"]
            }
        }
    
    except Exception as e:
        logger.error(f"Collaboration health check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "service": "collaboration",
                "error": str(e)
            }
        )


@router.post("/document/{document_id}/invite")
async def invite_user_to_document(
    document_id: str,
    invited_user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Invite a user to collaborate on a document.
    
    Args:
        document_id: ID of the document to collaborate on
        invited_user_id: ID of the user to invite
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        Invitation details
    """
    try:
        # Verify invited user exists
        invited_user = db.query(User).filter(User.id == invited_user_id).first()
        if not invited_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invited user not found"
            )
        
        # TODO: Implement proper document ownership/permission checking
        # For now, any authenticated user can invite others
        
        # TODO: Implement invitation system (email, notifications, etc.)
        # For now, return basic invitation details
        
        return {
            "document_id": document_id,
            "invited_user": {
                "id": invited_user.id,
                "username": invited_user.username
            },
            "invited_by": {
                "id": current_user.id,
                "username": current_user.username
            },
            "status": "invited",
            "message": f"User {invited_user.username} has been invited to collaborate on document {document_id}"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error inviting user to document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send collaboration invitation"
        )


@router.get("/document/{document_id}/participants")
async def get_document_participants(
    document_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get current participants for a document.
    
    Args:
        document_id: ID of the document
        current_user: Current authenticated user
    
    Returns:
        List of current participants
    """
    try:
        stats = get_collaboration_stats()
        document_stats = stats.get("document_stats", {})
        
        if document_id not in document_stats:
            return {
                "document_id": document_id,
                "participants": [],
                "participant_count": 0
            }
        
        # TODO: Get actual participant details from collaboration manager
        # For now, return basic stats
        doc_info = document_stats[document_id]
        
        return {
            "document_id": document_id,
            "participant_count": doc_info["participants"],
            "version": doc_info["version"],
            "edit_count": doc_info["edit_count"],
            "message": f"Document has {doc_info['participants']} active participants"
        }
    
    except Exception as e:
        logger.error(f"Error getting document participants: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve document participants"
        )


@router.post("/document/{document_id}/lock")
async def lock_document_for_editing(
    document_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Lock a document for exclusive editing (optional feature).
    
    Args:
        document_id: ID of the document to lock
        current_user: Current authenticated user
    
    Returns:
        Lock status
    """
    try:
        # TODO: Implement document locking mechanism
        # This is a placeholder for future implementation
        
        return {
            "document_id": document_id,
            "locked_by": {
                "id": current_user.id,
                "username": current_user.username
            },
            "locked_at": "2025-10-22T14:20:00Z",
            "status": "locked",
            "message": "Document locked for exclusive editing"
        }
    
    except Exception as e:
        logger.error(f"Error locking document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to lock document"
        )


@router.delete("/document/{document_id}/lock")
async def unlock_document(
    document_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Unlock a document to allow collaborative editing.
    
    Args:
        document_id: ID of the document to unlock
        current_user: Current authenticated user
    
    Returns:
        Unlock status
    """
    try:
        # TODO: Implement document unlocking mechanism
        # This is a placeholder for future implementation
        
        return {
            "document_id": document_id,
            "unlocked_by": {
                "id": current_user.id,
                "username": current_user.username
            },
            "unlocked_at": "2025-10-22T14:20:00Z",
            "status": "unlocked",
            "message": "Document unlocked for collaborative editing"
        }
    
    except Exception as e:
        logger.error(f"Error unlocking document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to unlock document"
        )