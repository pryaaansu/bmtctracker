"""
Route repository with specific business logic
"""
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_

from .base import BaseRepository
from ..models.route import Route
from ..models.stop import Stop
from ..schemas.route import RouteCreate, RouteUpdate

class RouteRepository(BaseRepository[Route, RouteCreate, RouteUpdate]):
    """Repository for Route model with specific business logic"""
    
    def __init__(self, db: Session):
        super().__init__(Route, db)
    
    def get_by_route_number(self, route_number: str) -> Optional[Route]:
        """Get route by route number"""
        cache_key = self._get_cache_key("route_number", route_number)
        
        cached_data = self._cache_get(cache_key)
        if cached_data:
            return cached_data
        
        route = self.db.query(Route).filter(Route.route_number == route_number).first()
        if route:
            self._cache_set(cache_key, self._model_to_dict(route))
        return route
    
    def get_active_routes(self) -> List[Route]:
        """Get all active routes"""
        cache_key = self._get_cache_key("active", "all")
        
        cached_data = self._cache_get(cache_key)
        if cached_data:
            return cached_data
        
        routes = self.db.query(Route).filter(Route.is_active == True).all()
        if routes:
            data = [self._model_to_dict(route) for route in routes]
            self._cache_set(cache_key, data, ttl=300)  # 5 minutes TTL
        return routes
    
    def get_with_stops(self, route_id: int) -> Optional[Route]:
        """Get route with all its stops"""
        cache_key = self._get_cache_key("with_stops", route_id)
        
        cached_data = self._cache_get(cache_key)
        if cached_data:
            return cached_data
        
        route = self.db.query(Route).options(
            joinedload(Route.stops)
        ).filter(Route.id == route_id).first()
        
        if route:
            # For caching, we need to serialize the route with stops
            route_data = self._model_to_dict(route)
            route_data['stops'] = [
                {
                    'id': stop.id,
                    'name': stop.name,
                    'name_kannada': stop.name_kannada,
                    'latitude': float(stop.latitude),
                    'longitude': float(stop.longitude),
                    'stop_order': stop.stop_order
                }
                for stop in sorted(route.stops, key=lambda x: x.stop_order)
            ]
            self._cache_set(cache_key, route_data, ttl=600)  # 10 minutes TTL
        
        return route
    
    def search_routes(self, query: str) -> List[Route]:
        """Search routes by name or route number"""
        cache_key = self._get_cache_key("search", query.lower())
        
        cached_data = self._cache_get(cache_key)
        if cached_data:
            return cached_data
        
        routes = self.db.query(Route).filter(
            and_(
                Route.is_active == True,
                (Route.name.ilike(f"%{query}%") | Route.route_number.ilike(f"%{query}%"))
            )
        ).all()
        
        if routes:
            data = [self._model_to_dict(route) for route in routes]
            self._cache_set(cache_key, data, ttl=180)  # 3 minutes TTL
        return routes
    
    def get_routes_by_stop_name(self, stop_name: str) -> List[Route]:
        """Get routes that have a stop with the given name"""
        cache_key = self._get_cache_key("by_stop", stop_name.lower())
        
        cached_data = self._cache_get(cache_key)
        if cached_data:
            return cached_data
        
        routes = self.db.query(Route).join(Stop).filter(
            and_(
                Route.is_active == True,
                (Stop.name.ilike(f"%{stop_name}%") | Stop.name_kannada.ilike(f"%{stop_name}%"))
            )
        ).distinct().all()
        
        if routes:
            data = [self._model_to_dict(route) for route in routes]
            self._cache_set(cache_key, data, ttl=300)
        return routes
    
    def toggle_active_status(self, route_id: int) -> Optional[Route]:
        """Toggle route active status"""
        route = self.get(route_id, use_cache=False)
        if route:
            route.is_active = not route.is_active
            self.db.commit()
            self.db.refresh(route)
            
            # Invalidate related cache
            self._cache_delete_pattern(f"{self.model.__tablename__}:*")
            
        return route