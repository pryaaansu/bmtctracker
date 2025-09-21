"""
Location Tracking Service

Handles real-time location updates, smooth interpolation, WebSocket broadcasting,
and location history management for BMTC buses.
"""

import asyncio
import json
import logging
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict
from sqlalchemy.orm import Session
from sqlalchemy import desc
import redis.asyncio as redis

from ..models.vehicle import Vehicle, VehicleStatus
from ..models.location import VehicleLocation
from ..models.route import Route
from ..core.database import get_db
from .mock_data_generator import MockDataGenerator, ScenarioType

logger = logging.getLogger(__name__)

@dataclass
class LocationUpdate:
    """Represents a location update with interpolation data"""
    vehicle_id: int
    latitude: float
    longitude: float
    speed: float
    bearing: float
    timestamp: datetime
    interpolated: bool = False
    confidence: float = 1.0

@dataclass
class WebSocketMessage:
    """WebSocket message structure"""
    type: str
    data: Dict
    timestamp: str

class LocationTrackingService:
    """Service for tracking vehicle locations and broadcasting updates"""
    
    def __init__(self, redis_client: redis.Redis = None):
        self.redis_client = redis_client
        self.mock_generator = MockDataGenerator()
        self.active_connections: Set[str] = set()
        self.location_cache: Dict[int, LocationUpdate] = {}
        self.interpolation_tasks: Dict[int, asyncio.Task] = {}
        self.cleanup_interval = 300  # 5 minutes
        self.max_location_age = 3600  # 1 hour
        self.interpolation_interval = 5  # seconds
        
    async def initialize(self):
        """Initialize the location tracking service"""
        if not self.redis_client:
            self.redis_client = redis.from_url("redis://localhost:6379")
        
        # Start background tasks
        asyncio.create_task(self._cleanup_old_locations())
        asyncio.create_task(self._generate_mock_locations())
        
        logger.info("Location tracking service initialized")
    
    async def process_location_update(self, vehicle_id: int, latitude: float, 
                                    longitude: float, speed: float, bearing: float,
                                    timestamp: datetime = None) -> LocationUpdate:
        """Process a new location update with smooth interpolation"""
        if timestamp is None:
            timestamp = datetime.now()
        
        # Create location update
        location_update = LocationUpdate(
            vehicle_id=vehicle_id,
            latitude=latitude,
            longitude=longitude,
            speed=speed,
            bearing=bearing,
            timestamp=timestamp
        )
        
        # Apply smoothing if we have previous location
        if vehicle_id in self.location_cache:
            location_update = await self._apply_smoothing(location_update)
        
        # Update cache
        self.location_cache[vehicle_id] = location_update
        
        # Store in Redis for real-time access
        await self._cache_location_update(location_update)
        
        # Store in database
        await self._store_location_update(location_update)
        
        # Broadcast to WebSocket clients
        await self._broadcast_location_update(location_update)
        
        # Process geofence notifications (async, don't wait)
        asyncio.create_task(self._process_geofence_notifications([location_update]))
        
        # Start interpolation task if not already running
        if vehicle_id not in self.interpolation_tasks:
            task = asyncio.create_task(self._interpolate_location(vehicle_id))
            self.interpolation_tasks[vehicle_id] = task
        
        return location_update
    
    async def _apply_smoothing(self, new_location: LocationUpdate) -> LocationUpdate:
        """Apply smoothing algorithm to reduce GPS noise"""
        previous = self.location_cache[new_location.vehicle_id]
        
        # Calculate time difference
        time_diff = (new_location.timestamp - previous.timestamp).total_seconds()
        
        # If update is too recent, apply more smoothing
        if time_diff < 10:  # Less than 10 seconds
            smoothing_factor = 0.3
        else:
            smoothing_factor = 0.7
        
        # Apply exponential smoothing
        new_location.latitude = (smoothing_factor * new_location.latitude + 
                               (1 - smoothing_factor) * previous.latitude)
        new_location.longitude = (smoothing_factor * new_location.longitude + 
                                (1 - smoothing_factor) * previous.longitude)
        
        # Smooth speed changes
        new_location.speed = (smoothing_factor * new_location.speed + 
                            (1 - smoothing_factor) * previous.speed)
        
        # Calculate confidence based on consistency
        distance_moved = self._calculate_distance(
            (previous.latitude, previous.longitude),
            (new_location.latitude, new_location.longitude)
        )
        
        expected_distance = previous.speed * (time_diff / 3600) * 1000  # meters
        
        if expected_distance > 0:
            confidence = min(1.0, 1.0 - abs(distance_moved - expected_distance) / expected_distance)
            new_location.confidence = max(0.1, confidence)
        
        return new_location
    
    async def _interpolate_location(self, vehicle_id: int):
        """Continuously interpolate location between updates for smooth movement"""
        try:
            while vehicle_id in self.location_cache:
                current_location = self.location_cache[vehicle_id]
                
                # Check if location is recent enough to interpolate
                age = (datetime.now() - current_location.timestamp).total_seconds()
                if age > 60:  # Stop interpolating if location is older than 1 minute
                    break
                
                # Generate interpolated position based on speed and bearing
                if current_location.speed > 0:
                    interpolated = await self._generate_interpolated_position(current_location)
                    
                    # Broadcast interpolated position
                    await self._broadcast_location_update(interpolated)
                
                await asyncio.sleep(self.interpolation_interval)
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error in location interpolation for vehicle {vehicle_id}: {e}")
        finally:
            # Clean up task reference
            if vehicle_id in self.interpolation_tasks:
                del self.interpolation_tasks[vehicle_id]
    
    async def _generate_interpolated_position(self, location: LocationUpdate) -> LocationUpdate:
        """Generate interpolated position based on current speed and bearing"""
        # Calculate how far the vehicle should have moved since last update
        time_since_update = (datetime.now() - location.timestamp).total_seconds()
        distance_meters = location.speed * (time_since_update / 3600) * 1000
        
        # Convert bearing to radians
        bearing_rad = math.radians(location.bearing)
        
        # Calculate new position using simple dead reckoning
        # This is a simplified calculation - in production you'd use more sophisticated methods
        earth_radius = 6371000  # meters
        
        lat_rad = math.radians(location.latitude)
        lng_rad = math.radians(location.longitude)
        
        new_lat_rad = math.asin(
            math.sin(lat_rad) * math.cos(distance_meters / earth_radius) +
            math.cos(lat_rad) * math.sin(distance_meters / earth_radius) * math.cos(bearing_rad)
        )
        
        new_lng_rad = lng_rad + math.atan2(
            math.sin(bearing_rad) * math.sin(distance_meters / earth_radius) * math.cos(lat_rad),
            math.cos(distance_meters / earth_radius) - math.sin(lat_rad) * math.sin(new_lat_rad)
        )
        
        return LocationUpdate(
            vehicle_id=location.vehicle_id,
            latitude=math.degrees(new_lat_rad),
            longitude=math.degrees(new_lng_rad),
            speed=location.speed,
            bearing=location.bearing,
            timestamp=datetime.now(),
            interpolated=True,
            confidence=location.confidence * 0.8  # Lower confidence for interpolated positions
        )
    
    async def _cache_location_update(self, location: LocationUpdate):
        """Cache location update in Redis"""
        if not self.redis_client:
            return
        
        try:
            cache_key = f"bus:location:{location.vehicle_id}"
            cache_data = {
                "latitude": location.latitude,
                "longitude": location.longitude,
                "speed": location.speed,
                "bearing": location.bearing,
                "timestamp": location.timestamp.isoformat(),
                "interpolated": location.interpolated,
                "confidence": location.confidence
            }
            
            # Cache for 5 minutes
            await self.redis_client.setex(cache_key, 300, json.dumps(cache_data))
            
        except Exception as e:
            logger.error(f"Error caching location update: {e}")
    
    async def _store_location_update(self, location: LocationUpdate):
        """Store location update in database"""
        try:
            # Only store non-interpolated locations in database to avoid clutter
            if not location.interpolated:
                db = next(get_db())
                try:
                    db_location = VehicleLocation(
                        vehicle_id=location.vehicle_id,
                        latitude=location.latitude,
                        longitude=location.longitude,
                        speed=location.speed,
                        bearing=location.bearing,
                        recorded_at=location.timestamp
                    )
                    db.add(db_location)
                    db.commit()
                finally:
                    db.close()
                    
        except Exception as e:
            logger.error(f"Error storing location update: {e}")
    
    async def _broadcast_location_update(self, location: LocationUpdate):
        """Broadcast location update to WebSocket clients"""
        if not self.active_connections:
            return
        
        try:
            message = WebSocketMessage(
                type="location_update",
                data=asdict(location),
                timestamp=datetime.now().isoformat()
            )
            
            # In a real implementation, you'd use a WebSocket manager
            # For now, we'll just log the broadcast
            logger.debug(f"Broadcasting location update for vehicle {location.vehicle_id}")
            
            # Store in Redis pub/sub for WebSocket servers to pick up
            if self.redis_client:
                await self.redis_client.publish(
                    "location_updates", 
                    json.dumps(asdict(message))
                )
                
        except Exception as e:
            logger.error(f"Error broadcasting location update: {e}")
    
    async def _generate_mock_locations(self):
        """Generate mock location updates for demo purposes"""
        try:
            while True:
                # Get active vehicles from database
                db = next(get_db())
                try:
                    active_vehicles = db.query(Vehicle).filter(
                        Vehicle.status == VehicleStatus.ACTIVE
                    ).limit(20).all()  # Limit to 20 for demo
                    
                    routes = db.query(Route).filter(Route.is_active == True).all()
                    
                    for i, vehicle in enumerate(active_vehicles):
                        if i < len(routes):
                            route = routes[i % len(routes)]
                            try:
                                # Generate location using mock generator
                                location_data = self.mock_generator.generate_bus_movements(
                                    route.route_number,
                                    vehicle.id
                                )
                                
                                # Process the location update
                                await self.process_location_update(
                                    vehicle_id=vehicle.id,
                                    latitude=location_data["latitude"],
                                    longitude=location_data["longitude"],
                                    speed=location_data["speed"],
                                    bearing=location_data["bearing"]
                                )
                                
                            except Exception as e:
                                logger.warning(f"Error generating mock location for vehicle {vehicle.id}: {e}")
                
                finally:
                    db.close()
                
                # Wait before next update cycle
                await asyncio.sleep(30)  # Update every 30 seconds
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error in mock location generation: {e}")
    
    async def _cleanup_old_locations(self):
        """Clean up old location data"""
        try:
            while True:
                await asyncio.sleep(self.cleanup_interval)
                
                # Clean up memory cache
                current_time = datetime.now()
                expired_vehicles = []
                
                for vehicle_id, location in self.location_cache.items():
                    age = (current_time - location.timestamp).total_seconds()
                    if age > self.max_location_age:
                        expired_vehicles.append(vehicle_id)
                
                for vehicle_id in expired_vehicles:
                    del self.location_cache[vehicle_id]
                    
                    # Cancel interpolation task
                    if vehicle_id in self.interpolation_tasks:
                        self.interpolation_tasks[vehicle_id].cancel()
                        del self.interpolation_tasks[vehicle_id]
                
                # Clean up database (keep only last 24 hours)
                db = next(get_db())
                try:
                    cutoff_time = current_time - timedelta(hours=24)
                    deleted_count = db.query(VehicleLocation).filter(
                        VehicleLocation.recorded_at < cutoff_time
                    ).delete()
                    db.commit()
                    
                    if deleted_count > 0:
                        logger.info(f"Cleaned up {deleted_count} old location records")
                        
                finally:
                    db.close()
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error in location cleanup: {e}")
    
    def _calculate_distance(self, coord1: tuple, coord2: tuple) -> float:
        """Calculate distance between two coordinates in meters"""
        import math
        
        R = 6371000  # Earth's radius in meters
        lat1, lon1 = math.radians(coord1[0]), math.radians(coord1[1])
        lat2, lon2 = math.radians(coord2[0]), math.radians(coord2[1])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c
    
    async def get_vehicle_location(self, vehicle_id: int) -> Optional[LocationUpdate]:
        """Get current location for a vehicle"""
        # Try cache first
        if vehicle_id in self.location_cache:
            return self.location_cache[vehicle_id]
        
        # Try Redis cache
        if self.redis_client:
            try:
                cache_key = f"bus:location:{vehicle_id}"
                cached_data = await self.redis_client.get(cache_key)
                if cached_data:
                    data = json.loads(cached_data)
                    return LocationUpdate(
                        vehicle_id=vehicle_id,
                        latitude=data["latitude"],
                        longitude=data["longitude"],
                        speed=data["speed"],
                        bearing=data["bearing"],
                        timestamp=datetime.fromisoformat(data["timestamp"]),
                        interpolated=data.get("interpolated", False),
                        confidence=data.get("confidence", 1.0)
                    )
            except Exception as e:
                logger.error(f"Error reading from Redis cache: {e}")
        
        # Fall back to database
        db = next(get_db())
        try:
            db_location = db.query(VehicleLocation).filter(
                VehicleLocation.vehicle_id == vehicle_id
            ).order_by(desc(VehicleLocation.recorded_at)).first()
            
            if db_location:
                return LocationUpdate(
                    vehicle_id=vehicle_id,
                    latitude=float(db_location.latitude),
                    longitude=float(db_location.longitude),
                    speed=float(db_location.speed),
                    bearing=db_location.bearing,
                    timestamp=db_location.recorded_at,
                    interpolated=False,
                    confidence=1.0
                )
        finally:
            db.close()
        
        return None
    
    async def _process_geofence_notifications(self, location_updates: List[LocationUpdate]):
        """Process geofence notifications for location updates"""
        try:
            # Import here to avoid circular imports
            from .geofence_service import geofence_service
            from .notification_engine import notification_engine
            
            # Convert location updates to format expected by geofence service
            vehicle_locations = []
            for location in location_updates:
                vehicle_locations.append({
                    'vehicle_id': location.vehicle_id,
                    'latitude': location.latitude,
                    'longitude': location.longitude,
                    'speed': location.speed,
                    'bearing': location.bearing,
                    'timestamp': location.timestamp
                })
            
            # Process geofence events and get notifications to send
            notifications_to_send = await geofence_service.process_vehicle_locations(vehicle_locations)
            
            # Send notifications via notification engine
            for notification_data in notifications_to_send:
                try:
                    await notification_engine.send_notification(
                        phone=notification_data['phone'],
                        message=notification_data['message'],
                        channel=notification_data['channel'],
                        subscription_id=notification_data.get('subscription_id'),
                        priority=notification_data.get('priority', 0),
                        metadata=notification_data.get('metadata', {})
                    )
                except Exception as e:
                    logger.error(f"Failed to send geofence notification: {str(e)}")
            
            if notifications_to_send:
                logger.info(f"Sent {len(notifications_to_send)} geofence notifications")
                
        except Exception as e:
            logger.error(f"Error processing geofence notifications: {str(e)}")
    
    async def get_all_active_locations(self) -> List[LocationUpdate]:
        """Get all active vehicle locations"""
        locations = []
        
        # Get from cache first
        for location in self.location_cache.values():
            age = (datetime.now() - location.timestamp).total_seconds()
            if age < 300:  # Only include locations less than 5 minutes old
                locations.append(location)
        
        return locations
    
    def add_websocket_connection(self, connection_id: str):
        """Add a WebSocket connection"""
        self.active_connections.add(connection_id)
        logger.info(f"Added WebSocket connection: {connection_id}")
    
    def remove_websocket_connection(self, connection_id: str):
        """Remove a WebSocket connection"""
        self.active_connections.discard(connection_id)
        logger.info(f"Removed WebSocket connection: {connection_id}")
    
    async def set_vehicle_scenario(self, vehicle_id: int, scenario: str):
        """Set scenario for a specific vehicle (for demo purposes)"""
        try:
            scenario_enum = ScenarioType(scenario)
            self.mock_generator.set_bus_scenario(vehicle_id, scenario_enum)
            logger.info(f"Set scenario {scenario} for vehicle {vehicle_id}")
        except ValueError:
            logger.error(f"Invalid scenario: {scenario}")
    
    async def simulate_rush_hour(self, enable: bool = True):
        """Enable/disable rush hour simulation"""
        self.mock_generator.simulate_rush_hour(enable)
        logger.info(f"Rush hour simulation {'enabled' if enable else 'disabled'}")

# Global instance
location_service = LocationTrackingService()