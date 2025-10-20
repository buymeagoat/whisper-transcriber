"""
Tests for Enhanced WebSocket Service (T025 Phase 4)
Comprehensive test suite for WebSocket scaling functionality.
"""

import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

import redis.asyncio as redis
from fastapi import WebSocket
from fastapi.testclient import TestClient

from api.services.enhanced_websocket_service import (
    EnhancedWebSocketService,
    WebSocketConnectionPool,
    WebSocketMessageQueue,
    WebSocketMetrics,
    ConnectionInfo,
    get_websocket_service,
    cleanup_websocket_service
)
from api.services.websocket_job_integration import (
    WebSocketJobNotifier,
    get_job_notifier,
    setup_job_event_listeners,
    notify_job_started,
    notify_job_progress_update,
    notify_job_completed,
    notify_job_failed
)
from api.models import Job, JobStatusEnum, User

# Test configuration
TEST_REDIS_URL = "redis://localhost:6379/15"  # Use different DB for tests
TEST_MAX_CONNECTIONS = 100

@pytest.fixture
async def mock_redis():
    """Create a mock Redis client."""
    mock_client = AsyncMock()
    mock_client.ping.return_value = True
    mock_client.publish = AsyncMock()
    mock_client.close = AsyncMock()
    
    mock_pubsub = AsyncMock()
    mock_pubsub.subscribe = AsyncMock()
    mock_pubsub.get_message = AsyncMock(return_value=None)
    mock_pubsub.close = AsyncMock()
    mock_client.pubsub.return_value = mock_pubsub
    
    return mock_client

@pytest.fixture
async def mock_websocket():
    """Create a mock WebSocket connection."""
    ws = AsyncMock(spec=WebSocket)
    ws.accept = AsyncMock()
    ws.send_json = AsyncMock()
    ws.close = AsyncMock()
    ws.receive_text = AsyncMock()
    ws.query_params = {"token": "test_token"}
    ws.headers = {"Authorization": "Bearer test_token"}
    return ws

@pytest.fixture
async def connection_pool():
    """Create a test WebSocket connection pool."""
    pool = WebSocketConnectionPool(max_connections=TEST_MAX_CONNECTIONS)
    yield pool
    
    # Cleanup
    await pool.stop_cleanup_task()

@pytest.fixture
async def message_queue(mock_redis):
    """Create a test WebSocket message queue."""
    with patch('api.services.enhanced_websocket_service.redis.from_url', return_value=mock_redis):
        queue = WebSocketMessageQueue(TEST_REDIS_URL)
        await queue.initialize()
        yield queue
        await queue.stop_subscriber()

@pytest.fixture
async def websocket_service(connection_pool, message_queue):
    """Create a test WebSocket service."""
    service = EnhancedWebSocketService(max_connections=TEST_MAX_CONNECTIONS, redis_url=TEST_REDIS_URL)
    service.connection_pool = connection_pool
    service.message_queue = message_queue
    service.is_running = True
    
    yield service
    
    await service.shutdown()

class TestWebSocketMetrics:
    """Test cases for WebSocket metrics tracking."""
    
    def test_metrics_initialization(self):
        """Test WebSocket metrics initialization."""
        metrics = WebSocketMetrics()
        
        assert metrics.total_connections == 0
        assert metrics.active_connections == 0
        assert metrics.messages_sent == 0
        assert metrics.connection_errors == 0
        assert metrics.average_message_time_ms == 0.0
        assert isinstance(metrics.message_types, dict)
    
    def test_metrics_reset(self):
        """Test periodic metrics reset."""
        metrics = WebSocketMetrics()
        metrics.connections_per_minute = 50
        
        initial_time = metrics.last_reset
        metrics.reset_periodic_metrics()
        
        assert metrics.connections_per_minute == 0
        assert metrics.last_reset > initial_time

