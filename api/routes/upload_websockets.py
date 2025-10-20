"""
WebSocket Upload Progress Tracking for T025 Phase 5: File Upload Optimization

Provides real-time WebSocket endpoints for monitoring upload progress,
chunk status updates, and error notifications during chunked file uploads.
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from api.services.enhanced_websocket_service import EnhancedWebSocketService
from api.services.chunked_upload_service import chunked_upload_service
from api.utils.logger import get_system_logger
import asyncio
import json

logger = get_system_logger("upload_websocket")

router = APIRouter(prefix="/ws/uploads", tags=["upload-websockets"])


async def get_user_id_from_websocket(websocket: WebSocket) -> str:
    """Extract user ID from WebSocket headers or query params."""
    # Check query parameters first
    user_id = websocket.query_params.get("user_id")
    if user_id:
        return user_id
    
    # Check headers
    user_id = websocket.headers.get("X-User-ID")
    if user_id:
        return user_id
    
    # Default for development
    return "default-user"


@router.websocket("/{session_id}/progress")
async def websocket_upload_progress(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time upload progress updates."""
    await websocket.accept()
    
    try:
        user_id = await get_user_id_from_websocket(websocket)
        
        # Verify session exists and user has access
        session = await chunked_upload_service._load_session(session_id)
        if not session:
            await websocket.send_json({
                "error": "Upload session not found",
                "session_id": session_id
            })
            await websocket.close(code=4004)
            return
        
        if session.user_id != user_id:
            await websocket.send_json({
                "error": "Access denied to upload session",
                "session_id": session_id
            })
            await websocket.close(code=4003)
            return
        
        # Register connection with WebSocket service
        # Note: In production, get service instance from app state
        # connection_id = await websocket_service.connect(websocket, user_id)
        
        # Send initial status
        status = await chunked_upload_service.get_upload_status(session_id, user_id)
        await websocket.send_json({
            "type": "initial_status",
            "session_id": session_id,
            "data": status
        })
        
        logger.info(f"WebSocket connected for upload session {session_id} (user: {user_id})")
        
        # Keep connection alive and handle messages
        while True:
            try:
                # Wait for messages from client
                message = await websocket.receive_text()
                data = json.loads(message)
                
                # Handle different message types
                if data.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                
                elif data.get("type") == "get_status":
                    status = await chunked_upload_service.get_upload_status(session_id, user_id)
                    await websocket.send_json({
                        "type": "status_update",
                        "session_id": session_id,
                        "data": status
                    })
                
                elif data.get("type") == "get_missing_chunks":
                    status = await chunked_upload_service.get_upload_status(session_id, user_id)
                    await websocket.send_json({
                        "type": "missing_chunks",
                        "session_id": session_id,
                        "missing_chunks": status.get("missing_chunks", [])
                    })
                
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                await websocket.send_json({
                    "error": "Invalid JSON message"
                })
            except Exception as e:
                logger.error(f"Error in upload WebSocket: {e}")
                await websocket.send_json({
                    "error": str(e)
                })
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for upload session {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error for upload session {session_id}: {e}")
    finally:
        # Cleanup connection
        try:
            # await websocket_service.disconnect(websocket)
            pass
        except:
            pass


@router.websocket("/user/{user_id}/notifications")
async def websocket_user_upload_notifications(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for all upload notifications for a user."""
    await websocket.accept()
    
    try:
        # Register connection
        # connection_id = await websocket_service.connect(websocket, user_id)
        
        # Send welcome message
        await websocket.send_json({
            "type": "connected",
            "user_id": user_id,
            "message": "Connected to upload notifications"
        })
        
        logger.info(f"User upload notifications WebSocket connected for user {user_id}")
        
        # Keep connection alive
        while True:
            try:
                message = await websocket.receive_text()
                data = json.loads(message)
                
                if data.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                
                elif data.get("type") == "list_active_uploads":
                    # Get user's active upload sessions
                    active_uploads = []
                    for sid, session in chunked_upload_service.sessions.items():
                        if session.user_id == user_id and session.status.value in ["active", "assembling"]:
                            upload_info = {
                                "session_id": sid,
                                "filename": session.original_filename,
                                "status": session.status.value,
                                "progress": round((len(session.uploaded_chunks) / session.total_chunks) * 100, 2),
                                "uploaded_chunks": len(session.uploaded_chunks),
                                "total_chunks": session.total_chunks
                            }
                            active_uploads.append(upload_info)
                    
                    await websocket.send_json({
                        "type": "active_uploads",
                        "uploads": active_uploads
                    })
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error in user upload notifications WebSocket: {e}")
                
    except WebSocketDisconnect:
        logger.info(f"User upload notifications WebSocket disconnected for user {user_id}")
    except Exception as e:
        logger.error(f"User upload notifications WebSocket error for user {user_id}: {e}")
    finally:
        try:
            # await websocket_service.disconnect(websocket)
            pass
        except:
            pass


@router.websocket("/admin/monitoring")
async def websocket_admin_upload_monitoring(websocket: WebSocket):
    """WebSocket endpoint for admin monitoring of all upload activities."""
    await websocket.accept()
    
    try:
        # TODO: Add admin authentication check
        admin_user_id = "admin"
        
        # Register admin connection
        # TODO: Integrate with WebSocket service from app state
        # connection_id = await websocket_service.connect(websocket, admin_user_id)
        
        # Send initial metrics
        metrics = chunked_upload_service.get_metrics()
        await websocket.send_json({
            "type": "initial_metrics",
            "data": metrics
        })
        
        logger.info("Admin upload monitoring WebSocket connected")
        
        # Keep connection alive and send periodic updates
        while True:
            try:
                # Wait for messages or timeout for periodic updates
                try:
                    message = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                    data = json.loads(message)
                    
                    if data.get("type") == "ping":
                        await websocket.send_json({"type": "pong"})
                    
                    elif data.get("type") == "get_metrics":
                        metrics = chunked_upload_service.get_metrics()
                        await websocket.send_json({
                            "type": "metrics_update",
                            "data": metrics
                        })
                    
                    elif data.get("type") == "get_active_sessions":
                        active_sessions = []
                        for session_id, session in chunked_upload_service.sessions.items():
                            if session.status.value in ["active", "assembling"]:
                                session_info = {
                                    "session_id": session_id,
                                    "user_id": session.user_id,
                                    "filename": session.original_filename,
                                    "status": session.status.value,
                                    "progress": round((len(session.uploaded_chunks) / session.total_chunks) * 100, 2),
                                    "created_at": session.created_at.isoformat(),
                                    "total_size": session.total_size
                                }
                                active_sessions.append(session_info)
                        
                        await websocket.send_json({
                            "type": "active_sessions",
                            "sessions": active_sessions
                        })
                    
                    elif data.get("type") == "cleanup_expired":
                        await chunked_upload_service.cleanup_expired_sessions()
                        await websocket.send_json({
                            "type": "cleanup_complete",
                            "message": "Expired sessions cleaned up"
                        })
                
                except asyncio.TimeoutError:
                    # Send periodic metrics update
                    metrics = chunked_upload_service.get_metrics()
                    await websocket.send_json({
                        "type": "periodic_metrics",
                        "data": metrics
                    })
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error in admin upload monitoring WebSocket: {e}")
                
    except WebSocketDisconnect:
        logger.info("Admin upload monitoring WebSocket disconnected")
    except Exception as e:
        logger.error(f"Admin upload monitoring WebSocket error: {e}")
    finally:
        try:
            # await websocket_service.disconnect(websocket)
            pass
        except:
            pass


class UploadWebSocketProgressNotifier:
    """Helper class to send progress notifications via WebSocket."""
    
    @staticmethod
    async def notify_chunk_uploaded(session_id: str, user_id: str, progress_data: Dict[str, Any]):
        """Notify via WebSocket that a chunk was uploaded."""
        try:
            message = {
                "type": "chunk_uploaded",
                "session_id": session_id,
                "data": progress_data
            }
            
            # Send to user-specific WebSocket connections
            # TODO: Integrate with WebSocket service from app state
            # await websocket_service.send_to_user(user_id, "upload_progress", message)
            
            # Also send to admin monitoring
            # await websocket_service.broadcast_to_group("admin", message)
            
        except Exception as e:
            logger.warning(f"Failed to send chunk upload notification: {e}")
    
    @staticmethod
    async def notify_upload_completed(session_id: str, user_id: str, job_id: str):
        """Notify via WebSocket that upload was completed."""
        try:
            message = {
                "type": "upload_completed",
                "session_id": session_id,
                "job_id": job_id,
                "message": "Upload completed successfully"
            }
            
            # TODO: Integrate with WebSocket service from app state
            # await websocket_service.send_to_user(user_id, "upload_progress", message)
            # await websocket_service.broadcast_to_group("admin", message)
            
        except Exception as e:
            logger.warning(f"Failed to send upload completion notification: {e}")
    
    @staticmethod
    async def notify_upload_failed(session_id: str, user_id: str, error: str):
        """Notify via WebSocket that upload failed."""
        try:
            message = {
                "type": "upload_failed",
                "session_id": session_id,
                "error": error,
                "message": "Upload failed"
            }
            
            # TODO: Integrate with WebSocket service from app state
            # await websocket_service.send_to_user(user_id, "upload_progress", message)
            # await websocket_service.broadcast_to_group("admin", message)
            
        except Exception as e:
            logger.warning(f"Failed to send upload failure notification: {e}")
    
    @staticmethod
    async def notify_assembly_started(session_id: str, user_id: str):
        """Notify via WebSocket that file assembly started."""
        try:
            message = {
                "type": "assembly_started",
                "session_id": session_id,
                "message": "Assembling uploaded chunks into final file"
            }
            
            # TODO: Integrate with WebSocket service from app state
            # await websocket_service.send_to_user(user_id, "upload_progress", message)
            
        except Exception as e:
            logger.warning(f"Failed to send assembly start notification: {e}")


# Global notifier instance
upload_websocket_notifier = UploadWebSocketProgressNotifier()
