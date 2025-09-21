"""
Vehicle location repository with real-time tracking
"""
from typing import List, Optional, Dict
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, desc, func
from datetime import datetime, timedelta

from .base import BaseRepository
from ..models.location import VehicleLocation
from ..models.vehicle import Vehicle

class VehicleLocationRepository(BaseRepository[VehicleLocation, dict, dict]):
    """Repository for VehicleLocation model with real-time capabilities"""
    
    def __init__(self, db: Session):
        super().__init__(VehicleLocation, db)
        self._cache_ttl = 30  # Short TTL for real-time data
    
    def get_latest_by_vehicle(self, vehicle_id: int) -> Optional[VehicleLocation]:
        """Get the most recent location for a vehicle"""
        cache_key = self._get_cache_key("latest", vehicle_id)
        
        cached_data = self._cache_get(cache_key)
        if cached_data:
            return cached_data
        
        location = self.db.query(VehicleLocation).filter(
            VehicleLocation.vehicle_id == vehicle_id
        ).order_by(desc(VehicleLocation.recorded_at)).first()
        
        if location:
            self._cache_set(cache_key, self._model_to_dict(location), ttl=30)  # 30 seconds TTL
        return location
    
    def get_vehicle_history(self, vehicle_id: int, hours: int = 24) -> List[VehicleLocation]:
        """Get location history for a vehicle"""
        cache_key = self._get_cache_key("history", f"{vehicle_id}:{hours}")
        
        cached_data = self._cache_get(cache_key)
        if cached_data:
            return cached_data
        
        since = datetime.now() - timedelta(hours=hours)
        locations = self.db.query(VehicleLocation).filter(
            and_(
                VehicleLocation.vehicle_id == vehicle_id,
                VehicleLocation.recorded_at >= since
            )
        ).order_by(VehicleLocation.recorded_at).all()
        
        if locations:
            data = [self._model_to_dict(location) for location in locations]
            self._cache_set(cache_key, data, ttl=300)  # 5 minutes TTL
        return locations
    
    def get_all_latest_locations(self) -> List[Dict]:
        """Get latest location for all vehicles"""
        cache_key = self._get_cache_key("all_latest", "vehicles")
        
        cached_data = self._cache_get(cache_key)
        if cached_data:
            return cached_data
        
        # Subquery to get latest recorded_at for each vehicle
        latest_times = self.db.query(
            VehicleLocation.vehicle_id,
            func.max(VehicleLocation.recorded_at).label('latest_time')
        ).group_by(VehicleLocation.vehicle_id).subquery()
        
        # Join to get full location records
        locations = self.db.query(VehicleLocation).join(
            latest_times,
            and_(
                VehicleLocation.vehicle_id == latest_times.c.vehicle_id,
                VehicleLocation.recorded_at == latest_times.c.latest_time
            )
        ).options(joinedload(VehicleLocation.vehicle)).all()
        
        result = []
        for location in locations:
            location_data = self._model_to_dict(location)
            if location.vehicle:
                location_data['vehicle'] = {
                    'id': location.vehicle.id,
                    'vehicle_number': location.vehicle.vehicle_number,
                    'capacity': location.vehicle.capacity,
                    'status': location.vehicle.status.value
                }
            result.append(location_data)
        
        if result:
            self._cache_set(cache_key, result, ttl=30)  # 30 seconds TTL
        return result
    
    def add_location_update(self, vehicle_id: int, latitude: float, longitude: float,
                          speed: float = 0, bearing: int = 0) -> VehicleLocation:
        """Add a new location update for a vehicle"""
        location = VehicleLocation(
            vehicle_id=vehicle_id,
            latitude=latitude,
            longitude=longitude,
            speed=speed,
            bearing=bearing,
            recorded_at=datetime.now()
        )
        
        self.db.add(location)
        self.db.commit()
        self.db.refresh(location)
        
        # Invalidate cache for this vehicle
        self._cache_delete(self._get_cache_key("latest", vehicle_id))
        self._cache_delete(self._get_cache_key("all_latest", "vehicles"))
        
        return location
    
    def get_locations_in_area(self, min_lat: float, max_lat: float,
                            min_lng: float, max_lng: float,
                            max_age_minutes: int = 10) -> List[Dict]:
        """Get recent locations within a geographic area"""
        cache_key = self._get_cache_key("area", f"{min_lat}:{max_lat}:{min_lng}:{max_lng}:{max_age_minutes}")
        
        cached_data = self._cache_get(cache_key)
        if cached_data:
            return cached_data
        
        since = datetime.now() - timedelta(minutes=max_age_minutes)
        
        # Get latest location for each vehicle in the area
        latest_times = self.db.query(
            VehicleLocation.vehicle_id,
            func.max(VehicleLocation.recorded_at).label('latest_time')
        ).filter(
            and_(
                VehicleLocation.latitude.between(min_lat, max_lat),
                VehicleLocation.longitude.between(min_lng, max_lng),
                VehicleLocation.recorded_at >= since
            )
        ).group_by(VehicleLocation.vehicle_id).subquery()
        
        locations = self.db.query(VehicleLocation).join(
            latest_times,
            and_(
                VehicleLocation.vehicle_id == latest_times.c.vehicle_id,
                VehicleLocation.recorded_at == latest_times.c.latest_time
            )
        ).options(joinedload(VehicleLocation.vehicle)).all()
        
        result = []
        for location in locations:
            location_data = self._model_to_dict(location)
            if location.vehicle:
                location_data['vehicle'] = {
                    'id': location.vehicle.id,
                    'vehicle_number': location.vehicle.vehicle_number,
                    'status': location.vehicle.status.value
                }
            result.append(location_data)
        
        if result:
            self._cache_set(cache_key, result, ttl=60)  # 1 minute TTL
        return result
    
    def cleanup_old_locations(self, days: int = 7) -> int:
        """Clean up location records older than specified days"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        deleted_count = self.db.query(VehicleLocation).filter(
            VehicleLocation.recorded_at < cutoff_date
        ).delete()
        
        self.db.commit()
        
        # Clear all location cache after cleanup
        self._cache_delete_pattern(f"{self.model.__tablename__}:*")
        
        return deleted_count
    
    def get_vehicle_speed_stats(self, vehicle_id: int, hours: int = 24) -> Dict:
        """Get speed statistics for a vehicle"""
        cache_key = self._get_cache_key("speed_stats", f"{vehicle_id}:{hours}")
        
        cached_data = self._cache_get(cache_key)
        if cached_data:
            return cached_data
        
        since = datetime.now() - timedelta(hours=hours)
        
        stats = self.db.query(
            func.avg(VehicleLocation.speed).label('avg_speed'),
            func.max(VehicleLocation.speed).label('max_speed'),
            func.min(VehicleLocation.speed).label('min_speed'),
            func.count(VehicleLocation.id).label('data_points')
        ).filter(
            and_(
                VehicleLocation.vehicle_id == vehicle_id,
                VehicleLocation.recorded_at >= since
            )
        ).first()
        
        result = {
            'avg_speed': float(stats.avg_speed) if stats.avg_speed else 0,
            'max_speed': float(stats.max_speed) if stats.max_speed else 0,
            'min_speed': float(stats.min_speed) if stats.min_speed else 0,
            'data_points': stats.data_points or 0
        }
        
        self._cache_set(cache_key, result, ttl=300)  # 5 minutes TTL
        return result