class TestConnectionInfo:
    """Test cases for connection information tracking."""
    
    async def test_connection_info_creation(self, mock_websocket):
        """Test connection info creation."""
        conn_info = ConnectionInfo(
            websocket=mock_websocket,
            user_id=1,
            job_id="test_job",
            connected_at=datetime.utcnow(),
            last_activity=datetime.utcnow(),
            connection_id="test_conn_id"
        )
        
        assert conn_info.websocket == mock_websocket
        assert conn_info.user_id == 1
        assert conn_info.job_id == "test_job"
        assert conn_info.connection_id == "test_conn_id"
        assert len(conn_info.subscriptions) == 0
    
    def test_subscription_management(self, mock_websocket):
        """Test subscription management."""
        conn_info = ConnectionInfo(
            websocket=mock_websocket,
            user_id=1,
            job_id=None,
            connected_at=datetime.utcnow(),
            last_activity=datetime.utcnow(),
            connection_id="test_conn_id"
        )
        
        # Add subscriptions
        conn_info.add_subscription("job_updates")
        conn_info.add_subscription("user_notifications")
        
        assert "job_updates" in conn_info.subscriptions
        assert "user_notifications" in conn_info.subscriptions
        assert len(conn_info.subscriptions) == 2
        
        # Remove subscription
        conn_info.remove_subscription("job_updates")
        assert "job_updates" not in conn_info.subscriptions
        assert len(conn_info.subscriptions) == 1
    
    def test_activity_update(self, mock_websocket):
        """Test activity timestamp update."""
        conn_info = ConnectionInfo(
            websocket=mock_websocket,
            user_id=1,
            job_id=None,
            connected_at=datetime.utcnow(),
            last_activity=datetime.utcnow() - timedelta(minutes=5),
            connection_id="test_conn_id"
        )
        
        old_activity = conn_info.last_activity
        conn_info.update_activity()
        
        assert conn_info.last_activity > old_activity

class TestWebSocketConnectionPool:
    """Test cases for WebSocket connection pool."""
    
    async def test_add_connection(self, connection_pool, mock_websocket):
        """Test adding a connection to the pool."""
        connection_id = "test_conn_1"
        user_id = 1
        job_id = "test_job_1"
        
        success = await connection_pool.add_connection(
            mock_websocket, connection_id, user_id, job_id
        )
        
        assert success is True
        assert connection_id in connection_pool.connections
        assert job_id in connection_pool.job_connections
        assert user_id in connection_pool.user_connections
        assert connection_pool.metrics.active_connections == 1
        assert connection_pool.metrics.total_connects == 1
    
    async def test_remove_connection(self, connection_pool, mock_websocket):
        """Test removing a connection from the pool."""
        connection_id = "test_conn_1"
        user_id = 1
        job_id = "test_job_1"
        
        # Add connection first
        await connection_pool.add_connection(mock_websocket, connection_id, user_id, job_id)
        
        # Remove connection
        await connection_pool.remove_connection(connection_id)
        
        assert connection_id not in connection_pool.connections
        assert job_id not in connection_pool.job_connections
        assert user_id not in connection_pool.user_connections
        assert connection_pool.metrics.active_connections == 0
        assert connection_pool.metrics.total_disconnects == 1
    
    async def test_send_to_connection(self, connection_pool, mock_websocket):
        """Test sending a message to a specific connection."""
        connection_id = "test_conn_1"
        
        # Add connection
        await connection_pool.add_connection(mock_websocket, connection_id)
        
        # Send message
        message = {"type": "test", "data": "hello"}
        success = await connection_pool.send_to_connection(connection_id, message)
        
        assert success is True
        mock_websocket.send_json.assert_called_once_with(message)
        assert connection_pool.metrics.messages_sent == 1
    
    async def test_broadcast_to_job(self, connection_pool, mock_websocket):
        """Test broadcasting to all connections for a job."""
        job_id = "test_job_1"
        
        # Add multiple connections for the same job
        mock_ws1 = AsyncMock(spec=WebSocket)
        mock_ws2 = AsyncMock(spec=WebSocket)
        mock_ws1.send_json = AsyncMock()
        mock_ws2.send_json = AsyncMock()
        
        await connection_pool.add_connection(mock_ws1, "conn_1", job_id=job_id)
        await connection_pool.add_connection(mock_ws2, "conn_2", job_id=job_id)
        
        # Broadcast message
        message = {"type": "job_update", "status": "processing"}
        sent_count = await connection_pool.broadcast_to_job(job_id, message)
        
        assert sent_count == 2
        mock_ws1.send_json.assert_called_once_with(message)
        mock_ws2.send_json.assert_called_once_with(message)
    
    async def test_broadcast_to_user(self, connection_pool):
        """Test broadcasting to all connections for a user."""
        user_id = 1
        
        # Add multiple connections for the same user
        mock_ws1 = AsyncMock(spec=WebSocket)
        mock_ws2 = AsyncMock(spec=WebSocket)
        mock_ws1.send_json = AsyncMock()
        mock_ws2.send_json = AsyncMock()
        
        await connection_pool.add_connection(mock_ws1, "conn_1", user_id=user_id)
        await connection_pool.add_connection(mock_ws2, "conn_2", user_id=user_id)
        
        # Broadcast message
        message = {"type": "user_notification", "message": "Hello user!"}
        sent_count = await connection_pool.broadcast_to_user(user_id, message)
        
        assert sent_count == 2
        mock_ws1.send_json.assert_called_once_with(message)
        mock_ws2.send_json.assert_called_once_with(message)
    
    async def test_connection_limit(self, mock_websocket):
        """Test connection pool maximum limit."""
        small_pool = WebSocketConnectionPool(max_connections=2)
        
        # Add connections up to limit
        success1 = await small_pool.add_connection(mock_websocket, "conn_1")
        success2 = await small_pool.add_connection(mock_websocket, "conn_2")
        success3 = await small_pool.add_connection(mock_websocket, "conn_3")
        
        assert success1 is True
        assert success2 is True
        assert success3 is False  # Should be rejected
        assert len(small_pool.connections) == 2
    
    async def test_cleanup_stale_connections(self, connection_pool, mock_websocket):
        """Test cleanup of stale connections."""
        connection_id = "stale_conn"
        
        # Add connection
        await connection_pool.add_connection(mock_websocket, connection_id)
        
        # Manually set last_activity to old time
        conn_info = connection_pool.connections[connection_id]
        conn_info.last_activity = datetime.utcnow() - timedelta(minutes=31)
        
        # Run cleanup (30 minute threshold)
        await connection_pool.cleanup_stale_connections(max_idle_minutes=30)
        
        # Connection should be removed
        assert connection_id not in connection_pool.connections
        mock_websocket.close.assert_called_once()

