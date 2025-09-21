"""
Geofence calculation engine for proximity-based notifications
"""
import math
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..repositories.subscription import SubscriptionRepository
from ..repositories.stop import StopRepository
from ..repositories.vehicle import VehicleRepository
from ..models.subscription import Subscription, NotificationChannel
from ..models.stop import Stop
from ..models.vehicle import Vehicle

logger = logging.getLogger(__name__)

@dataclass
class GeofenceEvent:
    """Represents a geofence event"""
    vehicle_id: int
    stop_id: int
    distance_meters: float
    eta_minutes: int
    event_type: str  # 'entering', 'within', 'exiting'
    timestamp: datetime
    confidence: float  # 0.0 to 1.0

@dataclass
class ProximityRule:
    """Defines proximity-based notification rules"""
    stop_id: int
    radius_meters: float
    eta_threshold_minutes: int
    notification_channels: List[NotificationChannel]
    active: bool = True

class GeofenceCalculator:
    """Handles geofence calculations and proximity detection"""
    
    @staticmethod
    def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate the great circle distance between two points on Earth
        Returns distance in meters
        """
        # Convert latitude and longitude from degrees to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Radius of Earth in meters
        r = 6371000
        
        return c * r
    
    @staticmethod
    def calculate_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate the bearing between two points
        Returns bearing in degrees (0-360)
        """
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        dlon = lon2 - lon1
        
        y = math.sin(dlon) * math.cos(lat2)
        x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
        
        bearing = math.atan2(y, x)
        bearing = math.degrees(bearing)
        bearing = (bearing + 360) % 360
        
        return bearing
    
    @staticmethod
    def is_approaching(vehicle_lat: float, vehicle_lon: float, vehicle_bearing: float,
                      stop_lat: float, stop_lon: float, tolerance_degrees: float = 45) -> bool:
        """
        Determine if vehicle is approaching the stop based on bearing
        """
        bearing_to_stop = GeofenceCalculator.calculate_bearing(
            vehicle_lat, vehicle_lon, stop_lat, stop_lon
        )
        
        # Calculate the difference between vehicle bearing and bearing to stop
        bearing_diff = abs(vehicle_bearing - bearing_to_stop)
        if bearing_diff > 180:
            bearing_diff = 360 - bearing_diff
        
        return bearing_diff <= tolerance_degrees
    
    @staticmethod
    def calculate_eta_from_distance(distance_meters: float, speed_kmh: float) -> int:
        """
        Calculate ETA in minutes based on distance and speed
        """
        if speed_kmh <= 0:
            speed_kmh = 20  # Default speed assumption
        
        # Convert speed to m/s
        speed_ms = speed_kmh * 1000 / 3600
        
        # Calculate time in seconds
        time_seconds = distance_meters / speed_ms
        
        # Convert to minutes and round up
        eta_minutes = math.ceil(time_seconds / 60)
        
        return max(1, eta_minutes)  # Minimum 1 minute
    
    def check_geofence_events(self, vehicle_locations: List[Dict[str, Any]], 
                            stops: List[Stop]) -> List[GeofenceEvent]:
        """
        Check for geofence events based on vehicle locations and stops
        """
        events = []
        
        for location in vehicle_locations:
            vehicle_id = location['vehicle_id']
            vehicle_lat = location['latitude']
            vehicle_lon = location['longitude']
            vehicle_speed = location.get('speed', 20)  # km/h
            vehicle_bearing = location.get('bearing', 0)
            timestamp = location.get('timestamp', datetime.now())
            
            for stop in stops:
                distance = self.haversine_distance(
                    vehicle_lat, vehicle_lon,
                    float(stop.latitude), float(stop.longitude)
                )
                
                # Check different proximity zones
                if distance <= 50:  # Very close - 50m
                    event_type = 'within'
                    confidence = 0.95
                elif distance <= 200:  # Close - 200m
                    # Check if approaching
                    if self.is_approaching(vehicle_lat, vehicle_lon, vehicle_bearing,
                                         float(stop.latitude), float(stop.longitude)):
                        event_type = 'entering'
                        confidence = 0.85
                    else:
                        continue  # Not approaching, skip
                elif distance <= 500:  # Nearby - 500m
                    # Only trigger if clearly approaching
                    if self.is_approaching(vehicle_lat, vehicle_lon, vehicle_bearing,
                                         float(stop.latitude), float(stop.longitude), tolerance_degrees=30):
                        event_type = 'entering'
                        confidence = 0.70
                    else:
                        continue
                else:
                    continue  # Too far away
                
                # Calculate ETA
                eta_minutes = self.calculate_eta_from_distance(distance, vehicle_speed)
                
                event = GeofenceEvent(
                    vehicle_id=vehicle_id,
                    stop_id=stop.id,
                    distance_meters=distance,
                    eta_minutes=eta_minutes,
                    event_type=event_type,
                    timestamp=timestamp,
                    confidence=confidence
                )
                
                events.append(event)
        
        return events

