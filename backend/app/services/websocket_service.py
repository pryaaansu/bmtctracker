"""
WebSocket service for real-time data streaming and subscription management
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Set, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum
import weakref

from sqlalchemy.orm import Session
from fastapi import WebSocket

from ..core.database import get_db
from ..models.location import VehicleLocation
from ..models.bus import Bus
from ..models.trip import Trip, TripStatus
from ..models.route import Route
from ..models.api_key import APIKey

logger = logging.getLogger(__name__)

class MessageType(Enum):
    LOCATION_UPDATE = "location_update"
    VEHICLE_STATUS_UPDATE = "vehicle_status_update"
    TRIP_UPDATE = "trip_update"
    ROUTE_UPDATE = "route_update"
    SUBSCRIPTION_UPDATE = "subscription_update"
    PING = "ping"
    PONG = "pong"
    ERROR = "error"
    INFO = "info"
    HEARTBEAT = "heartbeat"

@dataclass
class Subscription:
    """Represents a WebSocket subscription"""
    connection_id: str
    api_key_id: int
    vehicle_ids: Set[int]
    route_ids: Set[int]
    all_vehicles: bool
    all_routes: bool
    message_types: Set[MessageType]
    created_at: datetime
    last_activity: datetime

@dataclass
class ConnectionInfo:
    """Represents WebSocket connection information"""
    websocket: WebSocket
    api_key: APIKey
    connection_id: str
    connected_at: datetime
    last_ping: datetime
    subscription: Optional[Subscription] = None
    is_alive: bool = True

class WebSocketService:
    """Service for managing WebSocket connections and real-time data streaming"""
    
    def __init__(self):
        self.connections: Dict[str, ConnectionInfo] = {}
        self.subscriptions: Dict[str, Subscription] = {}
        self.message_queue: Dict[str, List[Dict[str, Any]]] = {}
        self.broadcast_tasks: List[asyncio.Task] = []
        self.cleanup_task: Optional[asyncio.Task] = None
        self.is_running = False
        
        # Statistics
        self.stats = {
            "total_connections": 0,
            "active_connections": 0,
            "messages_sent": 0,
            "messages_failed": 0,
            "subscriptions_created": 0,
            "subscriptions_removed": 0
        }
    
    async def start(self):
        """Start the WebSocket service"""
        if self.is_running:
            return
        
        self.is_running = True
        logger.info("Starting WebSocket service")
        
        # Start background tasks
        self.cleanup_task = asyncio.create_task(self._cleanup_connections())
        self.broadcast_tasks = [
            asyncio.create_task(self._broadcast_location_updates()),
            asyncio.create_task(self._broadcast_trip_updates()),
            asyncio.create_task(self._broadcast_vehicle_status_updates()),
            asyncio.create_task(self._heartbeat_connections())
        ]
        
        logger.info("WebSocket service started")
    
    async def stop(self):
        """Stop the WebSocket service"""
        if not self.is_running:
            return
        
        self.is_running = False
        logger.info("Stopping WebSocket service")
        
        # Cancel all background tasks
        if self.cleanup_task:
            self.cleanup_task.cancel()
        
        for task in self.broadcast_tasks:
            task.cancel()
        
        # Close all connections
        for connection_id, conn_info in list(self.connections.items()):
            await self.disconnect(connection_id)
        
        logger.info("WebSocket service stopped")
    
    async def connect(self, websocket: WebSocket, api_key: APIKey) -> str:
        """Accept a new WebSocket connection"""
        connection_id = f"ws_{int(time.time() * 1000)}_{api_key.id}_{len(self.connections)}"
        
        try:
            await websocket.accept()
            
            # Create connection info
            conn_info = ConnectionInfo(
                websocket=websocket,
                api_key=api_key,
                connection_id=connection_id,
                connected_at=datetime.utcnow(),
                last_ping=datetime.utcnow()
            )
            
            # Store connection
            self.connections[connection_id] = conn_info
            self.stats["total_connections"] += 1
            self.stats["active_connections"] += 1
            
            # Send welcome message
            await self._send_message(connection_id, {
                "type": MessageType.INFO.value,
                "message": "Connected to BMTC real-time data stream",
                "connection_id": connection_id,
                "timestamp": datetime.utcnow().isoformat(),
                "available_endpoints": [
                    "/ws/locations",
                    "/ws/trips",
                    "/ws/vehicles"
                ]
            })
            
            logger.info(f"WebSocket connected: {connection_id} (API Key: {api_key.key_name})")
            return connection_id
            
        except Exception as e:
            logger.error(f"Error connecting WebSocket {connection_id}: {e}")
            await self.disconnect(connection_id)
            raise
    
    async def disconnect(self, connection_id: str):
        """Disconnect a WebSocket connection"""
        if connection_id in self.connections:
            conn_info = self.connections[connection_id]
            
            try:
                await conn_info.websocket.close()
            except Exception as e:
                logger.warning(f"Error closing WebSocket {connection_id}: {e}")
            
            # Remove from tracking
            del self.connections[connection_id]
            if connection_id in self.subscriptions:
                del self.subscriptions[connection_id]
            if connection_id in self.message_queue:
                del self.message_queue[connection_id]
            
            self.stats["active_connections"] -= 1
            logger.info(f"WebSocket disconnected: {connection_id}")
    
    async def handle_message(self, connection_id: str, message: Dict[str, Any]):
        """Handle incoming WebSocket message"""
        if connection_id not in self.connections:
            return
        
        conn_info = self.connections[connection_id]
        conn_info.last_ping = datetime.utcnow()
        
        try:
            message_type = message.get("type")
            
            if message_type == "subscribe":
                await self._handle_subscription(connection_id, message.get("data", {}))
            elif message_type == "unsubscribe":
                await self._handle_unsubscription(connection_id, message.get("data", {}))
            elif message_type == "pong":
                # Update last ping time
                conn_info.last_ping = datetime.utcnow()
            elif message_type == "get_status":
                await self._send_connection_status(connection_id)
            elif message_type == "get_subscription":
                await self._send_subscription_info(connection_id)
            else:
                await self._send_message(connection_id, {
                    "type": MessageType.ERROR.value,
                    "message": f"Unknown message type: {message_type}",
                    "timestamp": datetime.utcnow().isoformat()
                })
        
        except Exception as e:
            logger.error(f"Error handling message from {connection_id}: {e}")
            await self._send_message(connection_id, {
                "type": MessageType.ERROR.value,
                "message": f"Error processing message: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            })
    
    async def _handle_subscription(self, connection_id: str, data: Dict[str, Any]):
        """Handle subscription request"""
        conn_info = self.connections[connection_id]
        
        # Parse subscription data
        vehicle_ids = set(data.get("vehicle_ids", []))
        route_ids = set(data.get("route_ids", []))
        all_vehicles = data.get("all_vehicles", False)
        all_routes = data.get("all_routes", False)
        message_types = set(data.get("message_types", [MessageType.LOCATION_UPDATE.value]))
        
        # Convert message type strings to enums
        message_type_enums = set()
        for msg_type in message_types:
            try:
                message_type_enums.add(MessageType(msg_type))
            except ValueError:
                logger.warning(f"Unknown message type: {msg_type}")
        
        # Create subscription
        subscription = Subscription(
            connection_id=connection_id,
            api_key_id=conn_info.api_key.id,
            vehicle_ids=vehicle_ids,
            route_ids=route_ids,
            all_vehicles=all_vehicles,
            all_routes=all_routes,
            message_types=message_type_enums,
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow()
        )
        
        # Store subscription
        self.subscriptions[connection_id] = subscription
        conn_info.subscription = subscription
        self.stats["subscriptions_created"] += 1
        
        # Send confirmation
        await self._send_message(connection_id, {
            "type": MessageType.SUBSCRIPTION_UPDATE.value,
            "message": "Subscription updated successfully",
            "data": {
                "vehicle_ids": list(vehicle_ids),
                "route_ids": list(route_ids),
                "all_vehicles": all_vehicles,
                "all_routes": all_routes,
                "message_types": list(message_types)
            },
            "timestamp": datetime.utcnow().isoformat()
        })
        
        logger.info(f"Subscription created for {connection_id}: vehicles={vehicle_ids}, routes={route_ids}")
    
    async def _handle_unsubscription(self, connection_id: str, data: Dict[str, Any]):
        """Handle unsubscription request"""
        if connection_id in self.subscriptions:
            del self.subscriptions[connection_id]
            if connection_id in self.connections:
                self.connections[connection_id].subscription = None
            self.stats["subscriptions_removed"] += 1
            
            await self._send_message(connection_id, {
                "type": MessageType.SUBSCRIPTION_UPDATE.value,
                "message": "Unsubscribed successfully",
                "timestamp": datetime.utcnow().isoformat()
            })
    
    async def _send_connection_status(self, connection_id: str):
        """Send connection status information"""
        if connection_id not in self.connections:
            return
        
        conn_info = self.connections[connection_id]
        subscription = conn_info.subscription
        
        status = {
            "connection_id": connection_id,
            "api_key_id": conn_info.api_key.id,
            "api_key_name": conn_info.api_key.name,
            "connected_at": conn_info.connected_at.isoformat(),
            "last_ping": conn_info.last_ping.isoformat(),
            "is_alive": conn_info.is_alive,
            "subscription": {
                "vehicle_ids": list(subscription.vehicle_ids) if subscription else [],
                "route_ids": list(subscription.route_ids) if subscription else [],
                "all_vehicles": subscription.all_vehicles if subscription else False,
                "all_routes": subscription.all_routes if subscription else False,
                "message_types": [t.value for t in subscription.message_types] if subscription else []
            } if subscription else None,
            "stats": self.stats
        }
        
        await self._send_message(connection_id, {
            "type": MessageType.INFO.value,
            "message": "Connection status",
            "data": status,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def _send_subscription_info(self, connection_id: str):
        """Send subscription information"""
        if connection_id not in self.subscriptions:
            await self._send_message(connection_id, {
                "type": MessageType.INFO.value,
                "message": "No active subscription",
                "timestamp": datetime.utcnow().isoformat()
            })
            return
        
        subscription = self.subscriptions[connection_id]
        
        await self._send_message(connection_id, {
            "type": MessageType.INFO.value,
            "message": "Subscription information",
            "data": {
                "vehicle_ids": list(subscription.vehicle_ids),
                "route_ids": list(subscription.route_ids),
                "all_vehicles": subscription.all_vehicles,
                "all_routes": subscription.all_routes,
                "message_types": [t.value for t in subscription.message_types],
                "created_at": subscription.created_at.isoformat(),
                "last_activity": subscription.last_activity.isoformat()
            },
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def _send_message(self, connection_id: str, message: Dict[str, Any]):
        """Send a message to a specific connection"""
        if connection_id not in self.connections:
            return
        
        conn_info = self.connections[connection_id]
        
        try:
            await conn_info.websocket.send_text(json.dumps(message))
            self.stats["messages_sent"] += 1
        except Exception as e:
            logger.error(f"Error sending message to {connection_id}: {e}")
            self.stats["messages_failed"] += 1
            # Mark connection as dead
            conn_info.is_alive = False
    
    async def broadcast_message(self, message: Dict[str, Any], vehicle_id: Optional[int] = None, route_id: Optional[int] = None):
        """Broadcast a message to all relevant subscribers"""
        for connection_id, subscription in self.subscriptions.items():
            should_send = False
            
            # Check if subscription matches the message
            if vehicle_id and (subscription.all_vehicles or vehicle_id in subscription.vehicle_ids):
                should_send = True
            elif route_id and (subscription.all_routes or route_id in subscription.route_ids):
                should_send = True
            elif subscription.all_vehicles and subscription.all_routes:
                should_send = True
            
            # Check message type
            if should_send and message.get("type") in [t.value for t in subscription.message_types]:
                await self._send_message(connection_id, message)
    
    async def _broadcast_location_updates(self):
        """Background task to broadcast location updates"""
        while self.is_running:
            try:
                # Get recent location updates
                db = next(get_db())
                cutoff_time = datetime.utcnow() - timedelta(seconds=30)
                
                recent_locations = db.query(VehicleLocation).filter(
                    VehicleLocation.recorded_at >= cutoff_time,
                    VehicleLocation.is_recent == True
                ).all()
                
                for location in recent_locations:
                    # Get vehicle and trip information
                    bus = db.query(Bus).filter(Bus.id == location.vehicle_id).first()
                    active_trip = db.query(Trip).filter(
                        Trip.vehicle_id == location.vehicle_id,
                        Trip.status == TripStatus.ACTIVE
                    ).first()
                    
                    if bus:
                        message = {
                            "type": MessageType.LOCATION_UPDATE.value,
                            "data": {
                                "vehicle_id": location.vehicle_id,
                                "vehicle_number": bus.vehicle_number,
                                "latitude": location.latitude,
                                "longitude": location.longitude,
                                "speed": location.speed,
                                "bearing": location.bearing,
                                "recorded_at": location.recorded_at.isoformat(),
                                "is_recent": location.is_recent,
                                "trip_id": active_trip.id if active_trip else None,
                                "route_id": active_trip.route_id if active_trip else None
                            },
                            "timestamp": datetime.utcnow().isoformat()
                        }
                        
                        await self.broadcast_message(
                            message,
                            vehicle_id=location.vehicle_id,
                            route_id=active_trip.route_id if active_trip else None
                        )
                
                await asyncio.sleep(5)  # Update every 5 seconds
                
            except Exception as e:
                logger.error(f"Error in location broadcast task: {e}")
                await asyncio.sleep(10)
    
    async def _broadcast_trip_updates(self):
        """Background task to broadcast trip updates"""
        while self.is_running:
            try:
                # This would monitor for trip status changes
                # For now, we'll just sleep
                await asyncio.sleep(10)
                
            except Exception as e:
                logger.error(f"Error in trip broadcast task: {e}")
                await asyncio.sleep(10)
    
    async def _broadcast_vehicle_status_updates(self):
        """Background task to broadcast vehicle status updates"""
        while self.is_running:
            try:
                # This would monitor for vehicle status changes
                # For now, we'll just sleep
                await asyncio.sleep(15)
                
            except Exception as e:
                logger.error(f"Error in vehicle status broadcast task: {e}")
                await asyncio.sleep(10)
    
    async def _heartbeat_connections(self):
        """Background task to send heartbeat messages and detect dead connections"""
        while self.is_running:
            try:
                current_time = datetime.utcnow()
                dead_connections = []
                
                for connection_id, conn_info in self.connections.items():
                    # Send ping if last ping was more than 30 seconds ago
                    if (current_time - conn_info.last_ping).total_seconds() > 30:
                        await self._send_message(connection_id, {
                            "type": MessageType.PING.value,
                            "timestamp": current_time.isoformat()
                        })
                    
                    # Mark as dead if no response for more than 60 seconds
                    if (current_time - conn_info.last_ping).total_seconds() > 60:
                        dead_connections.append(connection_id)
                
                # Remove dead connections
                for connection_id in dead_connections:
                    await self.disconnect(connection_id)
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in heartbeat task: {e}")
                await asyncio.sleep(10)
    
    async def _cleanup_connections(self):
        """Background task to clean up inactive connections"""
        while self.is_running:
            try:
                # Clean up message queues for disconnected connections
                current_connections = set(self.connections.keys())
                for connection_id in list(self.message_queue.keys()):
                    if connection_id not in current_connections:
                        del self.message_queue[connection_id]
                
                await asyncio.sleep(60)  # Cleanup every minute
                
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")
                await asyncio.sleep(30)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics"""
        return {
            **self.stats,
            "active_subscriptions": len(self.subscriptions),
            "queued_messages": sum(len(queue) for queue in self.message_queue.values()),
            "is_running": self.is_running
        }
    
    def get_connection_info(self, connection_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific connection"""
        if connection_id not in self.connections:
            return None
        
        conn_info = self.connections[connection_id]
        subscription = conn_info.subscription
        
        return {
            "connection_id": connection_id,
            "api_key_id": conn_info.api_key.id,
            "api_key_name": conn_info.api_key.key_name,
            "connected_at": conn_info.connected_at.isoformat(),
            "last_ping": conn_info.last_ping.isoformat(),
            "is_alive": conn_info.is_alive,
            "subscription": {
                "vehicle_ids": list(subscription.vehicle_ids) if subscription else [],
                "route_ids": list(subscription.route_ids) if subscription else [],
                "all_vehicles": subscription.all_vehicles if subscription else False,
                "all_routes": subscription.all_routes if subscription else False,
                "message_types": [t.value for t in subscription.message_types] if subscription else []
            } if subscription else None
        }

# Global WebSocket service instance
websocket_service = WebSocketService()

