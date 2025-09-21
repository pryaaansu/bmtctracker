"""
ETA Calculation Service

Implements sophisticated ETA calculation algorithms using Haversine distance,
route-aware pathfinding, speed-based estimation, and traffic/delay factors.
"""

import asyncio
import json
import logging
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
import redis.asyncio as redis

from ..models.vehicle import Vehicle, VehicleStatus
from ..models.location import VehicleLocation
from ..models.route import Route
from ..models.stop import Stop
from ..core.database import get_db
from .location_tracking_service import LocationUpdate

logger = logging.getLogger(__name__)

@dataclass
class ETAResult:
    """ETA calculation result with confidence metrics"""
    vehicle_id: int
    stop_id: int
    eta_seconds: int
    eta_minutes: float
    confidence: float
    distance_meters: float
    average_speed_kmh: float
    traffic_factor: float
    delay_factor: float
    calculation_method: str
    calculated_at: datetime

@dataclass
class RouteSegment:
    """Represents a segment of a route between two points"""
    start_lat: float
    start_lng: float
    end_lat: float
    end_lng: float
    distance_meters: float
    expected_time_seconds: float

class ETACalculationService:
    """Service for calculating estimated time of arrival for buses"""
    
    def __init__(self, redis_client: redis.Redis = None):
        self.redis_client = redis_client
        self.historical_speeds: Dict[int, List[float]] = {}  # vehicle_id -> speeds
        self.route_segments: Dict[int, List[RouteSegment]] = {}  # route_id -> segments
        self.traffic_factors: Dict[str, float] = {}  # time_period -> factor
        self.delay_patterns: Dict[int, Dict[str, float]] = {}  # route_id -> time_period -> delay
        
        # Configuration
        self.default_speed_kmh = 25.0  # Default bus speed in Bengaluru
        self.min_speed_kmh = 5.0  # Minimum speed (heavy traffic)
        self.max_speed_kmh = 60.0  # Maximum speed (highway)
        self.confidence_decay_rate = 0.1  # How quickly confidence decreases with time
        self.historical_data_window = 7  # Days of historical data to consider
        
    async def initialize(self):
        """Initialize the ETA calculation service"""
        if not self.redis_client:
            self.redis_client = redis.from_url("redis://localhost:6379")
        
        # Load historical data and route segments
        await self._load_historical_speeds()
        await self._load_route_segments()
        await self._load_traffic_patterns()
        
        # Start background tasks
        asyncio.create_task(self._update_historical_data())
        asyncio.create_task(self._update_traffic_factors())
        
        logger.info("ETA calculation service initialized")
    
    async def calculate_eta(self, vehicle_id: int, stop_id: int, 
                          current_location: Optional[LocationUpdate] = None) -> Optional[ETAResult]:
        """
        Calculate ETA for a vehicle to reach a specific stop
        
        Args:
            vehicle_id: ID of the vehicle
            stop_id: ID of the destination stop
            current_location: Current location (if available)
            
        Returns:
            ETAResult with calculated ETA and confidence metrics
        """
        try:
            # Get current location if not provided
            if not current_location:
                from .location_tracking_service import location_service
                current_location = await location_service.get_vehicle_location(vehicle_id)
                
            if not current_location:
                logger.warning(f"No location data available for vehicle {vehicle_id}")
                return None
            
            # Get stop information
            stop = await self._get_stop_info(stop_id)
            if not stop:
                logger.warning(f"Stop {stop_id} not found")
                return None
            
            # Get route information
            route = await self._get_route_info(stop.route_id)
            if not route:
                logger.warning(f"Route {stop.route_id} not found")
                return None
            
            # Calculate using multiple methods and choose the best
            eta_results = []
            
            # Method 1: Haversine distance with current speed
            haversine_eta = await self._calculate_haversine_eta(
                current_location, stop, vehicle_id
            )
            if haversine_eta:
                eta_results.append(haversine_eta)
            
            # Method 2: Route-aware pathfinding
            route_aware_eta = await self._calculate_route_aware_eta(
                current_location, stop, route, vehicle_id
            )
            if route_aware_eta:
                eta_results.append(route_aware_eta)
            
            # Method 3: Historical speed-based estimation
            historical_eta = await self._calculate_historical_eta(
                current_location, stop, vehicle_id
            )
            if historical_eta:
                eta_results.append(historical_eta)
            
            # Choose the best result based on confidence
            if not eta_results:
                return None
            
            best_eta = max(eta_results, key=lambda x: x.confidence)
            
            # Apply traffic and delay factors
            final_eta = await self._apply_traffic_and_delay_factors(best_eta, route.id)
            
            # Cache the result
            await self._cache_eta_result(final_eta)
            
            return final_eta
            
        except Exception as e:
            logger.error(f"Error calculating ETA for vehicle {vehicle_id} to stop {stop_id}: {e}")
            return None
    
    async def _calculate_haversine_eta(self, location: LocationUpdate, stop: Stop, 
                                     vehicle_id: int) -> Optional[ETAResult]:
        """Calculate ETA using Haversine distance and current speed"""
        try:
            # Calculate straight-line distance
            distance = self._haversine_distance(
                (location.latitude, location.longitude),
                (float(stop.latitude), float(stop.longitude))
            )
            
            # Use current speed if available and reasonable
            speed_kmh = location.speed if location.speed > self.min_speed_kmh else self.default_speed_kmh
            speed_kmh = min(speed_kmh, self.max_speed_kmh)
            
            # Calculate ETA
            eta_hours = distance / 1000 / speed_kmh
            eta_seconds = int(eta_hours * 3600)
            
            # Calculate confidence based on data quality
            confidence = location.confidence * 0.7  # Lower confidence for straight-line distance
            
            # Reduce confidence if speed is very low or very high
            if location.speed < 5 or location.speed > 50:
                confidence *= 0.8
            
            return ETAResult(
                vehicle_id=vehicle_id,
                stop_id=stop.id,
                eta_seconds=eta_seconds,
                eta_minutes=eta_seconds / 60,
                confidence=confidence,
                distance_meters=distance,
                average_speed_kmh=speed_kmh,
                traffic_factor=1.0,
                delay_factor=1.0,
                calculation_method="haversine",
                calculated_at=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error in Haversine ETA calculation: {e}")
            return None
    
    async def _calculate_route_aware_eta(self, location: LocationUpdate, stop: Stop, 
                                       route: Route, vehicle_id: int) -> Optional[ETAResult]:
        """Calculate ETA using route-aware pathfinding"""
        try:
            # Get route segments
            segments = await self._get_route_segments(route.id)
            if not segments:
                return None
            
            # Find the closest point on the route to current location
            closest_segment_idx, closest_point = await self._find_closest_route_point(
                location, segments
            )
            
            # Find the segment containing the destination stop
            stop_segment_idx = await self._find_stop_segment(stop, segments)
            if stop_segment_idx is None:
                return None
            
            # Calculate distance along the route
            route_distance = 0.0
            
            # Add remaining distance in current segment
            if closest_segment_idx < len(segments):
                current_segment = segments[closest_segment_idx]
                remaining_in_segment = self._haversine_distance(
                    (closest_point[0], closest_point[1]),
                    (current_segment.end_lat, current_segment.end_lng)
                )
                route_distance += remaining_in_segment
            
            # Add distance for intermediate segments
            for i in range(closest_segment_idx + 1, stop_segment_idx):
                route_distance += segments[i].distance_meters
            
            # Add distance to stop in final segment
            if stop_segment_idx < len(segments):
                final_segment = segments[stop_segment_idx]
                distance_to_stop = self._haversine_distance(
                    (final_segment.start_lat, final_segment.start_lng),
                    (float(stop.latitude), float(stop.longitude))
                )
                route_distance += distance_to_stop
            
            # Calculate average speed from historical data
            avg_speed = await self._get_historical_speed(vehicle_id, route.id)
            
            # Calculate ETA
            eta_hours = route_distance / 1000 / avg_speed
            eta_seconds = int(eta_hours * 3600)
            
            # Higher confidence for route-aware calculation
            confidence = location.confidence * 0.9
            
            return ETAResult(
                vehicle_id=vehicle_id,
                stop_id=stop.id,
                eta_seconds=eta_seconds,
                eta_minutes=eta_seconds / 60,
                confidence=confidence,
                distance_meters=route_distance,
                average_speed_kmh=avg_speed,
                traffic_factor=1.0,
                delay_factor=1.0,
                calculation_method="route_aware",
                calculated_at=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error in route-aware ETA calculation: {e}")
            return None
    
    async def _calculate_historical_eta(self, location: LocationUpdate, stop: Stop, 
                                      vehicle_id: int) -> Optional[ETAResult]:
        """Calculate ETA using historical speed patterns"""
        try:
            # Get historical speeds for this vehicle/route/time
            historical_speeds = await self._get_historical_speeds_for_context(
                vehicle_id, stop.route_id, datetime.now()
            )
            
            if not historical_speeds:
                return None
            
            # Calculate weighted average speed
            avg_speed = sum(historical_speeds) / len(historical_speeds)
            
            # Calculate distance (using Haversine as approximation)
            distance = self._haversine_distance(
                (location.latitude, location.longitude),
                (float(stop.latitude), float(stop.longitude))
            )
            
            # Apply route factor (routes are typically 1.3-1.5x straight line distance)
            route_factor = 1.4
            adjusted_distance = distance * route_factor
            
            # Calculate ETA
            eta_hours = adjusted_distance / 1000 / avg_speed
            eta_seconds = int(eta_hours * 3600)
            
            # Confidence based on amount of historical data
            confidence = min(0.95, len(historical_speeds) / 10) * location.confidence
            
            return ETAResult(
                vehicle_id=vehicle_id,
                stop_id=stop.id,
                eta_seconds=eta_seconds,
                eta_minutes=eta_seconds / 60,
                confidence=confidence,
                distance_meters=adjusted_distance,
                average_speed_kmh=avg_speed,
                traffic_factor=1.0,
                delay_factor=1.0,
                calculation_method="historical",
                calculated_at=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error in historical ETA calculation: {e}")
            return None
    
    async def _apply_traffic_and_delay_factors(self, eta_result: ETAResult, 
                                             route_id: int) -> ETAResult:
        """Apply traffic and delay factors to improve ETA accuracy"""
        try:
            # Get current time period for traffic factor
            current_hour = datetime.now().hour
            time_period = self._get_time_period(current_hour)
            
            # Get traffic factor
            traffic_factor = self.traffic_factors.get(time_period, 1.0)
            
            # Get route-specific delay factor
            delay_factor = 1.0
            if route_id in self.delay_patterns:
                delay_factor = self.delay_patterns[route_id].get(time_period, 1.0)
            
            # Apply factors
            adjusted_eta_seconds = int(eta_result.eta_seconds * traffic_factor * delay_factor)
            
            # Update the result
            eta_result.eta_seconds = adjusted_eta_seconds
            eta_result.eta_minutes = adjusted_eta_seconds / 60
            eta_result.traffic_factor = traffic_factor
            eta_result.delay_factor = delay_factor
            
            # Adjust confidence based on how much we're modifying the original estimate
            total_factor = traffic_factor * delay_factor
            if total_factor > 1.5 or total_factor < 0.7:
                eta_result.confidence *= 0.9  # Lower confidence for large adjustments
            
            return eta_result
            
        except Exception as e:
            logger.error(f"Error applying traffic and delay factors: {e}")
            return eta_result
    
    def _haversine_distance(self, coord1: Tuple[float, float], 
                           coord2: Tuple[float, float]) -> float:
        """Calculate Haversine distance between two coordinates in meters"""
        R = 6371000  # Earth's radius in meters
        lat1, lon1 = math.radians(coord1[0]), math.radians(coord1[1])
        lat2, lon2 = math.radians(coord2[0]), math.radians(coord2[1])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c
    
    def _get_time_period(self, hour: int) -> str:
        """Get time period for traffic/delay factors"""
        if 7 <= hour <= 10:
            return "morning_rush"
        elif 17 <= hour <= 20:
            return "evening_rush"
        elif 10 <= hour <= 17:
            return "daytime"
        else:
            return "off_peak"
    
    async def _get_stop_info(self, stop_id: int) -> Optional[Stop]:
        """Get stop information from database"""
        db = next(get_db())
        try:
            return db.query(Stop).filter(Stop.id == stop_id).first()
        finally:
            db.close()
    
    async def _get_route_info(self, route_id: int) -> Optional[Route]:
        """Get route information from database"""
        db = next(get_db())
        try:
            return db.query(Route).filter(Route.id == route_id).first()
        finally:
            db.close()
    
    async def _get_route_segments(self, route_id: int) -> List[RouteSegment]:
        """Get or generate route segments for pathfinding"""
        if route_id in self.route_segments:
            return self.route_segments[route_id]
        
        # Generate segments from route data
        db = next(get_db())
        try:
            route = db.query(Route).filter(Route.id == route_id).first()
            if not route:
                return []
            
            # Parse GeoJSON to extract coordinates
            try:
                import json
                geojson_data = json.loads(route.geojson)
                coordinates = geojson_data.get("coordinates", [])
                
                segments = []
                for i in range(len(coordinates) - 1):
                    start_coord = coordinates[i]
                    end_coord = coordinates[i + 1]
                    
                    distance = self._haversine_distance(
                        (start_coord[1], start_coord[0]),  # lat, lng
                        (end_coord[1], end_coord[0])
                    )
                    
                    # Estimate time based on average speed
                    expected_time = distance / 1000 / self.default_speed_kmh * 3600
                    
                    segment = RouteSegment(
                        start_lat=start_coord[1],
                        start_lng=start_coord[0],
                        end_lat=end_coord[1],
                        end_lng=end_coord[0],
                        distance_meters=distance,
                        expected_time_seconds=expected_time
                    )
                    segments.append(segment)
                
                self.route_segments[route_id] = segments
                return segments
                
            except (json.JSONDecodeError, KeyError) as e:
                logger.error(f"Error parsing route GeoJSON for route {route_id}: {e}")
                return []
                
        finally:
            db.close()
    
    async def _find_closest_route_point(self, location: LocationUpdate, 
                                      segments: List[RouteSegment]) -> Tuple[int, Tuple[float, float]]:
        """Find the closest point on the route to current location"""
        min_distance = float('inf')
        closest_segment_idx = 0
        closest_point = (location.latitude, location.longitude)
        
        for i, segment in enumerate(segments):
            # Check distance to start point
            start_distance = self._haversine_distance(
                (location.latitude, location.longitude),
                (segment.start_lat, segment.start_lng)
            )
            
            if start_distance < min_distance:
                min_distance = start_distance
                closest_segment_idx = i
                closest_point = (segment.start_lat, segment.start_lng)
            
            # Check distance to end point
            end_distance = self._haversine_distance(
                (location.latitude, location.longitude),
                (segment.end_lat, segment.end_lng)
            )
            
            if end_distance < min_distance:
                min_distance = end_distance
                closest_segment_idx = i
                closest_point = (segment.end_lat, segment.end_lng)
        
        return closest_segment_idx, closest_point
    
    async def _find_stop_segment(self, stop: Stop, segments: List[RouteSegment]) -> Optional[int]:
        """Find which segment contains the stop"""
        min_distance = float('inf')
        best_segment_idx = None
        
        for i, segment in enumerate(segments):
            # Calculate distance from stop to segment
            segment_distance = min(
                self._haversine_distance(
                    (float(stop.latitude), float(stop.longitude)),
                    (segment.start_lat, segment.start_lng)
                ),
                self._haversine_distance(
                    (float(stop.latitude), float(stop.longitude)),
                    (segment.end_lat, segment.end_lng)
                )
            )
            
            if segment_distance < min_distance:
                min_distance = segment_distance
                best_segment_idx = i
        
        return best_segment_idx
    
    async def _get_historical_speed(self, vehicle_id: int, route_id: int) -> float:
        """Get historical average speed for vehicle/route"""
        if vehicle_id in self.historical_speeds and self.historical_speeds[vehicle_id]:
            return sum(self.historical_speeds[vehicle_id]) / len(self.historical_speeds[vehicle_id])
        
        # Fallback to route-based historical data
        db = next(get_db())
        try:
            # Get recent speed data for this route
            cutoff_time = datetime.now() - timedelta(days=self.historical_data_window)
            
            speeds = db.query(VehicleLocation.speed).join(Vehicle).join(
                # This would need a proper join through trips table
                # For now, use a simplified approach
            ).filter(
                VehicleLocation.recorded_at >= cutoff_time,
                VehicleLocation.speed > 0
            ).limit(100).all()
            
            if speeds:
                avg_speed = sum(speed[0] for speed in speeds) / len(speeds)
                return max(self.min_speed_kmh, min(avg_speed, self.max_speed_kmh))
            
        except Exception as e:
            logger.error(f"Error getting historical speed: {e}")
        finally:
            db.close()
        
        return self.default_speed_kmh
    
    async def _get_historical_speeds_for_context(self, vehicle_id: int, route_id: int, 
                                               timestamp: datetime) -> List[float]:
        """Get historical speeds for similar context (time, route, etc.)"""
        # This would implement more sophisticated historical analysis
        # For now, return cached speeds if available
        if vehicle_id in self.historical_speeds:
            return self.historical_speeds[vehicle_id][-10:]  # Last 10 speeds
        
        return []
    
    async def _cache_eta_result(self, eta_result: ETAResult):
        """Cache ETA result in Redis"""
        if not self.redis_client:
            return
        
        try:
            cache_key = f"eta:{eta_result.vehicle_id}:{eta_result.stop_id}"
            cache_data = asdict(eta_result)
            cache_data["calculated_at"] = eta_result.calculated_at.isoformat()
            
            # Cache for 2 minutes
            await self.redis_client.setex(cache_key, 120, json.dumps(cache_data))
            
        except Exception as e:
            logger.error(f"Error caching ETA result: {e}")
    
    async def get_cached_eta(self, vehicle_id: int, stop_id: int) -> Optional[ETAResult]:
        """Get cached ETA result"""
        if not self.redis_client:
            return None
        
        try:
            cache_key = f"eta:{vehicle_id}:{stop_id}"
            cached_data = await self.redis_client.get(cache_key)
            
            if cached_data:
                data = json.loads(cached_data)
                data["calculated_at"] = datetime.fromisoformat(data["calculated_at"])
                return ETAResult(**data)
                
        except Exception as e:
            logger.error(f"Error reading cached ETA: {e}")
        
        return None
    
    async def _load_historical_speeds(self):
        """Load historical speed data"""
        try:
            db = next(get_db())
            try:
                # Load recent speed data for active vehicles
                cutoff_time = datetime.now() - timedelta(days=self.historical_data_window)
                
                speed_data = db.query(
                    VehicleLocation.vehicle_id,
                    VehicleLocation.speed
                ).filter(
                    VehicleLocation.recorded_at >= cutoff_time,
                    VehicleLocation.speed > 0
                ).all()
                
                # Group by vehicle
                for vehicle_id, speed in speed_data:
                    if vehicle_id not in self.historical_speeds:
                        self.historical_speeds[vehicle_id] = []
                    self.historical_speeds[vehicle_id].append(float(speed))
                
                logger.info(f"Loaded historical speeds for {len(self.historical_speeds)} vehicles")
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error loading historical speeds: {e}")
    
    async def _load_route_segments(self):
        """Load and cache route segments"""
        try:
            db = next(get_db())
            try:
                routes = db.query(Route).filter(Route.is_active == True).all()
                
                for route in routes:
                    await self._get_route_segments(route.id)
                
                logger.info(f"Loaded route segments for {len(self.route_segments)} routes")
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error loading route segments: {e}")
    
    async def _load_traffic_patterns(self):
        """Load traffic and delay patterns"""
        # Initialize with default traffic factors for Bengaluru
        self.traffic_factors = {
            "morning_rush": 1.5,  # 50% slower during morning rush
            "evening_rush": 1.6,  # 60% slower during evening rush
            "daytime": 1.2,       # 20% slower during daytime
            "off_peak": 1.0       # Normal speed during off-peak
        }
        
        # Initialize delay patterns (would be loaded from historical data)
        # For now, use default patterns
        self.delay_patterns = {}
        
        logger.info("Loaded traffic and delay patterns")
    
    async def _update_historical_data(self):
        """Background task to update historical data"""
        try:
            while True:
                await asyncio.sleep(3600)  # Update every hour
                await self._load_historical_speeds()
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error updating historical data: {e}")
    
    async def _update_traffic_factors(self):
        """Background task to update traffic factors"""
        try:
            while True:
                await asyncio.sleep(1800)  # Update every 30 minutes
                
                # This would analyze recent speed data to update traffic factors
                # For now, keep static factors
                
                await asyncio.sleep(1800)
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error updating traffic factors: {e}")

# Global instance
eta_service = ETACalculationService()