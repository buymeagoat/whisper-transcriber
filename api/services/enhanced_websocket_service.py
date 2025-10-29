"""
Enhanced WebSocket Service for T025 Phase 4: WebSocket Scaling
Provides scalable WebSocket connection management with Redis pub/sub, connection pooling, and performance monitoring.
"""

import asyncio
import json
import os
import time
from typing import Dict, List, Set, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from contextlib import asynccontextmanager
import uuid

from fastapi import WebSocket, WebSocketDisconnect, HTTPException
import redis.asyncio as redis
from sqlalchemy.orm import Session

from api.utils.logger import get_system_logger
from api.services.redis_cache import get_cache_service
from api.models import Job, JobStatusEnum, User

logger = get_system_logger("websocket_service")

@dataclass
class WebSocketMetrics:
    """WebSocket performance metrics."""
    total_connections: int = 0
    active_connections: int = 0
    messages_sent: int = 0
    messages_received: int = 0
    connection_errors: int = 0
    average_message_time_ms: float = 0.0
    peak_connections: int = 0
    connections_per_minute: int = 0
    last_reset: datetime = field(default_factory=datetime.utcnow)
    
    # Connection lifecycle tracking
    total_connects: int = 0
    total_disconnects: int = 0
    forced_disconnects: int = 0
    
    # Message type statistics
    message_types: Dict[str, int] = field(default_factory=dict)
    
    def reset_periodic_metrics(self):
        """Reset metrics that should be calculated periodically."""
        self.connections_per_minute = 0
        self.last_reset = datetime.utcnow()

@dataclass
class ConnectionInfo:
    """Information about a WebSocket connection."""
    websocket: WebSocket
    user_id: Optional[int]
    job_id: Optional[str]
    connected_at: datetime
    last_activity: datetime
    connection_id: str
    subscriptions: Set[str] = field(default_factory=set)
    
    def update_activity(self):
        """Update the last activity timestamp."""
        self.last_activity = datetime.utcnow()
    
    def add_subscription(self, topic: str):
        """Add a subscription topic."""
        self.subscriptions.add(topic)
    
    def remove_subscription(self, topic: str):
        """Remove a subscription topic."""
        self.subscriptions.discard(topic)

