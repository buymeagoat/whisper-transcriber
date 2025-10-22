"""
T036: Real-time Collaboration Features - WebSocket Server
WebSocket infrastructure for real-time collaborative editing and communication.
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Set
from enum import Enum
import weakref

from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..orm_bootstrap import get_db
from ..models import User, Job
from ..utils.logger import get_logger

logger = get_logger("collaboration_websocket")


class MessageType(Enum):
    """Types of WebSocket messages for collaboration."""
    
    # Connection management
    USER_JOINED = "user_joined"
    USER_LEFT = "user_left"
    USER_PRESENCE = "user_presence"
    
    # Document collaboration
    DOCUMENT_OPEN = "document_open"
    DOCUMENT_CLOSE = "document_close"
    DOCUMENT_EDIT = "document_edit"
    DOCUMENT_CURSOR = "document_cursor"
    DOCUMENT_SELECTION = "document_selection"
    
    # Comments and annotations
    COMMENT_ADD = "comment_add"
    COMMENT_UPDATE = "comment_update"
    COMMENT_DELETE = "comment_delete"
    ANNOTATION_ADD = "annotation_add"
    ANNOTATION_UPDATE = "annotation_update"
    ANNOTATION_DELETE = "annotation_delete"
    
    # System messages
    ERROR = "error"
    HEARTBEAT = "heartbeat"
    SYNC_REQUEST = "sync_request"
    SYNC_RESPONSE = "sync_response"


class UserPresence:
    """Represents a user's presence in a collaborative session."""
    
    def __init__(self, user_id: int, username: str, websocket: WebSocket):
        self.user_id = user_id
        self.username = username
        self.websocket = websocket
        self.session_id = str(uuid.uuid4())
        self.connected_at = datetime.utcnow()
        self.last_seen = datetime.utcnow()
        self.current_document = None
        self.cursor_position = None
        self.selection_range = None
        self.is_typing = False
    
    def update_activity(self):
        """Update last seen timestamp."""
        self.last_seen = datetime.utcnow()
    
    def to_dict(self) -> dict:
        """Convert presence to dictionary for serialization."""
        return {
            "user_id": self.user_id,
            "username": self.username,
            "session_id": self.session_id,
            "connected_at": self.connected_at.isoformat(),
            "last_seen": self.last_seen.isoformat(),
            "current_document": self.current_document,
            "cursor_position": self.cursor_position,
            "selection_range": self.selection_range,
            "is_typing": self.is_typing
        }


