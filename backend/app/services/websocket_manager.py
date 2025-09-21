"""
WebSocket Manager for Real-time Location Broadcasting

Manages WebSocket connections and broadcasts location updates to connected clients.
"""

import asyncio
import json
import logging
from typing import Dict, List, Set
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime
import redis.asyncio as redis

logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manages WebSocket connections for real-time updates"""
    
    def __init__(self):
        # Store active connections by type
        self.active_connections: Dict[str, Set[WebSocket]] = {
            "realtime": set(),
            "admin": set(),
            "driver": set()
        }
        self.connection_metadata: Dict[WebSocket, Dict] = {}
        self.redis_client: redis.Redis = None
        self.subscriber_task: asyncio.Task = None
    
    async def initialize(self):
        """Initialize the WebSocket manager"""
        try:
            self.redis_client = redis.from_url("redis://localhost:6379")
            # Start Redis subscriber for location updates
            self.subscriber_task = asyncio.create_task(self._redis_subscriber())
            logger.info("WebSocket manager initialized")
        except Exception as e:
            logger.error(f"Failed to initialize WebSocket manager: {e}")
    
    async def connect(self, websocket: WebSocket, connection_type: str = "realtime", 
                     metadata: Dict = None):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        
        if connection_type not in self.active_connections:
            connection_type = "realtime"
        
        self.active_connections[connection_type].add(websocket)
        self.connection_metadata[websocket] = {
            "type": connection_type,
            "connected_at": datetime.now(),
            "metadata": metadata or {}
        }
        
        logger.info(f"New {connection_type} WebSocket connection established. "
                   f"Total connections: {self.get_connection_count()}")
        
        # Send initial connection confirmation
        await self._send_to_connection(websocket, {
            "type": "connection_established",
            "connection_type": connection_type,
            "timestamp": datetime.now().isoformat()
        })
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        connection_info = self.connection_metadata.get(websocket, {})
        connection_type = connection_info.get("type", "realtime")
        
        self.active_connections[connection_type].discard(websocket)
        self.connection_metadata.pop(websocket, None)
        
        logger.info(f"{connection_type.title()} WebSocket connection closed. "
                   f"Total connections: {self.get_connection_count()}")
    
    async def broadcast_to_type(self, connection_type: str, message: Dict):
        """Broadcast message to all connections of a specific type"""
        if connection_type not in self.active_connections:
            return
        
        connections = self.active_connections[connection_type].copy()
        if not connections:
            return
        
        message_json = json.dumps(message)
        disconnected = []
        
        for connection in connections:
            try:
                await connection.send_text(message_json)
            except Exception as e:
                logger.warning(f"Failed to send message to {connection_type} connection: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected connections
        for connection in disconnected:
            self.disconnect(connection)
    
    async def broadcast_location_update(self, location_data: Dict):
        """Broadcast location update to realtime connections"""
        message = {
            "type": "location_update",
            "data": location_data,
            "timestamp": datetime.now().isoformat()
        }
        await self.broadcast_to_type("realtime", message)
    
    async def broadcast_admin_update(self, update_data: Dict):
        """Broadcast admin update to admin connections"""
        message = {
            "type": "admin_update",
            "data": update_data,
            "timestamp": datetime.now().isoformat()
        }
        await self.broadcast_to_type("admin", message)
    
    async def send_to_connection(self, websocket: WebSocket, message: Dict):
        """Send message to a specific connection"""
        await self._send_to_connection(websocket, message)
    
    async def _send_to_connection(self, websocket: WebSocket, message: Dict):
        """Internal method to send message to connection"""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.warning(f"Failed to send message to connection: {e}")
            self.disconnect(websocket)
    
    async def _redis_subscriber(self):
        """Subscribe to Redis pub/sub for location updates"""
        if not self.redis_client:
            return
        
        try:
            pubsub = self.redis_client.pubsub()
            await pubsub.subscribe("location_updates", "admin_updates")
            
            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                        
                        if message["channel"] == b"location_updates":
                            await self.broadcast_location_update(data.get("data", {}))
                        elif message["channel"] == b"admin_updates":
                            await self.broadcast_admin_update(data.get("data", {}))
                            
                    except Exception as e:
                        logger.error(f"Error processing Redis message: {e}")
                        
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error in Redis subscriber: {e}")
        finally:
            if self.redis_client:
                await pubsub.unsubscribe("location_updates", "admin_updates")
    
    def get_connection_count(self) -> int:
        """Get total number of active connections"""
        return sum(len(connections) for connections in self.active_connections.values())
    
    def get_connection_stats(self) -> Dict:
        """Get connection statistics"""
        return {
            "total_connections": self.get_connection_count(),
            "realtime_connections": len(self.active_connections["realtime"]),
            "admin_connections": len(self.active_connections["admin"]),
            "driver_connections": len(self.active_connections["driver"])
        }
    
    async def handle_client_message(self, websocket: WebSocket, message: str):
        """Handle incoming message from client"""
        try:
            data = json.loads(message)
            message_type = data.get("type")
            
            if message_type == "ping":
                await self._send_to_connection(websocket, {
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                })
            elif message_type == "subscribe_vehicle":
                # Handle vehicle-specific subscription
                vehicle_id = data.get("vehicle_id")
                if vehicle_id:
                    connection_info = self.connection_metadata.get(websocket, {})
                    connection_info.setdefault("subscriptions", set()).add(f"vehicle_{vehicle_id}")
                    logger.info(f"Client subscribed to vehicle {vehicle_id}")
            elif message_type == "unsubscribe_vehicle":
                # Handle vehicle unsubscription
                vehicle_id = data.get("vehicle_id")
                if vehicle_id:
                    connection_info = self.connection_metadata.get(websocket, {})
                    subscriptions = connection_info.get("subscriptions", set())
                    subscriptions.discard(f"vehicle_{vehicle_id}")
                    logger.info(f"Client unsubscribed from vehicle {vehicle_id}")
            
        except json.JSONDecodeError:
            logger.warning("Received invalid JSON from WebSocket client")
        except Exception as e:
            logger.error(f"Error handling client message: {e}")
    
    async def cleanup(self):
        """Clean up resources"""
        if self.subscriber_task:
            self.subscriber_task.cancel()
            try:
                await self.subscriber_task
            except asyncio.CancelledError:
                pass
        
        if self.redis_client:
            await self.redis_client.close()
        
        # Close all connections
        for connection_type, connections in self.active_connections.items():
            for connection in connections.copy():
                try:
                    await connection.close()
                except:
                    pass
        
        logger.info("WebSocket manager cleaned up")

# Global instance
websocket_manager = ConnectionManager()

# WebSocket endpoint handlers
async def websocket_endpoint(websocket: WebSocket, connection_type: str = "realtime"):
    """Generic WebSocket endpoint handler"""
    await websocket_manager.connect(websocket, connection_type)
    
    try:
        while True:
            message = await websocket.receive_text()
            await websocket_manager.handle_client_message(websocket, message)
            
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        websocket_manager.disconnect(websocket)