class WebSocketConnectionPool:
    """Advanced WebSocket connection pool with monitoring and management."""
    
    def __init__(self, max_connections: int = 1000):
        self.max_connections = max_connections
        self.connections: Dict[str, ConnectionInfo] = {}
        self.job_connections: Dict[str, Set[str]] = {}  # job_id -> connection_ids
        self.user_connections: Dict[int, Set[str]] = {}  # user_id -> connection_ids
        self.metrics = WebSocketMetrics()
        self.cleanup_task: Optional[asyncio.Task] = None
        
    async def add_connection(self, websocket: WebSocket, connection_id: str, 
                           user_id: Optional[int] = None, job_id: Optional[str] = None) -> bool:
        """Add a new WebSocket connection to the pool."""
        try:
            # Check connection limits
            if len(self.connections) >= self.max_connections:
                logger.warning(f"Connection pool full ({self.max_connections}), rejecting connection")
                return False
            
            # Create connection info
            conn_info = ConnectionInfo(
                websocket=websocket,
                user_id=user_id,
                job_id=job_id,
                connected_at=datetime.utcnow(),
                last_activity=datetime.utcnow(),
                connection_id=connection_id
            )
            
            # Add to connection mappings
            self.connections[connection_id] = conn_info
            
            if job_id:
                if job_id not in self.job_connections:
                    self.job_connections[job_id] = set()
                self.job_connections[job_id].add(connection_id)
            
            if user_id:
                if user_id not in self.user_connections:
                    self.user_connections[user_id] = set()
                self.user_connections[user_id].add(connection_id)
            
            # Update metrics
            self.metrics.active_connections = len(self.connections)
            self.metrics.total_connects += 1
            self.metrics.peak_connections = max(self.metrics.peak_connections, self.metrics.active_connections)
            
            logger.info(f"WebSocket connection added: {connection_id} (user: {user_id}, job: {job_id})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add WebSocket connection {connection_id}: {e}")
            return False
    
    async def remove_connection(self, connection_id: str, reason: str = "disconnect"):
        """Remove a WebSocket connection from the pool."""
        try:
            if connection_id not in self.connections:
                return
            
            conn_info = self.connections[connection_id]
            
            # Remove from job connections
            if conn_info.job_id and conn_info.job_id in self.job_connections:
                self.job_connections[conn_info.job_id].discard(connection_id)
                if not self.job_connections[conn_info.job_id]:
                    del self.job_connections[conn_info.job_id]
            
            # Remove from user connections
            if conn_info.user_id and conn_info.user_id in self.user_connections:
                self.user_connections[conn_info.user_id].discard(connection_id)
                if not self.user_connections[conn_info.user_id]:
                    del self.user_connections[conn_info.user_id]
            
            # Remove from main connections
            del self.connections[connection_id]
            
            # Update metrics
            self.metrics.active_connections = len(self.connections)
            self.metrics.total_disconnects += 1
            if reason == "forced":
                self.metrics.forced_disconnects += 1
            
            logger.info(f"WebSocket connection removed: {connection_id} (reason: {reason})")
            
        except Exception as e:
            logger.error(f"Failed to remove WebSocket connection {connection_id}: {e}")
    
    async def send_to_connection(self, connection_id: str, message: Dict[str, Any]) -> bool:
        """Send a message to a specific connection."""
        try:
            if connection_id not in self.connections:
                return False
            
            conn_info = self.connections[connection_id]
            start_time = time.time()
            
            await conn_info.websocket.send_json(message)
            
            # Update metrics
            send_time_ms = (time.time() - start_time) * 1000
            self.metrics.messages_sent += 1
            self._update_average_message_time(send_time_ms)
            self._track_message_type(message.get("type", "unknown"))
            
            conn_info.update_activity()
            return True
            
        except Exception as e:
            logger.warning(f"Failed to send message to connection {connection_id}: {e}")
            # Mark connection for removal
            await self.remove_connection(connection_id, "send_error")
            self.metrics.connection_errors += 1
            return False
    
    async def broadcast_to_job(self, job_id: str, message: Dict[str, Any]) -> int:
        """Broadcast a message to all connections for a specific job."""
        if job_id not in self.job_connections:
            return 0
        
        sent_count = 0
        connection_ids = list(self.job_connections[job_id])  # Copy to avoid modification during iteration
        
        for connection_id in connection_ids:
            if await self.send_to_connection(connection_id, message):
                sent_count += 1
        
        return sent_count
    
    async def broadcast_to_user(self, user_id: int, message: Dict[str, Any]) -> int:
        """Broadcast a message to all connections for a specific user."""
        if user_id not in self.user_connections:
            return 0
        
        sent_count = 0
        connection_ids = list(self.user_connections[user_id])  # Copy to avoid modification during iteration
        
        for connection_id in connection_ids:
            if await self.send_to_connection(connection_id, message):
                sent_count += 1
        
        return sent_count
    
    async def broadcast_to_all(self, message: Dict[str, Any]) -> int:
        """Broadcast a message to all active connections."""
        sent_count = 0
        connection_ids = list(self.connections.keys())  # Copy to avoid modification during iteration
        
        for connection_id in connection_ids:
            if await self.send_to_connection(connection_id, message):
                sent_count += 1
        
        return sent_count
    
    def get_connection_info(self, connection_id: str) -> Optional[ConnectionInfo]:
        """Get information about a specific connection."""
        return self.connections.get(connection_id)
    
    def get_connections_for_job(self, job_id: str) -> List[ConnectionInfo]:
        """Get all connections for a specific job."""
        if job_id not in self.job_connections:
            return []
        
        return [self.connections[conn_id] for conn_id in self.job_connections[job_id] 
                if conn_id in self.connections]
    
    def get_connections_for_user(self, user_id: int) -> List[ConnectionInfo]:
        """Get all connections for a specific user."""
        if user_id not in self.user_connections:
            return []
        
        return [self.connections[conn_id] for conn_id in self.user_connections[user_id] 
                if conn_id in self.connections]
    
    def _update_average_message_time(self, new_time_ms: float):
        """Update the rolling average message time."""
        if self.metrics.messages_sent == 1:
            self.metrics.average_message_time_ms = new_time_ms
        else:
            # Rolling average
            self.metrics.average_message_time_ms = (
                (self.metrics.average_message_time_ms * (self.metrics.messages_sent - 1) + new_time_ms) / 
                self.metrics.messages_sent
            )
    
    def _track_message_type(self, message_type: str):
        """Track message type statistics."""
        self.metrics.message_types[message_type] = self.metrics.message_types.get(message_type, 0) + 1
    
    async def cleanup_stale_connections(self, max_idle_minutes: int = 30):
        """Clean up stale connections that haven't been active."""
        cutoff_time = datetime.utcnow() - timedelta(minutes=max_idle_minutes)
        stale_connections = []
        
        for connection_id, conn_info in self.connections.items():
            if conn_info.last_activity < cutoff_time:
                stale_connections.append(connection_id)
        
        for connection_id in stale_connections:
            try:
                conn_info = self.connections[connection_id]
                await conn_info.websocket.close(code=1000, reason="Idle timeout")
                await self.remove_connection(connection_id, "timeout")
                logger.info(f"Cleaned up stale connection: {connection_id}")
            except Exception as e:
                logger.warning(f"Error cleaning up stale connection {connection_id}: {e}")
    
    async def start_cleanup_task(self):
        """Start the background cleanup task."""
        if self.cleanup_task and not self.cleanup_task.done():
            return
        
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def stop_cleanup_task(self):
        """Stop the background cleanup task."""
        if self.cleanup_task and not self.cleanup_task.done():
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
    
    async def _cleanup_loop(self):
        """Background loop for cleaning up stale connections."""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                await self.cleanup_stale_connections()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in WebSocket cleanup loop: {e}")

