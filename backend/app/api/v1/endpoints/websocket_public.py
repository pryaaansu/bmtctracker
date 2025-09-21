from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import json
import asyncio
import time
from datetime import datetime, timedelta
import logging

from ....core.database import get_db
from ....services.api_auth_service import APIAuthService
from ....models.api_key import APIKey
from ....models.location import VehicleLocation
from ....models.bus import Bus
from ....models.trip import Trip, TripStatus
from ....models.route import Route

router = APIRouter()

# WebSocket connection manager
class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.subscriptions: Dict[str, Dict[str, Any]] = {}  # connection_id -> subscription data
        self.connection_metadata: Dict[str, Dict[str, Any]] = {}  # connection_id -> metadata
    
    async def connect(self, websocket: WebSocket, connection_id: str, api_key: APIKey):
        """Accept a WebSocket connection and store metadata"""
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        self.connection_metadata[connection_id] = {
            "api_key_id": api_key.id,
            "api_key_name": api_key.key_name,
            "connected_at": datetime.utcnow(),
            "last_ping": datetime.utcnow()
        }
        self.subscriptions[connection_id] = {
            "vehicle_ids": set(),
            "route_ids": set(),
            "all_vehicles": False,
            "all_routes": False
        }
        logging.info(f"WebSocket connected: {connection_id} (API Key: {api_key.key_name})")
    
    def disconnect(self, connection_id: str):
        """Remove a WebSocket connection"""
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
        if connection_id in self.subscriptions:
            del self.subscriptions[connection_id]
        if connection_id in self.connection_metadata:
            del self.connection_metadata[connection_id]
        logging.info(f"WebSocket disconnected: {connection_id}")
    
    async def send_message(self, connection_id: str, message: Dict[str, Any]):
        """Send a message to a specific connection"""
        if connection_id in self.active_connections:
            try:
                websocket = self.active_connections[connection_id]
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logging.error(f"Error sending message to {connection_id}: {e}")
                self.disconnect(connection_id)
    
    async def broadcast_to_subscribers(self, message: Dict[str, Any], vehicle_id: Optional[int] = None, route_id: Optional[int] = None):
        """Broadcast a message to all subscribers of specific vehicle or route"""
        for connection_id, subscription in self.subscriptions.items():
            should_send = False
            
            # Check if connection is subscribed to this vehicle/route
            if vehicle_id and (subscription["all_vehicles"] or vehicle_id in subscription["vehicle_ids"]):
                should_send = True
            elif route_id and (subscription["all_routes"] or route_id in subscription["route_ids"]):
                should_send = True
            elif subscription["all_vehicles"] and subscription["all_routes"]:
                should_send = True
            
            if should_send:
                await self.send_message(connection_id, message)
    
    def update_subscription(self, connection_id: str, subscription_data: Dict[str, Any]):
        """Update subscription for a connection"""
        if connection_id in self.subscriptions:
            self.subscriptions[connection_id].update(subscription_data)
    
    def get_connection_count(self) -> int:
        """Get the number of active connections"""
        return len(self.active_connections)
    
    def get_connection_info(self, connection_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific connection"""
        if connection_id in self.connection_metadata:
            metadata = self.connection_metadata[connection_id].copy()
            metadata["subscription"] = self.subscriptions.get(connection_id, {})
            return metadata
        return None

# Global WebSocket manager instance
websocket_manager = WebSocketManager()

# WebSocket message types
class MessageType:
    LOCATION_UPDATE = "location_update"
    VEHICLE_STATUS_UPDATE = "vehicle_status_update"
    TRIP_UPDATE = "trip_update"
    SUBSCRIPTION_UPDATE = "subscription_update"
    PING = "ping"
    PONG = "pong"
    ERROR = "error"
    INFO = "info"

async def authenticate_websocket(websocket: WebSocket, api_key: str, db: Session) -> Optional[APIKey]:
    """Authenticate WebSocket connection using API key"""
    try:
        auth_service = APIAuthService(db)
        api_key_obj = auth_service.authenticate_api_key(api_key)
        
        if not api_key_obj:
            await websocket.close(code=1008, reason="Invalid API key")
            return None
        
        # Check rate limits (WebSocket connections might have different limits)
        # For now, we'll allow WebSocket connections without strict rate limiting
        
        return api_key_obj
    except Exception as e:
        logging.error(f"WebSocket authentication error: {e}")
        await websocket.close(code=1008, reason="Authentication failed")
        return None

@router.websocket("/ws/locations")
async def websocket_locations(
    websocket: WebSocket,
    api_key: str = Query(..., description="API key for authentication"),
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for real-time location updates
    
    Subscribe to real-time vehicle location updates. Send subscription messages
    to filter by specific vehicles or routes.
    """
    # Authenticate the connection
    api_key_obj = await authenticate_websocket(websocket, api_key, db)
    if not api_key_obj:
        return
    
    connection_id = f"ws_{int(time.time() * 1000)}_{api_key_obj.id}"
    
    try:
        # Connect the WebSocket
        await websocket_manager.connect(websocket, connection_id, api_key_obj)
        
        # Send welcome message
        await websocket_manager.send_message(connection_id, {
            "type": MessageType.INFO,
            "message": "Connected to real-time location updates",
            "connection_id": connection_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Start ping/pong heartbeat
        async def heartbeat():
            while connection_id in websocket_manager.active_connections:
                try:
                    await websocket_manager.send_message(connection_id, {
                        "type": MessageType.PING,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    await asyncio.sleep(30)  # Ping every 30 seconds
                except Exception:
                    break
        
        # Start heartbeat task
        heartbeat_task = asyncio.create_task(heartbeat())
        
        # Listen for messages
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle different message types
                if message.get("type") == "subscribe":
                    # Handle subscription update
                    subscription_data = message.get("data", {})
                    websocket_manager.update_subscription(connection_id, subscription_data)
                    
                    await websocket_manager.send_message(connection_id, {
                        "type": MessageType.SUBSCRIPTION_UPDATE,
                        "message": "Subscription updated",
                        "data": websocket_manager.subscriptions[connection_id],
                        "timestamp": datetime.utcnow().isoformat()
                    })
                
                elif message.get("type") == "pong":
                    # Handle pong response
                    websocket_manager.connection_metadata[connection_id]["last_ping"] = datetime.utcnow()
                
                elif message.get("type") == "get_status":
                    # Send current connection status
                    status = websocket_manager.get_connection_info(connection_id)
                    await websocket_manager.send_message(connection_id, {
                        "type": MessageType.INFO,
                        "message": "Connection status",
                        "data": status,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                await websocket_manager.send_message(connection_id, {
                    "type": MessageType.ERROR,
                    "message": "Invalid JSON message",
                    "timestamp": datetime.utcnow().isoformat()
                })
            except Exception as e:
                logging.error(f"WebSocket error: {e}")
                await websocket_manager.send_message(connection_id, {
                    "type": MessageType.ERROR,
                    "message": f"Internal error: {str(e)}",
                    "timestamp": datetime.utcnow().isoformat()
                })
    
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logging.error(f"WebSocket connection error: {e}")
    finally:
        # Clean up
        heartbeat_task.cancel()
        websocket_manager.disconnect(connection_id)

@router.websocket("/ws/trips")
async def websocket_trips(
    websocket: WebSocket,
    api_key: str = Query(..., description="API key for authentication"),
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for real-time trip updates
    
    Subscribe to real-time trip status updates including start, end, and status changes.
    """
    # Authenticate the connection
    api_key_obj = await authenticate_websocket(websocket, api_key, db)
    if not api_key_obj:
        return
    
    connection_id = f"ws_trips_{int(time.time() * 1000)}_{api_key_obj.id}"
    
    try:
        # Connect the WebSocket
        await websocket_manager.connect(websocket, connection_id, api_key_obj)
        
        # Send welcome message
        await websocket_manager.send_message(connection_id, {
            "type": MessageType.INFO,
            "message": "Connected to real-time trip updates",
            "connection_id": connection_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Listen for messages
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle subscription messages
                if message.get("type") == "subscribe":
                    subscription_data = message.get("data", {})
                    websocket_manager.update_subscription(connection_id, subscription_data)
                    
                    await websocket_manager.send_message(connection_id, {
                        "type": MessageType.SUBSCRIPTION_UPDATE,
                        "message": "Subscription updated",
                        "data": websocket_manager.subscriptions[connection_id],
                        "timestamp": datetime.utcnow().isoformat()
                    })
                
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                await websocket_manager.send_message(connection_id, {
                    "type": MessageType.ERROR,
                    "message": "Invalid JSON message",
                    "timestamp": datetime.utcnow().isoformat()
                })
            except Exception as e:
                logging.error(f"WebSocket error: {e}")
                await websocket_manager.send_message(connection_id, {
                    "type": MessageType.ERROR,
                    "message": f"Internal error: {str(e)}",
                    "timestamp": datetime.utcnow().isoformat()
                })
    
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logging.error(f"WebSocket connection error: {e}")
    finally:
        websocket_manager.disconnect(connection_id)

# Background task to broadcast location updates
async def broadcast_location_updates(db: Session):
    """Background task to broadcast location updates to WebSocket subscribers"""
    while True:
        try:
            # Get recent location updates (last 30 seconds)
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
                    # Prepare location update message
                    location_message = {
                        "type": MessageType.LOCATION_UPDATE,
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
                    
                    # Broadcast to subscribers
                    await websocket_manager.broadcast_to_subscribers(
                        location_message,
                        vehicle_id=location.vehicle_id,
                        route_id=active_trip.route_id if active_trip else None
                    )
            
            # Sleep for 5 seconds before next update
            await asyncio.sleep(5)
            
        except Exception as e:
            logging.error(f"Error in location broadcast task: {e}")
            await asyncio.sleep(10)  # Wait longer on error

# API endpoints for WebSocket management
@router.get("/ws/status")
def get_websocket_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get WebSocket connection status
    
    Returns information about active WebSocket connections.
    Only admins can view WebSocket status.
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can view WebSocket status")
    
    connections = []
    for connection_id, metadata in websocket_manager.connection_metadata.items():
        subscription = websocket_manager.subscriptions.get(connection_id, {})
        connections.append({
            "connection_id": connection_id,
            "api_key_id": metadata["api_key_id"],
            "api_key_name": metadata["api_key_name"],
            "connected_at": metadata["connected_at"].isoformat(),
            "last_ping": metadata["last_ping"].isoformat(),
            "subscription": {
                "vehicle_ids": list(subscription.get("vehicle_ids", [])),
                "route_ids": list(subscription.get("route_ids", [])),
                "all_vehicles": subscription.get("all_vehicles", False),
                "all_routes": subscription.get("all_routes", False)
            }
        })
    
    return {
        "success": True,
        "data": {
            "total_connections": websocket_manager.get_connection_count(),
            "connections": connections
        },
        "message": "WebSocket status retrieved",
        "timestamp": datetime.utcnow().isoformat()
    }

@router.post("/ws/broadcast")
async def broadcast_message(
    message: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Broadcast a message to all WebSocket connections
    
    Sends a custom message to all active WebSocket connections.
    Only admins can broadcast messages.
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can broadcast messages")
    
    # Add timestamp to message
    message["timestamp"] = datetime.utcnow().isoformat()
    
    # Broadcast to all connections
    for connection_id in websocket_manager.active_connections:
        await websocket_manager.send_message(connection_id, message)
    
    return {
        "success": True,
        "data": {"connections_notified": websocket_manager.get_connection_count()},
        "message": "Message broadcasted to all connections",
        "timestamp": datetime.utcnow().isoformat()
    }

