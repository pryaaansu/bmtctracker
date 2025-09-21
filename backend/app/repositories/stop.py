"""
Stop repository with geospatial queries
"""
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, func, text
import math

from .base import BaseRepository
from ..models.stop import Stop
from ..schemas.stop import StopCreate, StopUpdate

class StopRepository(BaseRepository[Stop, StopCreate, StopUpdate]):
    """Repository for Stop model with geospatial capabilities"""
    
    def __init__(self, db: Session):
        super().__init__(Stop, db)
    
    def get_by_route(self, route_id: int) -> List[Stop]:
        """Get all stops for a route, ordered by stop_order"""
        cache_key = self._get_cache_key("route", route_id)
        
        cached_data = self._cache_get(cache_key)
        if cached_data:
            return cached_data
        
        stops = self.db.query(Stop).filter(
            Stop.route_id == route_id
        ).order_by(Stop.stop_order).all()
        
        if stops:
            data = [self._model_to_dict(stop) for stop in stops]
            self._cache_set(cache_key, data, ttl=600)  # 10 minutes TTL
        return stops
    
    def search_stops(self, query: str) -> List[Stop]:
        """Search stops by name (English or Kannada)"""
        cache_key = self._get_cache_key("search", query.lower())
        
        cached_data = self._cache_get(cache_key)
        if cached_data:
            return cached_data
        
        stops = self.db.query(Stop).filter(
            (Stop.name.ilike(f"%{query}%")) | 
            (Stop.name_kannada.ilike(f"%{query}%"))
        ).all()
        
        if stops:
            data = [self._model_to_dict(stop) for stop in stops]
            self._cache_set(cache_key, data, ttl=180)  # 3 minutes TTL
        return stops
    
    def get_nearby_stops(self, latitude: float, longitude: float, radius_km: float = 1.0) -> List[dict]:
        """Get stops within radius using Haversine formula"""
        cache_key = self._get_cache_key("nearby", f"{latitude}:{longitude}:{radius_km}")
        
        cached_data = self._cache_get(cache_key)
        if cached_data:
            return cached_data
        
        # Haversine formula for distance calculation
        # Note: For production, consider using PostGIS or similar for better performance
        haversine_formula = f"""
            (6371 * acos(
                cos(radians({latitude})) * 
                cos(radians(latitude)) * 
                cos(radians(longitude) - radians({longitude})) + 
                sin(radians({latitude})) * 
                sin(radians(latitude))
            ))
        """
        
        stops_with_distance = self.db.query(
            Stop,
            text(haversine_formula).label('distance')
        ).having(
            text(f"distance <= {radius_km}")
        ).order_by(text('distance')).all()
        
        result = []
        for stop, distance in stops_with_distance:
            stop_data = self._model_to_dict(stop)
            stop_data['distance_km'] = round(float(distance), 3)
            result.append(stop_data)
        
        if result:
            self._cache_set(cache_key, result, ttl=120)  # 2 minutes TTL
        
        return result
    
    def get_stops_with_route_info(self) -> List[dict]:
        """Get stops with their route information"""
        cache_key = self._get_cache_key("with_routes", "all")
        
        cached_data = self._cache_get(cache_key)
        if cached_data:
            return cached_data
        
        stops = self.db.query(Stop).options(joinedload(Stop.route)).all()
        
        result = []
        for stop in stops:
            stop_data = self._model_to_dict(stop)
            if stop.route:
                stop_data['route'] = {
                    'id': stop.route.id,
                    'name': stop.route.name,
                    'route_number': stop.route.route_number,
                    'is_active': stop.route.is_active
                }
            result.append(stop_data)
        
        if result:
            self._cache_set(cache_key, result, ttl=300)  # 5 minutes TTL
        
        return result
    
    def get_stop_with_subscriptions(self, stop_id: int) -> Optional[dict]:
        """Get stop with active subscription count"""
        cache_key = self._get_cache_key("with_subs", stop_id)
        
        cached_data = self._cache_get(cache_key)
        if cached_data:
            return cached_data
        
        stop = self.db.query(Stop).options(joinedload(Stop.subscriptions)).filter(
            Stop.id == stop_id
        ).first()
        
        if stop:
            stop_data = self._model_to_dict(stop)
            stop_data['active_subscriptions'] = len([
                sub for sub in stop.subscriptions if sub.is_active
            ])
            self._cache_set(cache_key, stop_data, ttl=60)  # 1 minute TTL
            return stop_data
        
        return None
    
    def get_popular_stops(self, limit: int = 10) -> List[dict]:
        """Get stops with most active subscriptions"""
        cache_key = self._get_cache_key("popular", limit)
        
        cached_data = self._cache_get(cache_key)
        if cached_data:
            return cached_data
        
        # This would be more efficient with a proper SQL query
        # For now, we'll get all stops and sort by subscription count
        stops = self.db.query(Stop).options(joinedload(Stop.subscriptions)).all()
        
        stops_with_counts = []
        for stop in stops:
            stop_data = self._model_to_dict(stop)
            active_subs = len([sub for sub in stop.subscriptions if sub.is_active])
            stop_data['subscription_count'] = active_subs
            stops_with_counts.append(stop_data)
        
        # Sort by subscription count and take top N
        result = sorted(stops_with_counts, key=lambda x: x['subscription_count'], reverse=True)[:limit]
        
        if result:
            self._cache_set(cache_key, result, ttl=300)  # 5 minutes TTL
        
        return result
    
    @staticmethod
    def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points using Haversine formula"""
        R = 6371  # Earth's radius in kilometers
        
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = (math.sin(dlat/2)**2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c