class NotificationTriggerEngine:
    """Handles notification trigger evaluation and scheduling"""
    
    def __init__(self):
        self.geofence_calculator = GeofenceCalculator()
        self.active_triggers = {}  # Track active triggers to avoid duplicates
        self.trigger_history = {}  # Track trigger history for rate limiting
    
    def evaluate_triggers(self, geofence_events: List[GeofenceEvent], 
                         db: Session) -> List[Dict[str, Any]]:
        """
        Evaluate geofence events against subscription triggers
        Returns list of notifications to send
        """
        notifications_to_send = []
        
        subscription_repo = SubscriptionRepository(db)
        
        for event in geofence_events:
            # Get active subscriptions for this stop
            subscriptions = subscription_repo.get_subscriptions_for_notification(
                event.stop_id, event.eta_minutes
            )
            
            for subscription in subscriptions:
                # Check if we should trigger notification
                if self._should_trigger_notification(event, subscription):
                    notification_data = self._create_notification_data(event, subscription, db)
                    if notification_data:
                        notifications_to_send.append(notification_data)
                        
                        # Track this trigger to avoid duplicates
                        trigger_key = f"{subscription.id}_{event.vehicle_id}_{event.stop_id}"
                        self.active_triggers[trigger_key] = datetime.now()
        
        return notifications_to_send
    
    def _should_trigger_notification(self, event: GeofenceEvent, 
                                   subscription: Subscription) -> bool:
        """
        Determine if a notification should be triggered
        """
        # Check ETA threshold
        if event.eta_minutes > subscription.eta_threshold:
            return False
        
        # Check confidence threshold
        if event.confidence < 0.6:
            return False
        
        # Check for duplicate triggers (rate limiting)
        trigger_key = f"{subscription.id}_{event.vehicle_id}_{event.stop_id}"
        
        if trigger_key in self.active_triggers:
            last_trigger = self.active_triggers[trigger_key]
            # Don't trigger again within 5 minutes
            if datetime.now() - last_trigger < timedelta(minutes=5):
                return False
        
        # Check trigger history for rate limiting per subscription
        history_key = f"sub_{subscription.id}"
        if history_key in self.trigger_history:
            recent_triggers = [
                t for t in self.trigger_history[history_key]
                if datetime.now() - t < timedelta(hours=1)
            ]
            # Limit to 10 notifications per hour per subscription
            if len(recent_triggers) >= 10:
                return False
        
        return True
    
    def _create_notification_data(self, event: GeofenceEvent, 
                                subscription: Subscription, db: Session) -> Optional[Dict[str, Any]]:
        """
        Create notification data for the event and subscription
        """
        try:
            # Get vehicle and stop information
            vehicle_repo = VehicleRepository(db)
            stop_repo = StopRepository(db)
            
            vehicle = vehicle_repo.get(event.vehicle_id)
            stop = stop_repo.get_with_route_info(event.stop_id)
            
            if not vehicle or not stop:
                return None
            
            # Create message based on language preference and channel
            message = self._create_notification_message(
                event, vehicle, stop, subscription.channel
            )
            
            notification_data = {
                'phone': subscription.phone,
                'message': message,
                'channel': subscription.channel,
                'subscription_id': subscription.id,
                'priority': 1 if event.eta_minutes <= 2 else 0,  # High priority for imminent arrivals
                'metadata': {
                    'event_type': event.event_type,
                    'vehicle_id': event.vehicle_id,
                    'stop_id': event.stop_id,
                    'distance_meters': event.distance_meters,
                    'eta_minutes': event.eta_minutes,
                    'confidence': event.confidence,
                    'vehicle_number': vehicle.vehicle_number,
                    'route_number': stop.get('route', {}).get('route_number', 'Unknown')
                }
            }
            
            # Track trigger history
            history_key = f"sub_{subscription.id}"
            if history_key not in self.trigger_history:
                self.trigger_history[history_key] = []
            self.trigger_history[history_key].append(datetime.now())
            
            return notification_data
            
        except Exception as e:
            logger.error(f"Failed to create notification data: {str(e)}")
            return None
    
    def _create_notification_message(self, event: GeofenceEvent, vehicle: Vehicle,
                                   stop: Dict[str, Any], channel: NotificationChannel) -> str:
        """
        Create notification message based on event and channel
        """
        vehicle_number = vehicle.vehicle_number
        stop_name = stop.get('name', 'Unknown Stop')
        stop_name_kn = stop.get('name_kannada', '')
        route_info = stop.get('route', {})
        route_number = route_info.get('route_number', 'Unknown')
        eta_minutes = event.eta_minutes
        
        if channel == NotificationChannel.SMS:
            # SMS message (English + Kannada)
            message = f"🚌 Bus {vehicle_number} (Route {route_number}) arriving at {stop_name}"
            if stop_name_kn:
                message += f" / {stop_name_kn}"
            message += f" in {eta_minutes} min"
            if eta_minutes <= 2:
                message += " - Hurry! 🏃‍♂️"
            return message
            
        elif channel == NotificationChannel.VOICE:
            # Voice message (simpler for TTS)
            message = f"Bus {vehicle_number} on route {route_number} is arriving at {stop_name} in {eta_minutes} minutes"
            return message
            
        elif channel == NotificationChannel.WHATSAPP:
            # WhatsApp message (richer formatting)
            message = f"🚌 *Bus Alert*\n\n"
            message += f"Bus: *{vehicle_number}*\n"
            message += f"Route: *{route_number}*\n"
            message += f"Stop: *{stop_name}*"
            if stop_name_kn:
                message += f" ({stop_name_kn})"
            message += f"\nETA: *{eta_minutes} minutes*"
            if eta_minutes <= 2:
                message += "\n\n⚡ *Arriving soon - Please be ready!*"
            return message
            
        else:
            # Default message
            return f"Bus {vehicle_number} arriving at {stop_name} in {eta_minutes} minutes"
    
    def cleanup_old_triggers(self):
        """
        Clean up old trigger records to prevent memory leaks
        """
        current_time = datetime.now()
        
        # Clean up active triggers older than 30 minutes
        expired_triggers = [
            key for key, timestamp in self.active_triggers.items()
            if current_time - timestamp > timedelta(minutes=30)
        ]
        
        for key in expired_triggers:
            del self.active_triggers[key]
        
        # Clean up trigger history older than 24 hours
        for history_key in list(self.trigger_history.keys()):
            self.trigger_history[history_key] = [
                t for t in self.trigger_history[history_key]
                if current_time - t < timedelta(hours=24)
            ]
            
            # Remove empty history entries
            if not self.trigger_history[history_key]:
                del self.trigger_history[history_key]