class TestWebSocketMessageQueue:
    """Test cases for WebSocket message queue."""
    
    async def test_message_queue_initialization(self, message_queue):
        """Test message queue initialization."""
        assert message_queue.redis_client is not None
        assert message_queue.pubsub is not None
    
    async def test_publish_job_update(self, message_queue):
        """Test publishing job update messages."""
        job_id = "test_job_1"
        status = "processing"
        progress = 50
        message = "Half complete"
        
        await message_queue.publish_job_update(job_id, status, progress, message)
        
        # Verify Redis publish was called
        message_queue.redis_client.publish.assert_called_once()
        call_args = message_queue.redis_client.publish.call_args
        
        assert call_args[0][0] == "websocket:job_updates"
        published_data = json.loads(call_args[0][1])
        assert published_data["job_id"] == job_id
        assert published_data["status"] == status
        assert published_data["progress"] == progress
    
    async def test_publish_user_notification(self, message_queue):
        """Test publishing user notification messages."""
        user_id = 1
        notification_type = "job_completed"
        message = "Your job is done!"
        
        await message_queue.publish_user_notification(user_id, notification_type, message)
        
        message_queue.redis_client.publish.assert_called_once()
        call_args = message_queue.redis_client.publish.call_args
        
        assert call_args[0][0] == "websocket:user_notifications"
        published_data = json.loads(call_args[0][1])
        assert published_data["user_id"] == user_id
        assert published_data["notification_type"] == notification_type
    
    async def test_publish_system_broadcast(self, message_queue):
        """Test publishing system broadcast messages."""
        message = "System maintenance in 30 minutes"
        broadcast_type = "maintenance"
        
        await message_queue.publish_system_broadcast(message, broadcast_type)
        
        message_queue.redis_client.publish.assert_called_once()
        call_args = message_queue.redis_client.publish.call_args
        
        assert call_args[0][0] == "websocket:system_broadcasts"
        published_data = json.loads(call_args[0][1])
        assert published_data["message"] == message
        assert published_data["broadcast_type"] == broadcast_type

