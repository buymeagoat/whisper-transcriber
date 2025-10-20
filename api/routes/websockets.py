"""
Enhanced WebSocket Routes for T025 Phase 4: WebSocket Scaling
Provides scalable WebSocket endpoints with authentication, connection management, and real-time updates.
"""

import asyncio
from typing import Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from api.orm_bootstrap import get_db
from api.services.enhanced_websocket_service import get_websocket_service, EnhancedWebSocketService
from api.services.websocket_auth import get_current_user_websocket, AuthenticationError
from api.models import User, Job, JobStatusEnum
from api.utils.logger import get_system_logger

logger = get_system_logger("websocket_routes")

router = APIRouter(
    prefix="/ws",
    tags=["websockets", "real-time"]
)

async def authenticate_websocket(websocket: WebSocket, token: Optional[str] = None) -> Optional[User]:
    """Authenticate a WebSocket connection."""
    try:
        if not token:
            # Try to get token from query parameters
            token = websocket.query_params.get("token")
        
        if not token:
            # Try to get token from headers
            authorization = websocket.headers.get("Authorization", "")
            if authorization.startswith("Bearer "):
                token = authorization[7:]
        
        if not token:
            await websocket.close(code=1008, reason="Authentication required")
            return None
        
        # Validate token (this would typically use your JWT validation logic)
        user = await get_current_user_websocket(token)
        return user
        
    except AuthenticationError as e:
        await websocket.close(code=1008, reason=f"Authentication failed: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"WebSocket authentication error: {e}")
        await websocket.close(code=1011, reason="Authentication error")
        return None

@router.websocket("/jobs/{job_id}")
async def websocket_job_progress(
    websocket: WebSocket, 
    job_id: str,
    token: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """WebSocket endpoint for real-time job progress updates."""
    websocket_service = await get_websocket_service()
    connection_id = None
    
    try:
        # Authenticate the connection
        user = await authenticate_websocket(websocket, token)
        if not user:
            return
        
        # Verify user has access to this job
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            await websocket.close(code=1008, reason="Job not found")
            return
        
        if job.user_id != user.id and user.role != "admin":
            await websocket.close(code=1008, reason="Access denied")
            return
        
        # Connect to WebSocket service
        connection_id = await websocket_service.connect_websocket(
            websocket, 
            user_id=user.id, 
            job_id=job_id
        )
        
        # Send initial job status
        await websocket_service.connection_pool.send_to_connection(connection_id, {
            "type": "job_status",
            "job_id": job_id,
            "status": job.status.value,
            "progress": job.progress or 0,
            "message": f"Connected to job {job_id}",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Receive messages (for potential client-to-server communication)
                message = await websocket.receive_text()
                
                # Update connection activity
                conn_info = websocket_service.connection_pool.get_connection_info(connection_id)
                if conn_info:
                    conn_info.update_activity()
                
                # Handle client messages if needed
                await _handle_client_message(connection_id, message, websocket_service, db)
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error in WebSocket job progress loop: {e}")
                break
                
    except Exception as e:
        logger.error(f"WebSocket job progress error: {e}")
        
    finally:
        if connection_id:
            await websocket_service.disconnect_websocket(connection_id)

@router.websocket("/user/notifications")
async def websocket_user_notifications(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """WebSocket endpoint for user-specific notifications."""
    websocket_service = await get_websocket_service()
    connection_id = None
    
    try:
        # Authenticate the connection
        user = await authenticate_websocket(websocket, token)
        if not user:
            return
        
        # Connect to WebSocket service
        connection_id = await websocket_service.connect_websocket(
            websocket, 
            user_id=user.id
        )
        
        # Send welcome message
        await websocket_service.connection_pool.send_to_connection(connection_id, {
            "type": "welcome",
            "message": f"Connected to notifications for user {user.username}",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Keep connection alive
        while True:
            try:
                message = await websocket.receive_text()
                
                # Update connection activity
                conn_info = websocket_service.connection_pool.get_connection_info(connection_id)
                if conn_info:
                    conn_info.update_activity()
                
                # Handle client messages
                await _handle_client_message(connection_id, message, websocket_service, db)
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error in WebSocket user notifications loop: {e}")
                break
                
    except Exception as e:
        logger.error(f"WebSocket user notifications error: {e}")
        
    finally:
        if connection_id:
            await websocket_service.disconnect_websocket(connection_id)

@router.websocket("/admin/monitoring")
async def websocket_admin_monitoring(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """WebSocket endpoint for admin system monitoring."""
    websocket_service = await get_websocket_service()
    connection_id = None
    
    try:
        # Authenticate the connection
        user = await authenticate_websocket(websocket, token)
        if not user or user.role != "admin":
            await websocket.close(code=1008, reason="Admin access required")
            return
        
        # Connect to WebSocket service
        connection_id = await websocket_service.connect_websocket(
            websocket, 
            user_id=user.id
        )
        
        # Send initial system status
        metrics = websocket_service.get_metrics()
        await websocket_service.connection_pool.send_to_connection(connection_id, {
            "type": "system_status",
            "metrics": metrics,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Start periodic status updates
        status_task = asyncio.create_task(
            _send_periodic_status(connection_id, websocket_service)
        )
        
        # Keep connection alive
        try:
            while True:
                message = await websocket.receive_text()
                
                # Update connection activity
                conn_info = websocket_service.connection_pool.get_connection_info(connection_id)
                if conn_info:
                    conn_info.update_activity()
                
                # Handle admin commands
                await _handle_admin_message(connection_id, message, websocket_service, db)
                
        except WebSocketDisconnect:
            pass
        finally:
            status_task.cancel()
            
    except Exception as e:
        logger.error(f"WebSocket admin monitoring error: {e}")
        
    finally:
        if connection_id:
            await websocket_service.disconnect_websocket(connection_id)

@router.websocket("/system/broadcasts")
async def websocket_system_broadcasts(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """WebSocket endpoint for system-wide broadcasts."""
    websocket_service = await get_websocket_service()
    connection_id = None
    
    try:
        # Authenticate the connection (optional for system broadcasts)
        user = await authenticate_websocket(websocket, token)
        user_id = user.id if user else None
        
        # Connect to WebSocket service
        connection_id = await websocket_service.connect_websocket(
            websocket, 
            user_id=user_id
        )
        
        # Send welcome message
        await websocket_service.connection_pool.send_to_connection(connection_id, {
            "type": "broadcast_connected",
            "message": "Connected to system broadcasts",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Keep connection alive
        while True:
            try:
                message = await websocket.receive_text()
                
                # Update connection activity
                conn_info = websocket_service.connection_pool.get_connection_info(connection_id)
                if conn_info:
                    conn_info.update_activity()
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error in WebSocket system broadcasts loop: {e}")
                break
                
    except Exception as e:
        logger.error(f"WebSocket system broadcasts error: {e}")
        
    finally:
        if connection_id:
            await websocket_service.disconnect_websocket(connection_id)

# Helper functions

async def _handle_client_message(connection_id: str, message: str, 
                                websocket_service: EnhancedWebSocketService, db: Session):
    """Handle messages received from WebSocket clients."""
    try:
        import json
        data = json.loads(message)
        message_type = data.get("type")
        
        if message_type == "ping":
            # Respond to ping with pong
            await websocket_service.connection_pool.send_to_connection(connection_id, {
                "type": "pong",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        elif message_type == "subscribe":
            # Handle subscription requests
            topic = data.get("topic")
            if topic:
                conn_info = websocket_service.connection_pool.get_connection_info(connection_id)
                if conn_info:
                    conn_info.add_subscription(topic)
                    await websocket_service.connection_pool.send_to_connection(connection_id, {
                        "type": "subscribed",
                        "topic": topic,
                        "timestamp": datetime.utcnow().isoformat()
                    })
        
        elif message_type == "unsubscribe":
            # Handle unsubscription requests
            topic = data.get("topic")
            if topic:
                conn_info = websocket_service.connection_pool.get_connection_info(connection_id)
                if conn_info:
                    conn_info.remove_subscription(topic)
                    await websocket_service.connection_pool.send_to_connection(connection_id, {
                        "type": "unsubscribed",
                        "topic": topic,
                        "timestamp": datetime.utcnow().isoformat()
                    })
        
        # Log received message for debugging
        logger.debug(f"Received client message: {message_type} from connection {connection_id}")
        
    except json.JSONDecodeError:
        logger.warning(f"Invalid JSON message from connection {connection_id}: {message}")
    except Exception as e:
        logger.error(f"Error handling client message from {connection_id}: {e}")

async def _handle_admin_message(connection_id: str, message: str, 
                               websocket_service: EnhancedWebSocketService, db: Session):
    """Handle admin-specific messages."""
    try:
        import json
        data = json.loads(message)
        command = data.get("command")
        
        if command == "get_metrics":
            metrics = websocket_service.get_metrics()
            await websocket_service.connection_pool.send_to_connection(connection_id, {
                "type": "metrics_response",
                "metrics": metrics,
                "timestamp": datetime.utcnow().isoformat()
            })
        
        elif command == "get_connections":
            connection_status = websocket_service.get_connection_status()
            await websocket_service.connection_pool.send_to_connection(connection_id, {
                "type": "connections_response",
                "status": connection_status,
                "timestamp": datetime.utcnow().isoformat()
            })
        
        elif command == "broadcast":
            # Admin broadcast message
            broadcast_message = data.get("message", "")
            broadcast_type = data.get("broadcast_type", "info")
            
            await websocket_service.broadcast_system_message(
                broadcast_message, 
                broadcast_type
            )
            
            await websocket_service.connection_pool.send_to_connection(connection_id, {
                "type": "broadcast_sent",
                "message": "Broadcast sent successfully",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        logger.debug(f"Handled admin command: {command} from connection {connection_id}")
        
    except json.JSONDecodeError:
        logger.warning(f"Invalid JSON admin message from connection {connection_id}: {message}")
    except Exception as e:
        logger.error(f"Error handling admin message from {connection_id}: {e}")

async def _send_periodic_status(connection_id: str, websocket_service: EnhancedWebSocketService):
    """Send periodic status updates to admin connections."""
    while True:
        try:
            await asyncio.sleep(30)  # Send updates every 30 seconds
            
            metrics = websocket_service.get_metrics()
            connection_status = websocket_service.get_connection_status()
            
            await websocket_service.connection_pool.send_to_connection(connection_id, {
                "type": "periodic_status",
                "metrics": metrics,
                "connection_status": connection_status,
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error sending periodic status to {connection_id}: {e}")
            break