class GeofenceService:
    """Main geofence service that coordinates geofence calculations and triggers"""
    
    def __init__(self):
        self.trigger_engine = NotificationTriggerEngine()
        self.last_cleanup = datetime.now()
    
    async def process_vehicle_locations(self, vehicle_locations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process vehicle locations and generate notifications
        """
        try:
            db = next(get_db())
            
            # Get all active stops
            stop_repo = StopRepository(db)
            stops = stop_repo.get_all_active()
            
            # Calculate geofence events
            geofence_events = self.trigger_engine.geofence_calculator.check_geofence_events(
                vehicle_locations, stops
            )
            
            logger.info(f"Generated {len(geofence_events)} geofence events from {len(vehicle_locations)} vehicle locations")
            
            # Evaluate triggers and generate notifications
            notifications_to_send = self.trigger_engine.evaluate_triggers(geofence_events, db)
            
            logger.info(f"Generated {len(notifications_to_send)} notifications from geofence events")
            
            # Periodic cleanup
            if datetime.now() - self.last_cleanup > timedelta(hours=1):
                self.trigger_engine.cleanup_old_triggers()
                self.last_cleanup = datetime.now()
            
            return notifications_to_send
            
        except Exception as e:
            logger.error(f"Failed to process vehicle locations: {str(e)}")
            return []
    
    def get_proximity_stats(self) -> Dict[str, Any]:
        """
        Get statistics about proximity detection
        """
        return {
            'active_triggers': len(self.trigger_engine.active_triggers),
            'trigger_history_entries': len(self.trigger_engine.trigger_history),
            'last_cleanup': self.last_cleanup.isoformat()
        }

# Global geofence service instance
geofence_service = GeofenceService()