class TestEnhancedWebSocketService:
    """Test cases for the enhanced WebSocket service."""
    
    async def test_service_initialization(self, websocket_service):
        """Test WebSocket service initialization."""
        assert websocket_service.connection_pool is not None
        assert websocket_service.message_queue is not None
        assert websocket_service.is_running is True
    
    async def test_connect_websocket(self, websocket_service, mock_websocket):
        """Test WebSocket connection through service."""
        user_id = 1
        job_id = "test_job"
        
        connection_id = await websocket_service.connect_websocket(
            mock_websocket, user_id, job_id
        )
        
        assert connection_id is not None
        assert len(connection_id) > 0
        mock_websocket.accept.assert_called_once()
        
        # Verify connection was added to pool
        assert connection_id in websocket_service.connection_pool.connections
    
    async def test_send_job_update(self, websocket_service):
        """Test sending job updates through service."""
        job_id = "test_job"
        status = "completed"
        progress = 100
        message = "Job finished"
        
        await websocket_service.send_job_update(job_id, status, progress, message)
        
        # Verify message was published
        websocket_service.message_queue.redis_client.publish.assert_called()
    
    async def test_get_metrics(self, websocket_service):
        """Test getting service metrics."""
        metrics = websocket_service.get_metrics()
        
        assert "connection_pool" in metrics
        assert "messaging" in metrics
        assert "service_status" in metrics
        assert "timestamp" in metrics
        
        # Check specific metric fields
        assert "active_connections" in metrics["connection_pool"]
        assert "messages_sent" in metrics["messaging"]
        assert "is_running" in metrics["service_status"]
    
    async def test_get_connection_status(self, websocket_service, mock_websocket):
        """Test getting connection status."""
        # Add some connections
        await websocket_service.connect_websocket(mock_websocket, user_id=1, job_id="job1")
        await websocket_service.connect_websocket(mock_websocket, user_id=2, job_id="job2")
        
        status = websocket_service.get_connection_status()
        
        assert "total_connections" in status
        assert "job_connections" in status
        assert "user_connections" in status
        assert "utilization_percent" in status
        
        assert status["total_connections"] == 2

class TestWebSocketJobIntegration:
    """Test cases for WebSocket job integration."""
    
    async def test_job_notifier_initialization(self):
        """Test WebSocket job notifier initialization."""
        with patch('api.services.websocket_job_integration.get_websocket_service') as mock_service:
            mock_ws_service = AsyncMock()
            mock_service.return_value = mock_ws_service
            
            notifier = WebSocketJobNotifier()
            await notifier.initialize()
            
            assert notifier._initialized is True
            assert notifier.websocket_service == mock_ws_service
    
    async def test_notify_job_status_change(self):
        """Test job status change notification."""
        with patch('api.services.websocket_job_integration.get_websocket_service') as mock_service:
            mock_ws_service = AsyncMock()
            mock_ws_service.send_job_update = AsyncMock()
            mock_ws_service.send_user_notification = AsyncMock()
            mock_service.return_value = mock_ws_service
            
            notifier = WebSocketJobNotifier()
            await notifier.initialize()
            
            # Create test job
            job = Job(
                id="test_job",
                user_id=1,
                original_filename="test.mp3",
                saved_filename="saved.mp3",
                model="small",
                status=JobStatusEnum.COMPLETED
            )
            
            await notifier.notify_job_status_change(job, previous_status="processing")
            
            # Verify notifications were sent
            mock_ws_service.send_job_update.assert_called_once()
            mock_ws_service.send_user_notification.assert_called_once()
    
    async def test_notify_job_progress(self):
        """Test job progress notification."""
        with patch('api.services.websocket_job_integration.get_job_notifier') as mock_notifier:
            mock_job_notifier = AsyncMock()
            mock_job_notifier.notify_job_progress = AsyncMock()
            mock_notifier.return_value = mock_job_notifier
            
            await notify_job_progress_update("test_job", 75, "Almost done", 1)
            
            mock_job_notifier.notify_job_progress.assert_called_once_with(
                job_id="test_job",
                progress=75,
                message="Almost done",
                user_id=1
            )
    
    async def test_notify_job_completed(self):
        """Test job completion notification."""
        with patch('api.services.websocket_job_integration.get_job_notifier') as mock_notifier:
            mock_job_notifier = AsyncMock()
            mock_job_notifier.websocket_service = AsyncMock()
            mock_job_notifier.websocket_service.send_job_update = AsyncMock()
            mock_job_notifier.websocket_service.send_user_notification = AsyncMock()
            mock_notifier.return_value = mock_job_notifier
            
            await notify_job_completed("test_job", 1, "/download/test_job")
            
            # Verify both job update and user notification were sent
            mock_job_notifier.websocket_service.send_job_update.assert_called_once()
            mock_job_notifier.websocket_service.send_user_notification.assert_called_once()
    
    async def test_notify_job_failed(self):
        """Test job failure notification."""
        with patch('api.services.websocket_job_integration.get_job_notifier') as mock_notifier:
            mock_job_notifier = AsyncMock()
            mock_job_notifier.notify_job_error = AsyncMock()
            mock_notifier.return_value = mock_job_notifier
            
            await notify_job_failed("test_job", "Processing error", 1)
            
            mock_job_notifier.notify_job_error.assert_called_once_with(
                job_id="test_job",
                error_message="Processing error",
                user_id=1
            )

