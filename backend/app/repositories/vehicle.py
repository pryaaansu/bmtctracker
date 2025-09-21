"""
Vehicle repository with specific business logic
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from .base import BaseRepository
from ..models.vehicle import Vehicle, VehicleStatus
from ..schemas.vehicle import VehicleCreate, VehicleUpdate

class VehicleRepository(BaseRepository[Vehicle, VehicleCreate, VehicleUpdate]):
    """Repository for Vehicle model with specific business logic"""
    
    def __init__(self, db: Session):
        super().__init__(Vehicle, db)
    
    def get_by_vehicle_number(self, vehicle_number: str) -> Optional[Vehicle]:
        """Get vehicle by vehicle number"""
        cache_key = self._get_cache_key("vehicle_number", vehicle_number)
        
        cached_data = self._cache_get(cache_key)
        if cached_data:
            return cached_data
        
        vehicle = self.db.query(Vehicle).filter(Vehicle.vehicle_number == vehicle_number).first()
        if vehicle:
            self._cache_set(cache_key, self._model_to_dict(vehicle))
        return vehicle
    
    def get_active_vehicles(self) -> List[Vehicle]:
        """Get all active vehicles"""
        cache_key = self._get_cache_key("status", "active")
        
        cached_data = self._cache_get(cache_key)
        if cached_data:
            return cached_data
        
        vehicles = self.db.query(Vehicle).filter(Vehicle.status == VehicleStatus.ACTIVE).all()
        if vehicles:
            data = [self._model_to_dict(vehicle) for vehicle in vehicles]
            self._cache_set(cache_key, data, ttl=120)  # 2 minutes TTL
        return vehicles
    
    def get_by_status(self, status: VehicleStatus) -> List[Vehicle]:
        """Get vehicles by status"""
        cache_key = self._get_cache_key("status", status.value)
        
        cached_data = self._cache_get(cache_key)
        if cached_data:
            return cached_data
        
        vehicles = self.db.query(Vehicle).filter(Vehicle.status == status).all()
        if vehicles:
            data = [self._model_to_dict(vehicle) for vehicle in vehicles]
            self._cache_set(cache_key, data, ttl=120)
        return vehicles
    
    def get_available_vehicles(self) -> List[Vehicle]:
        """Get vehicles that are active and not assigned to a driver"""
        cache_key = self._get_cache_key("available", "all")
        
        cached_data = self._cache_get(cache_key)
        if cached_data:
            return cached_data
        
        vehicles = self.db.query(Vehicle).filter(
            and_(
                Vehicle.status == VehicleStatus.ACTIVE,
                ~Vehicle.assigned_driver.has()  # No assigned driver
            )
        ).all()
        
        if vehicles:
            data = [self._model_to_dict(vehicle) for vehicle in vehicles]
            self._cache_set(cache_key, data, ttl=60)  # 1 minute TTL
        return vehicles
    
    def update_status(self, vehicle_id: int, status: VehicleStatus) -> Optional[Vehicle]:
        """Update vehicle status"""
        vehicle = self.get(vehicle_id, use_cache=False)
        if vehicle:
            vehicle.status = status
            self.db.commit()
            self.db.refresh(vehicle)
            
            # Invalidate related cache
            self._cache_delete_pattern(f"{self.model.__tablename__}:*")
            
        return vehicle
    
    def get_vehicles_with_current_location(self) -> List[dict]:
        """Get vehicles with their most recent location"""
        # This would typically join with vehicle_locations table
        # For now, return basic vehicle info
        return self.get_active_vehicles()