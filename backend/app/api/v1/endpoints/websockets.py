"""
WebSocket endpoints for real-time location updates
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from ...services.websocket_manager import websocket_manager, websocket_endpoint
from ...services.location_tracking_service import location_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.websocket("/ws/realtime")
async def realtime_websocket(websocket: WebSocket):
    """WebSocket endpoint for real-time bus location updates"""
    await websocket_endpoint(websocket, "realtime")

@router.websocket("/ws/admin")
async def admin_websocket(websocket: WebSocket):
    """WebSocket endpoint for admin dashboard updates"""
    await websocket_endpoint(websocket, "admin")

@router.websocket("/ws/driver")
async def driver_websocket(websocket: WebSocket):
    """WebSocket endpoint for driver portal updates"""
    await websocket_endpoint(websocket, "driver")

@router.get("/ws/stats")
async def websocket_stats():
    """Get WebSocket connection statistics"""
    return websocket_manager.get_connection_stats()

@router.post("/ws/broadcast/test")
async def test_broadcast(message: str = "Test message"):
    """Test endpoint to broadcast a message to all realtime connections"""
    test_data = {
        "type": "test_message",
        "message": message,
        "vehicle_id": 1,
        "latitude": 12.9716,
        "longitude": 77.5946
    }
    
    await websocket_manager.broadcast_location_update(test_data)
    return {"status": "Message broadcasted", "data": test_data}