class TestWebSocketPerformance:
    """Test cases for WebSocket performance and scaling."""
    
    async def test_multiple_connections_performance(self, connection_pool):
        """Test performance with multiple connections."""
        num_connections = 50
        connections = []
        
        # Add multiple connections
        for i in range(num_connections):
            mock_ws = AsyncMock(spec=WebSocket)
            mock_ws.send_json = AsyncMock()
            
            success = await connection_pool.add_connection(
                mock_ws, f"conn_{i}", user_id=i % 10, job_id=f"job_{i % 5}"
            )
            assert success is True
            connections.append(mock_ws)
        
        # Test broadcast performance
        message = {"type": "test_broadcast", "data": "performance_test"}
        sent_count = await connection_pool.broadcast_to_all(message)
        
        assert sent_count == num_connections
        assert connection_pool.metrics.active_connections == num_connections
    
    async def test_message_throughput(self, connection_pool, mock_websocket):
        """Test message sending throughput."""
        # Add connection
        connection_id = "throughput_test"
        await connection_pool.add_connection(mock_websocket, connection_id)
        
        # Send multiple messages rapidly
        num_messages = 100
        for i in range(num_messages):
            await connection_pool.send_to_connection(connection_id, {
                "type": "throughput_test",
                "message_id": i
            })
        
        assert connection_pool.metrics.messages_sent == num_messages
        assert mock_websocket.send_json.call_count == num_messages
    
    async def test_connection_scaling(self):
        """Test connection pool scaling behavior."""
        # Test with larger connection pool
        large_pool = WebSocketConnectionPool(max_connections=1000)
        
        # Add many connections
        num_connections = 500
        for i in range(num_connections):
            mock_ws = AsyncMock(spec=WebSocket)
            success = await large_pool.add_connection(mock_ws, f"scale_conn_{i}")
            assert success is True
        
        assert len(large_pool.connections) == num_connections
        assert large_pool.metrics.active_connections == num_connections
        
        # Cleanup
        await large_pool.stop_cleanup_task()

class TestErrorHandling:
    """Test cases for error handling and recovery."""
    
    async def test_connection_send_error(self, connection_pool):
        """Test handling of connection send errors."""
        mock_ws = AsyncMock(spec=WebSocket)
        mock_ws.send_json.side_effect = Exception("Connection lost")
        
        connection_id = "error_conn"
        await connection_pool.add_connection(mock_ws, connection_id)
        
        # Try to send message (should handle error gracefully)
        success = await connection_pool.send_to_connection(connection_id, {"type": "test"})
        
        assert success is False
        assert connection_id not in connection_pool.connections  # Should be removed
        assert connection_pool.metrics.connection_errors == 1
    
    async def test_redis_connection_failure(self):
        """Test handling of Redis connection failures."""
        with patch('api.services.enhanced_websocket_service.redis.from_url') as mock_redis:
            mock_redis.side_effect = Exception("Redis connection failed")
            
            queue = WebSocketMessageQueue("redis://invalid:6379")
            
            with pytest.raises(Exception):
                await queue.initialize()
    
    async def test_graceful_shutdown(self, websocket_service, mock_websocket):
        """Test graceful service shutdown."""
        # Add some connections
        conn_id1 = await websocket_service.connect_websocket(mock_websocket, user_id=1)
        conn_id2 = await websocket_service.connect_websocket(mock_websocket, user_id=2)
        
        # Shutdown service
        await websocket_service.shutdown()
        
        assert websocket_service.is_running is False
        assert len(websocket_service.connection_pool.connections) == 0
        
        # Verify connections were closed
        assert mock_websocket.close.call_count >= 2

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
