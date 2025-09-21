"""
Tests for WebSocket Manager
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from app.services.websocket_manager import ConnectionManager


class TestConnectionManager:
    """Test cases for ConnectionManager"""
    
    @pytest.fixture
    def manager(self):
        """Create a ConnectionManager instance for testing"""
        manager = ConnectionManager()
        manager.redis_client = Mock()
        return manager
    
    @pytest.fixture
    def mock_websocket(self):
        """Create a mock WebSocket connection"""
        websocket = Mock()
        websocket.accept = AsyncMock()
        websocket.send_text = AsyncMock()
        websocket.close = AsyncMock()
        return websocket
    
    @pytest.mark.asyncio
    async def test_connect_websocket(self, manager, mock_websocket):
        """Test connecting a WebSocket"""
        await manager.connect(mock_websocket, "realtime")
        
        # Verify connection was accepted
        mock_websocket.accept.assert_called_once()
        
        # Verify connection was added to active connections
        assert mock_websocket in manager.active_connections["realtime"]
        assert mock_websocket in manager.connection_metadata
        
        # Verify metadata was stored
        metadata = manager.connection_metadata[mock_websocket]
        assert metadata["type"] == "realtime"
        assert "connected_at" in metadata
        
        # Verify initial message was sent
        mock_websocket.send_text.assert_called_once()
        sent_message = json.loads(mock_websocket.send_text.call_args[0][0])
        assert sent_message["type"] == "connection_established"
        assert sent_message["connection_type"] == "realtime"
    
    def test_disconnect_websocket(self, manager, mock_websocket):
        """Test disconnecting a WebSocket"""
        # First connect
        manager.active_connections["realtime"].add(mock_websocket)
        manager.connection_metadata[mock_websocket] = {
            "type": "realtime",
            "connected_at": datetime.now()
        }
        
        # Then disconnect
        manager.disconnect(mock_websocket)
        
        # Verify connection was removed
        assert mock_websocket not in manager.active_connections["realtime"]
        assert mock_websocket not in manager.connection_metadata
    
    @pytest.mark.asyncio
    async def test_broadcast_to_type(self, manager, mock_websocket):
        """Test broadcasting to connections of a specific type"""
        # Add connection
        manager.active_connections["realtime"].add(mock_websocket)
        
        test_message = {
            "type": "test",
            "data": {"vehicle_id": 1, "latitude": 12.9716}
        }
        
        await manager.broadcast_to_type("realtime", test_message)
        
        # Verify message was sent
        mock_websocket.send_text.assert_called_once()
        sent_message = json.loads(mock_websocket.send_text.call_args[0][0])
        assert sent_message == test_message
    
    @pytest.mark.asyncio
    async def test_broadcast_location_update(self, manager, mock_websocket):
        """Test broadcasting location updates"""
        # Add connection
        manager.active_connections["realtime"].add(mock_websocket)
        
        location_data = {
            "vehicle_id": 1,
            "latitude": 12.9716,
            "longitude": 77.5946,
            "speed": 25.0,
            "bearing": 90
        }
        
        await manager.broadcast_location_update(location_data)
        
        # Verify message was sent
        mock_websocket.send_text.assert_called_once()
        sent_message = json.loads(mock_websocket.send_text.call_args[0][0])
        assert sent_message["type"] == "location_update"
        assert sent_message["data"] == location_data
        assert "timestamp" in sent_message
    
    @pytest.mark.asyncio
    async def test_broadcast_admin_update(self, manager, mock_websocket):
        """Test broadcasting admin updates"""
        # Add admin connection
        manager.active_connections["admin"].add(mock_websocket)
        
        admin_data = {
            "metric": "active_buses",
            "value": 25,
            "change": "+2"
        }
        
        await manager.broadcast_admin_update(admin_data)
        
        # Verify message was sent
        mock_websocket.send_text.assert_called_once()
        sent_message = json.loads(mock_websocket.send_text.call_args[0][0])
        assert sent_message["type"] == "admin_update"
        assert sent_message["data"] == admin_data
    
    @pytest.mark.asyncio
    async def test_handle_client_message_ping(self, manager, mock_websocket):
        """Test handling ping message from client"""
        ping_message = json.dumps({"type": "ping"})
        
        await manager.handle_client_message(mock_websocket, ping_message)
        
        # Verify pong response was sent
        mock_websocket.send_text.assert_called_once()
        sent_message = json.loads(mock_websocket.send_text.call_args[0][0])
        assert sent_message["type"] == "pong"
        assert "timestamp" in sent_message
    
    @pytest.mark.asyncio
    async def test_handle_client_message_subscribe_vehicle(self, manager, mock_websocket):
        """Test handling vehicle subscription message"""
        # Add connection metadata
        manager.connection_metadata[mock_websocket] = {
            "type": "realtime",
            "connected_at": datetime.now(),
            "metadata": {}
        }
        
        subscribe_message = json.dumps({
            "type": "subscribe_vehicle",
            "vehicle_id": 123
        })
        
        await manager.handle_client_message(mock_websocket, subscribe_message)
        
        # Verify subscription was added
        subscriptions = manager.connection_metadata[mock_websocket].get("subscriptions", set())
        assert "vehicle_123" in subscriptions
    
    @pytest.mark.asyncio
    async def test_handle_client_message_unsubscribe_vehicle(self, manager, mock_websocket):
        """Test handling vehicle unsubscription message"""
        # Add connection metadata with existing subscription
        manager.connection_metadata[mock_websocket] = {
            "type": "realtime",
            "connected_at": datetime.now(),
            "metadata": {},
            "subscriptions": {"vehicle_123"}
        }
        
        unsubscribe_message = json.dumps({
            "type": "unsubscribe_vehicle",
            "vehicle_id": 123
        })
        
        await manager.handle_client_message(mock_websocket, unsubscribe_message)
        
        # Verify subscription was removed
        subscriptions = manager.connection_metadata[mock_websocket].get("subscriptions", set())
        assert "vehicle_123" not in subscriptions
    
    @pytest.mark.asyncio
    async def test_handle_invalid_json(self, manager, mock_websocket):
        """Test handling invalid JSON from client"""
        invalid_message = "invalid json {"
        
        # Should not raise exception
        await manager.handle_client_message(mock_websocket, invalid_message)
        
        # No message should be sent back
        mock_websocket.send_text.assert_not_called()
    
    def test_get_connection_count(self, manager, mock_websocket):
        """Test getting connection count"""
        assert manager.get_connection_count() == 0
        
        # Add connections
        manager.active_connections["realtime"].add(mock_websocket)
        manager.active_connections["admin"].add(Mock())
        
        assert manager.get_connection_count() == 2
    
    def test_get_connection_stats(self, manager):
        """Test getting connection statistics"""
        # Add mock connections
        manager.active_connections["realtime"].add(Mock())
        manager.active_connections["realtime"].add(Mock())
        manager.active_connections["admin"].add(Mock())
        
        stats = manager.get_connection_stats()
        
        assert stats["total_connections"] == 3
        assert stats["realtime_connections"] == 2
        assert stats["admin_connections"] == 1
        assert stats["driver_connections"] == 0
    
    @pytest.mark.asyncio
    async def test_broadcast_with_failed_connection(self, manager):
        """Test broadcasting when a connection fails"""
        # Create mock connections - one working, one failing
        working_websocket = Mock()
        working_websocket.send_text = AsyncMock()
        
        failing_websocket = Mock()
        failing_websocket.send_text = AsyncMock(side_effect=Exception("Connection failed"))
        
        # Add both connections
        manager.active_connections["realtime"].add(working_websocket)
        manager.active_connections["realtime"].add(failing_websocket)
        manager.connection_metadata[working_websocket] = {"type": "realtime"}
        manager.connection_metadata[failing_websocket] = {"type": "realtime"}
        
        test_message = {"type": "test", "data": "test"}
        
        await manager.broadcast_to_type("realtime", test_message)
        
        # Working connection should receive message
        working_websocket.send_text.assert_called_once()
        
        # Failing connection should be removed
        assert failing_websocket not in manager.active_connections["realtime"]
        assert failing_websocket not in manager.connection_metadata
        
        # Working connection should remain
        assert working_websocket in manager.active_connections["realtime"]
    
    @pytest.mark.asyncio
    async def test_cleanup(self, manager):
        """Test cleanup of resources"""
        # Add mock connections
        mock_websocket = Mock()
        mock_websocket.close = AsyncMock()
        manager.active_connections["realtime"].add(mock_websocket)
        
        # Mock Redis client
        manager.redis_client = Mock()
        manager.redis_client.close = AsyncMock()
        
        # Mock subscriber task
        manager.subscriber_task = Mock()
        manager.subscriber_task.cancel = Mock()
        
        await manager.cleanup()
        
        # Verify cleanup actions
        manager.subscriber_task.cancel.assert_called_once()
        manager.redis_client.close.assert_called_once()
        mock_websocket.close.assert_called_once()


@pytest.mark.asyncio
async def test_websocket_manager_initialization():
    """Test WebSocket manager initialization"""
    manager = ConnectionManager()
    
    with patch('redis.asyncio.from_url') as mock_redis:
        mock_redis.return_value = Mock()
        
        await manager.initialize()
        
        # Verify Redis client was created
        mock_redis.assert_called_once_with("redis://localhost:6379")
        assert manager.redis_client is not None


if __name__ == "__main__":
    pytest.main([__file__])