class WebSocketMessageQueue:
    """Redis-backed message queue for scalable WebSocket message delivery."""
    
    def __init__(self, redis_url: str = None):
        redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0").replace("/0", "/1")
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
        self.pubsub: Optional[redis.client.PubSub] = None
        self.message_handlers: Dict[str, Callable] = {}
        self.running = False
        self.subscriber_task: Optional[asyncio.Task] = None
        
    async def initialize(self):
        """Initialize the Redis connection and pub/sub."""
        try:
            self.redis_client = redis.from_url(self.redis_url)
            await self.redis_client.ping()
            
            self.pubsub = self.redis_client.pubsub()
            
            # Subscribe to WebSocket message channels
            await self.pubsub.subscribe(
                "websocket:job_updates",
                "websocket:user_notifications", 
                "websocket:system_broadcasts",
                "websocket:admin_alerts"
            )
            
            logger.info("WebSocket message queue initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize WebSocket message queue: {e}")
            raise
    
    async def start_subscriber(self):
        """Start the message subscriber task."""
        if self.running:
            return
        
        self.running = True
        self.subscriber_task = asyncio.create_task(self._message_subscriber_loop())
        logger.info("WebSocket message subscriber started")
    
    async def stop_subscriber(self):
        """Stop the message subscriber task."""
        self.running = False
        
        if self.subscriber_task and not self.subscriber_task.done():
            self.subscriber_task.cancel()
            try:
                await self.subscriber_task
            except asyncio.CancelledError:
                pass
        
        if self.pubsub:
            await self.pubsub.close()
        
        if self.redis_client:
            await self.redis_client.close()
        
        logger.info("WebSocket message subscriber stopped")
    
    async def publish_job_update(self, job_id: str, status: str, progress: int = 0, 
                                message: str = "", extra_data: Dict[str, Any] = None):
        """Publish a job status update."""
        if not self.redis_client:
            return
        
        data = {
            "type": "job_update",
            "job_id": job_id,
            "status": status,
            "progress": progress,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            **(extra_data or {})
        }
        
        await self.redis_client.publish("websocket:job_updates", json.dumps(data))
    
    async def publish_user_notification(self, user_id: int, notification_type: str, 
                                      message: str, data: Dict[str, Any] = None):
        """Publish a user notification."""
        if not self.redis_client:
            return
        
        notification_data = {
            "type": "user_notification",
            "user_id": user_id,
            "notification_type": notification_type,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data or {}
        }
        
        await self.redis_client.publish("websocket:user_notifications", json.dumps(notification_data))
    
    async def publish_system_broadcast(self, message: str, broadcast_type: str = "info", 
                                     data: Dict[str, Any] = None):
        """Publish a system-wide broadcast."""
        if not self.redis_client:
            return
        
        broadcast_data = {
            "type": "system_broadcast",
            "broadcast_type": broadcast_type,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data or {}
        }
        
        await self.redis_client.publish("websocket:system_broadcasts", json.dumps(broadcast_data))
    
    async def publish_admin_alert(self, alert_type: str, message: str, severity: str = "info",
                                data: Dict[str, Any] = None):
        """Publish an admin alert."""
        if not self.redis_client:
            return
        
        alert_data = {
            "type": "admin_alert",
            "alert_type": alert_type,
            "message": message,
            "severity": severity,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data or {}
        }
        
        await self.redis_client.publish("websocket:admin_alerts", json.dumps(alert_data))
    
    def register_handler(self, message_type: str, handler: Callable):
        """Register a message handler for a specific message type."""
        self.message_handlers[message_type] = handler
    
    async def _message_subscriber_loop(self):
        """Main loop for processing Redis pub/sub messages."""
        while self.running:
            try:
                if not self.pubsub:
                    break
                
                message = await self.pubsub.get_message(timeout=1.0)
                if message is None:
                    continue
                
                if message["type"] == "message":
                    await self._handle_redis_message(message)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in WebSocket message subscriber loop: {e}")
                await asyncio.sleep(1)  # Brief pause before retrying
    
    async def _handle_redis_message(self, message):
        """Handle a Redis pub/sub message."""
        try:
            channel = message["channel"].decode()
            data = json.loads(message["data"].decode())
            message_type = data.get("type")
            
            if message_type in self.message_handlers:
                await self.message_handlers[message_type](data)
            else:
                logger.warning(f"No handler registered for message type: {message_type}")
                
        except Exception as e:
            logger.error(f"Error handling Redis message: {e}")