class DocumentSession:
    """Manages a collaborative editing session for a document."""
    
    def __init__(self, document_id: str):
        self.document_id = document_id
        self.created_at = datetime.utcnow()
        self.participants: Dict[int, UserPresence] = {}
        self.edit_history: List[dict] = []
        self.version = 0
        self.lock = asyncio.Lock()
    
    async def add_participant(self, user_presence: UserPresence):
        """Add a user to the document session."""
        async with self.lock:
            self.participants[user_presence.user_id] = user_presence
            user_presence.current_document = self.document_id
            
            # Notify other participants
            await self._broadcast_to_others(
                user_presence.user_id,
                {
                    "type": MessageType.USER_JOINED.value,
                    "user": user_presence.to_dict(),
                    "document_id": self.document_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
    
    async def remove_participant(self, user_id: int):
        """Remove a user from the document session."""
        async with self.lock:
            if user_id in self.participants:
                user_presence = self.participants.pop(user_id)
                user_presence.current_document = None
                
                # Notify other participants
                await self._broadcast_to_others(
                    user_id,
                    {
                        "type": MessageType.USER_LEFT.value,
                        "user_id": user_id,
                        "document_id": self.document_id,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
    
    async def apply_edit(self, user_id: int, edit_data: dict):
        """Apply an edit operation to the document."""
        async with self.lock:
            # Create edit operation
            edit_operation = {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat(),
                "version": self.version,
                "operation": edit_data,
                "document_id": self.document_id
            }
            
            # Add to history
            self.edit_history.append(edit_operation)
            self.version += 1
            
            # Broadcast to other participants
            await self._broadcast_to_others(
                user_id,
                {
                    "type": MessageType.DOCUMENT_EDIT.value,
                    "edit": edit_operation
                }
            )
            
            return edit_operation
    
    async def update_cursor(self, user_id: int, cursor_data: dict):
        """Update user's cursor position."""
        if user_id in self.participants:
            user_presence = self.participants[user_id]
            user_presence.cursor_position = cursor_data.get("position")
            user_presence.selection_range = cursor_data.get("selection")
            user_presence.is_typing = cursor_data.get("is_typing", False)
            user_presence.update_activity()
            
            # Broadcast cursor update
            await self._broadcast_to_others(
                user_id,
                {
                    "type": MessageType.DOCUMENT_CURSOR.value,
                    "user_id": user_id,
                    "cursor_position": user_presence.cursor_position,
                    "selection_range": user_presence.selection_range,
                    "is_typing": user_presence.is_typing,
                    "document_id": self.document_id
                }
            )
    
    async def _broadcast_to_others(self, sender_id: int, message: dict):
        """Broadcast message to all participants except sender."""
        for user_id, presence in self.participants.items():
            if user_id != sender_id:
                try:
                    await presence.websocket.send_text(json.dumps(message))
                except Exception as e:
                    logger.error(f"Failed to send message to user {user_id}: {e}")
    
    async def broadcast_to_all(self, message: dict):
        """Broadcast message to all participants."""
        for presence in self.participants.values():
            try:
                await presence.websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to broadcast message to user {presence.user_id}: {e}")
    
    def get_participants_info(self) -> List[dict]:
        """Get information about all participants."""
        return [presence.to_dict() for presence in self.participants.values()]


class CollaborationManager:
    """Manages all collaborative sessions and WebSocket connections."""
    
    def __init__(self):
        self.active_connections: Dict[int, UserPresence] = {}
        self.document_sessions: Dict[str, DocumentSession] = {}
        self.user_to_documents: Dict[int, Set[str]] = {}
        self.cleanup_task = None
    
    async def connect_user(self, websocket: WebSocket, user_id: int, username: str) -> UserPresence:
        """Connect a user and create presence."""
        # Disconnect existing connection if any
        if user_id in self.active_connections:
            await self.disconnect_user(user_id)
        
        # Create new presence
        presence = UserPresence(user_id, username, websocket)
        self.active_connections[user_id] = presence
        self.user_to_documents[user_id] = set()
        
        logger.info(f"User {username} (ID: {user_id}) connected with session {presence.session_id}")
        
        # Start cleanup task if not running
        if self.cleanup_task is None or self.cleanup_task.done():
            self.cleanup_task = asyncio.create_task(self._periodic_cleanup())
        
        return presence
    
    async def disconnect_user(self, user_id: int):
        """Disconnect a user and clean up their sessions."""
        if user_id not in self.active_connections:
            return
        
        presence = self.active_connections.pop(user_id)
        
        # Remove from all document sessions
        if user_id in self.user_to_documents:
            for document_id in list(self.user_to_documents[user_id]):
                await self.leave_document(user_id, document_id)
            del self.user_to_documents[user_id]
        
        logger.info(f"User {presence.username} (ID: {user_id}) disconnected")
    
    async def join_document(self, user_id: int, document_id: str) -> Optional[DocumentSession]:
        """Add user to a document session."""
        if user_id not in self.active_connections:
            return None
        
        # Create document session if it doesn't exist
        if document_id not in self.document_sessions:
            self.document_sessions[document_id] = DocumentSession(document_id)
        
        session = self.document_sessions[document_id]
        presence = self.active_connections[user_id]
        
        await session.add_participant(presence)
        self.user_to_documents[user_id].add(document_id)
        
        logger.info(f"User {presence.username} joined document {document_id}")
        return session
    
    async def leave_document(self, user_id: int, document_id: str):
        """Remove user from a document session."""
        if document_id in self.document_sessions:
            session = self.document_sessions[document_id]
            await session.remove_participant(user_id)
            
            # Clean up empty sessions
            if not session.participants:
                del self.document_sessions[document_id]
                logger.info(f"Cleaned up empty document session {document_id}")
        
        if user_id in self.user_to_documents:
            self.user_to_documents[user_id].discard(document_id)
    
    async def handle_message(self, user_id: int, message: dict):
        """Handle incoming WebSocket message."""
        try:
            message_type = MessageType(message.get("type"))
            
            if message_type == MessageType.DOCUMENT_OPEN:
                document_id = message.get("document_id")
                if document_id:
                    session = await self.join_document(user_id, document_id)
                    if session:
                        # Send current participants and document state
                        presence = self.active_connections[user_id]
                        await presence.websocket.send_text(json.dumps({
                            "type": MessageType.SYNC_RESPONSE.value,
                            "document_id": document_id,
                            "participants": session.get_participants_info(),
                            "version": session.version,
                            "edit_history": session.edit_history[-50:]  # Last 50 edits
                        }))
            
            elif message_type == MessageType.DOCUMENT_CLOSE:
                document_id = message.get("document_id")
                if document_id:
                    await self.leave_document(user_id, document_id)
            
            elif message_type == MessageType.DOCUMENT_EDIT:
                document_id = message.get("document_id")
                edit_data = message.get("edit_data")
                if document_id and edit_data and document_id in self.document_sessions:
                    session = self.document_sessions[document_id]
                    await session.apply_edit(user_id, edit_data)
            
            elif message_type == MessageType.DOCUMENT_CURSOR:
                document_id = message.get("document_id")
                cursor_data = message.get("cursor_data")
                if document_id and cursor_data and document_id in self.document_sessions:
                    session = self.document_sessions[document_id]
                    await session.update_cursor(user_id, cursor_data)
            
            elif message_type == MessageType.HEARTBEAT:
                # Update user activity
                if user_id in self.active_connections:
                    self.active_connections[user_id].update_activity()
                    # Send heartbeat response
                    presence = self.active_connections[user_id]
                    await presence.websocket.send_text(json.dumps({
                        "type": MessageType.HEARTBEAT.value,
                        "timestamp": datetime.utcnow().isoformat()
                    }))
            
            else:
                logger.warning(f"Unhandled message type: {message_type}")
        
        except Exception as e:
            logger.error(f"Error handling message from user {user_id}: {e}")
            if user_id in self.active_connections:
                presence = self.active_connections[user_id]
                await presence.websocket.send_text(json.dumps({
                    "type": MessageType.ERROR.value,
                    "error": "Failed to process message",
                    "details": str(e)
                }))
    
    async def _periodic_cleanup(self):
        """Periodic cleanup of stale connections and sessions."""
        while True:
            try:
                await asyncio.sleep(30)  # Run every 30 seconds
                
                # Check for stale connections (no activity for 5 minutes)
                stale_users = []
                cutoff_time = datetime.utcnow().timestamp() - 300  # 5 minutes
                
                for user_id, presence in self.active_connections.items():
                    if presence.last_seen.timestamp() < cutoff_time:
                        stale_users.append(user_id)
                
                # Disconnect stale users
                for user_id in stale_users:
                    logger.info(f"Disconnecting stale user {user_id}")
                    await self.disconnect_user(user_id)
                
            except Exception as e:
                logger.error(f"Error in periodic cleanup: {e}")
    
    def get_system_stats(self) -> dict:
        """Get collaboration system statistics."""
        return {
            "active_connections": len(self.active_connections),
            "active_document_sessions": len(self.document_sessions),
            "total_participants": sum(len(session.participants) for session in self.document_sessions.values()),
            "document_stats": {
                doc_id: {
                    "participants": len(session.participants),
                    "version": session.version,
                    "edit_count": len(session.edit_history)
                }
                for doc_id, session in self.document_sessions.items()
            }
        }


# Global collaboration manager instance
collaboration_manager = CollaborationManager()


async def handle_websocket_connection(websocket: WebSocket, user_id: int, username: str):
    """Handle a WebSocket connection for collaboration."""
    try:
        await websocket.accept()
        presence = await collaboration_manager.connect_user(websocket, user_id, username)
        
        # Send connection confirmation
        await websocket.send_text(json.dumps({
            "type": MessageType.USER_JOINED.value,
            "session_id": presence.session_id,
            "user": presence.to_dict(),
            "timestamp": datetime.utcnow().isoformat()
        }))
        
        # Listen for messages
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                await collaboration_manager.handle_message(user_id, message)
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON from user {user_id}: {e}")
                await websocket.send_text(json.dumps({
                    "type": MessageType.ERROR.value,
                    "error": "Invalid JSON format"
                }))
    
    except Exception as e:
        logger.error(f"WebSocket connection error for user {user_id}: {e}")
    
    finally:
        await collaboration_manager.disconnect_user(user_id)


def get_collaboration_stats() -> dict:
    """Get current collaboration system statistics."""
    return collaboration_manager.get_system_stats()