class EnhancedWebSocketService:
    """Enhanced WebSocket service with connection pooling, message queuing, and monitoring."""
    
    def __init__(self, max_connections: int = 1000, redis_url: str = None):
        self.connection_pool = WebSocketConnectionPool(max_connections)
        redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/1")
        self.message_queue = WebSocketMessageQueue(redis_url)
        self.is_running = False
        
        # Register message handlers
        self.message_queue.register_handler("job_update", self._handle_job_update)
        self.message_queue.register_handler("user_notification", self._handle_user_notification)
        self.message_queue.register_handler("system_broadcast", self._handle_system_broadcast)
        self.message_queue.register_handler("admin_alert", self._handle_admin_alert)
    
    async def initialize(self):
        """Initialize the WebSocket service."""
        try:
            await self.message_queue.initialize()
            await self.connection_pool.start_cleanup_task()
            await self.message_queue.start_subscriber()
            self.is_running = True
            
            logger.info("Enhanced WebSocket service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Enhanced WebSocket service: {e}")
            raise
    
    async def shutdown(self):
        """Shutdown the WebSocket service."""
        self.is_running = False
        
        await self.message_queue.stop_subscriber()
        await self.connection_pool.stop_cleanup_task()
        
        # Close all active connections
        for connection_id in list(self.connection_pool.connections.keys()):
            try:
                conn_info = self.connection_pool.connections[connection_id]
                await conn_info.websocket.close(code=1001, reason="Server shutdown")
                await self.connection_pool.remove_connection(connection_id, "shutdown")
            except Exception as e:
                logger.warning(f"Error closing connection {connection_id}: {e}")
        
        logger.info("Enhanced WebSocket service shutdown completed")
    
    async def connect_websocket(self, websocket: WebSocket, user_id: Optional[int] = None, 
                              job_id: Optional[str] = None) -> str:
        """Connect a new WebSocket with authentication and setup."""
        connection_id = str(uuid.uuid4())
        
        try:
            await websocket.accept()
            
            if not await self.connection_pool.add_connection(websocket, connection_id, user_id, job_id):
                await websocket.close(code=1013, reason="Service unavailable")
                raise HTTPException(status_code=503, detail="WebSocket service at capacity")
            
            # Send initial connection confirmation
            await self.connection_pool.send_to_connection(connection_id, {
                "type": "connection_established",
                "connection_id": connection_id,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return connection_id
            
        except Exception as e:
            logger.error(f"Failed to connect WebSocket: {e}")
            await self.connection_pool.remove_connection(connection_id, "connect_error")
            raise
    
    async def disconnect_websocket(self, connection_id: str):
        """Disconnect a WebSocket connection."""
        await self.connection_pool.remove_connection(connection_id, "disconnect")
    
    async def send_job_update(self, job_id: str, status: str, progress: int = 0, 
                            message: str = "", extra_data: Dict[str, Any] = None):
        """Send a job update to all relevant connections."""
        await self.message_queue.publish_job_update(job_id, status, progress, message, extra_data)
    
    async def send_user_notification(self, user_id: int, notification_type: str, 
                                   message: str, data: Dict[str, Any] = None):
        """Send a notification to a specific user."""
        await self.message_queue.publish_user_notification(user_id, notification_type, message, data)
    
    async def broadcast_system_message(self, message: str, broadcast_type: str = "info",
                                     data: Dict[str, Any] = None):
        """Broadcast a system message to all connections."""
        await self.message_queue.publish_system_broadcast(message, broadcast_type, data)
    
    async def send_admin_alert(self, alert_type: str, message: str, severity: str = "info",
                             data: Dict[str, Any] = None):
        """Send an alert to admin connections."""
        await self.message_queue.publish_admin_alert(alert_type, message, severity, data)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current WebSocket service metrics."""
        return {
            "connection_pool": {
                "active_connections": self.connection_pool.metrics.active_connections,
                "peak_connections": self.connection_pool.metrics.peak_connections,
                "total_connects": self.connection_pool.metrics.total_connects,
                "total_disconnects": self.connection_pool.metrics.total_disconnects,
                "forced_disconnects": self.connection_pool.metrics.forced_disconnects,
                "connection_errors": self.connection_pool.metrics.connection_errors
            },
            "messaging": {
                "messages_sent": self.connection_pool.metrics.messages_sent,
                "average_message_time_ms": self.connection_pool.metrics.average_message_time_ms,
                "message_types": self.connection_pool.metrics.message_types
            },
            "service_status": {
                "is_running": self.is_running,
                "redis_connected": self.message_queue.redis_client is not None,
                "subscriber_running": self.message_queue.running
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Get detailed connection status information."""
        job_stats = {}
        user_stats = {}
        
        for job_id, connection_ids in self.connection_pool.job_connections.items():
            job_stats[job_id] = len(connection_ids)
        
        for user_id, connection_ids in self.connection_pool.user_connections.items():
            user_stats[str(user_id)] = len(connection_ids)
        
        return {
            "total_connections": len(self.connection_pool.connections),
            "job_connections": job_stats,
            "user_connections": user_stats,
            "max_connections": self.connection_pool.max_connections,
            "utilization_percent": (len(self.connection_pool.connections) / self.connection_pool.max_connections) * 100
        }
    
    # Message handlers
    async def _handle_job_update(self, data: Dict[str, Any]):
        """Handle job update messages from Redis."""
        job_id = data.get("job_id")
        if job_id:
            await self.connection_pool.broadcast_to_job(job_id, data)
    
    async def _handle_user_notification(self, data: Dict[str, Any]):
        """Handle user notification messages from Redis."""
        user_id = data.get("user_id")
        if user_id:
            await self.connection_pool.broadcast_to_user(user_id, data)
    
    async def _handle_system_broadcast(self, data: Dict[str, Any]):
        """Handle system broadcast messages from Redis."""
        await self.connection_pool.broadcast_to_all(data)
    
    async def _handle_admin_alert(self, data: Dict[str, Any]):
        """Handle admin alert messages from Redis."""
        # Broadcast to admin users only (implement role-based filtering as needed)
        await self.connection_pool.broadcast_to_all(data)

# Global WebSocket service instance
_websocket_service: Optional[EnhancedWebSocketService] = None

async def get_websocket_service() -> EnhancedWebSocketService:
    """Get the global WebSocket service instance."""
    global _websocket_service
    
    if _websocket_service is None:
        # Use the main Redis URL but switch to database 1 for WebSocket
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        # Change database from 0 to 1 for WebSocket service
        redis_url = redis_url.replace("/0", "/1")
        _websocket_service = EnhancedWebSocketService(redis_url=redis_url)
        await _websocket_service.initialize()
    
    return _websocket_service

async def cleanup_websocket_service():
    """Cleanup the WebSocket service."""
    global _websocket_service
    
    if _websocket_service:
        await _websocket_service.shutdown()
        _websocket_service = None

@asynccontextmanager
async def websocket_service_lifespan():
    """Context manager for WebSocket service lifecycle."""
    try:
        service = await get_websocket_service()
        yield service
    finally:
        await cleanup_websocket_service()
