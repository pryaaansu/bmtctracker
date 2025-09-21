from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel
import time

from ....core.database import get_db
from ....services.api_auth_service import APIAuthService, check_rate_limit
from ....models.api_key import APIKey
from ....models.bus import Bus
from ....models.route import Route
from ....models.stop import Stop
from ....models.location import VehicleLocation
from ....models.trip import Trip, TripStatus

router = APIRouter()

# Pydantic models for public API responses
class PublicBusResponse(BaseModel):
    id: int
    vehicle_number: str
    status: str
    current_location: Optional[Dict[str, Any]] = None
    current_trip: Optional[Dict[str, Any]] = None
    occupancy: Optional[Dict[str, Any]] = None
    last_updated: Optional[datetime] = None

class PublicRouteResponse(BaseModel):
    id: int
    name: str
    route_number: str
    is_active: bool
    total_stops: int
    estimated_duration_minutes: Optional[int] = None
    start_stop: Optional[Dict[str, Any]] = None
    end_stop: Optional[Dict[str, Any]] = None

class PublicStopResponse(BaseModel):
    id: int
    name: str
    name_kannada: Optional[str] = None
    latitude: float
    longitude: float
    is_active: bool
    routes: List[Dict[str, Any]] = []

class PublicLocationResponse(BaseModel):
    vehicle_id: int
    latitude: float
    longitude: float
    speed: Optional[float] = None
    bearing: Optional[float] = None
    recorded_at: datetime
    is_recent: bool

class PublicTripResponse(BaseModel):
    id: int
    vehicle_number: str
    route_number: str
    route_name: str
    status: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    current_location: Optional[Dict[str, Any]] = None
    next_stop: Optional[Dict[str, Any]] = None
    eta_minutes: Optional[int] = None

class APIResponse(BaseModel):
    success: bool
    data: Any
    message: Optional[str] = None
    timestamp: datetime
    request_id: Optional[str] = None

# Helper function to create API response
def create_api_response(data: Any, message: str = None, request_id: str = None) -> APIResponse:
    return APIResponse(
        success=True,
        data=data,
        message=message,
        timestamp=datetime.utcnow(),
        request_id=request_id
    )

# Public API endpoints

@router.get("/buses", response_model=APIResponse)
def get_public_buses(
    request: Request,
    response: Response,
    status: Optional[str] = Query(None, description="Filter by bus status"),
    route_id: Optional[int] = Query(None, description="Filter by route ID"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of buses to return"),
    offset: int = Query(0, ge=0, description="Number of buses to skip"),
    api_key: APIKey = Depends(check_rate_limit),
    db: Session = Depends(get_db)
):
    """
    Get list of buses with real-time information
    
    Returns a list of buses with their current status, location, and trip information.
    """
    start_time = time.time()
    
    try:
        # Build query
        query = db.query(Bus).filter(Bus.is_active == True)
        
        if status:
            query = query.filter(Bus.status == status)
        
        if route_id:
            # Join with trips to filter by route
            query = query.join(Trip, Bus.id == Trip.vehicle_id).filter(
                Trip.route_id == route_id,
                Trip.status == TripStatus.ACTIVE
            )
        
        # Apply pagination
        buses = query.offset(offset).limit(limit).all()
        
        # Format response data
        bus_data = []
        for bus in buses:
            # Get current location
            current_location = None
            last_location = db.query(VehicleLocation).filter(
                VehicleLocation.vehicle_id == bus.id
            ).order_by(VehicleLocation.recorded_at.desc()).first()
            
            if last_location:
                current_location = {
                    "latitude": last_location.latitude,
                    "longitude": last_location.longitude,
                    "speed": last_location.speed,
                    "bearing": last_location.bearing,
                    "recorded_at": last_location.recorded_at.isoformat(),
                    "is_recent": last_location.is_recent
                }
            
            # Get current trip
            current_trip = None
            active_trip = db.query(Trip).filter(
                Trip.vehicle_id == bus.id,
                Trip.status == TripStatus.ACTIVE
            ).first()
            
            if active_trip:
                route = db.query(Route).filter(Route.id == active_trip.route_id).first()
                current_trip = {
                    "id": active_trip.id,
                    "route_id": active_trip.route_id,
                    "route_number": route.route_number if route else None,
                    "route_name": route.name if route else None,
                    "start_time": active_trip.start_time.isoformat() if active_trip.start_time else None
                }
            
            bus_data.append({
                "id": bus.id,
                "vehicle_number": bus.vehicle_number,
                "status": bus.status,
                "current_location": current_location,
                "current_trip": current_trip,
                "last_updated": last_location.recorded_at.isoformat() if last_location else None
            })
        
        # Log API usage
        auth_service = APIAuthService(db)
        auth_service.log_api_usage(
            api_key_id=api_key.id,
            endpoint=f"GET {request.url.path}",
            method="GET",
            status_code=200,
            response_time_ms=int((time.time() - start_time) * 1000),
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
        
        return create_api_response(
            data=bus_data,
            message=f"Retrieved {len(bus_data)} buses",
            request_id=request.headers.get("x-request-id")
        )
        
    except Exception as e:
        # Log error
        auth_service = APIAuthService(db)
        auth_service.log_api_usage(
            api_key_id=api_key.id,
            endpoint=f"GET {request.url.path}",
            method="GET",
            status_code=500,
            response_time_ms=int((time.time() - start_time) * 1000),
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            error_message=str(e)
        )
        
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/buses/{bus_id}", response_model=APIResponse)
def get_public_bus(
    bus_id: int,
    request: Request,
    response: Response,
    api_key: APIKey = Depends(check_rate_limit),
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific bus
    
    Returns detailed information about a bus including current location, trip, and occupancy.
    """
    start_time = time.time()
    
    try:
        bus = db.query(Bus).filter(Bus.id == bus_id, Bus.is_active == True).first()
        
        if not bus:
            raise HTTPException(status_code=404, detail="Bus not found")
        
        # Get current location
        current_location = None
        last_location = db.query(VehicleLocation).filter(
            VehicleLocation.vehicle_id == bus.id
        ).order_by(VehicleLocation.recorded_at.desc()).first()
        
        if last_location:
            current_location = {
                "latitude": last_location.latitude,
                "longitude": last_location.longitude,
                "speed": last_location.speed,
                "bearing": last_location.bearing,
                "recorded_at": last_location.recorded_at.isoformat(),
                "is_recent": last_location.is_recent
            }
        
        # Get current trip
        current_trip = None
        active_trip = db.query(Trip).filter(
            Trip.vehicle_id == bus.id,
            Trip.status == TripStatus.ACTIVE
        ).first()
        
        if active_trip:
            route = db.query(Route).filter(Route.id == active_trip.route_id).first()
            current_trip = {
                "id": active_trip.id,
                "route_id": active_trip.route_id,
                "route_number": route.route_number if route else None,
                "route_name": route.name if route else None,
                "start_time": active_trip.start_time.isoformat() if active_trip.start_time else None
            }
        
        bus_data = {
            "id": bus.id,
            "vehicle_number": bus.vehicle_number,
            "status": bus.status,
            "current_location": current_location,
            "current_trip": current_trip,
            "last_updated": last_location.recorded_at.isoformat() if last_location else None
        }
        
        # Log API usage
        auth_service = APIAuthService(db)
        auth_service.log_api_usage(
            api_key_id=api_key.id,
            endpoint=f"GET {request.url.path}",
            method="GET",
            status_code=200,
            response_time_ms=int((time.time() - start_time) * 1000),
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
        
        return create_api_response(
            data=bus_data,
            message="Bus details retrieved successfully",
            request_id=request.headers.get("x-request-id")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        # Log error
        auth_service = APIAuthService(db)
        auth_service.log_api_usage(
            api_key_id=api_key.id,
            endpoint=f"GET {request.url.path}",
            method="GET",
            status_code=500,
            response_time_ms=int((time.time() - start_time) * 1000),
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            error_message=str(e)
        )
        
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/routes", response_model=APIResponse)
def get_public_routes(
    request: Request,
    response: Response,
    active_only: bool = Query(True, description="Return only active routes"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of routes to return"),
    offset: int = Query(0, ge=0, description="Number of routes to skip"),
    api_key: APIKey = Depends(check_rate_limit),
    db: Session = Depends(get_db)
):
    """
    Get list of routes
    
    Returns a list of bus routes with their basic information.
    """
    start_time = time.time()
    
    try:
        # Build query
        query = db.query(Route)
        
        if active_only:
            query = query.filter(Route.is_active == True)
        
        # Apply pagination
        routes = query.offset(offset).limit(limit).all()
        
        # Format response data
        route_data = []
        for route in routes:
            # Count stops
            stop_count = len(route.stops) if route.stops else 0
            
            # Get start and end stops
            start_stop = None
            end_stop = None
            if route.stops:
                start_stop = {
                    "id": route.stops[0].id,
                    "name": route.stops[0].name,
                    "latitude": route.stops[0].latitude,
                    "longitude": route.stops[0].longitude
                }
                end_stop = {
                    "id": route.stops[-1].id,
                    "name": route.stops[-1].name,
                    "latitude": route.stops[-1].latitude,
                    "longitude": route.stops[-1].longitude
                }
            
            route_data.append({
                "id": route.id,
                "name": route.name,
                "route_number": route.route_number,
                "is_active": route.is_active,
                "total_stops": stop_count,
                "start_stop": start_stop,
                "end_stop": end_stop
            })
        
        # Log API usage
        auth_service = APIAuthService(db)
        auth_service.log_api_usage(
            api_key_id=api_key.id,
            endpoint=f"GET {request.url.path}",
            method="GET",
            status_code=200,
            response_time_ms=int((time.time() - start_time) * 1000),
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
        
        return create_api_response(
            data=route_data,
            message=f"Retrieved {len(route_data)} routes",
            request_id=request.headers.get("x-request-id")
        )
        
    except Exception as e:
        # Log error
        auth_service = APIAuthService(db)
        auth_service.log_api_usage(
            api_key_id=api_key.id,
            endpoint=f"GET {request.url.path}",
            method="GET",
            status_code=500,
            response_time_ms=int((time.time() - start_time) * 1000),
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            error_message=str(e)
        )
        
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/routes/{route_id}", response_model=APIResponse)
def get_public_route(
    route_id: int,
    request: Request,
    response: Response,
    api_key: APIKey = Depends(check_rate_limit),
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific route
    
    Returns detailed information about a route including all stops and active trips.
    """
    start_time = time.time()
    
    try:
        route = db.query(Route).filter(Route.id == route_id).first()
        
        if not route:
            raise HTTPException(status_code=404, detail="Route not found")
        
        # Get stops
        stops_data = []
        if route.stops:
            for stop in route.stops:
                stops_data.append({
                    "id": stop.id,
                    "name": stop.name,
                    "name_kannada": stop.name_kannada,
                    "latitude": stop.latitude,
                    "longitude": stop.longitude,
                    "sequence": stop.sequence
                })
        
        # Get active trips
        active_trips = db.query(Trip).filter(
            Trip.route_id == route_id,
            Trip.status == TripStatus.ACTIVE
        ).all()
        
        trips_data = []
        for trip in active_trips:
            bus = db.query(Bus).filter(Bus.id == trip.vehicle_id).first()
            if bus:
                trips_data.append({
                    "id": trip.id,
                    "vehicle_number": bus.vehicle_number,
                    "start_time": trip.start_time.isoformat() if trip.start_time else None
                })
        
        route_data = {
            "id": route.id,
            "name": route.name,
            "route_number": route.route_number,
            "is_active": route.is_active,
            "stops": stops_data,
            "active_trips": trips_data,
            "total_stops": len(stops_data),
            "active_trips_count": len(trips_data)
        }
        
        # Log API usage
        auth_service = APIAuthService(db)
        auth_service.log_api_usage(
            api_key_id=api_key.id,
            endpoint=f"GET {request.url.path}",
            method="GET",
            status_code=200,
            response_time_ms=int((time.time() - start_time) * 1000),
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
        
        return create_api_response(
            data=route_data,
            message="Route details retrieved successfully",
            request_id=request.headers.get("x-request-id")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        # Log error
        auth_service = APIAuthService(db)
        auth_service.log_api_usage(
            api_key_id=api_key.id,
            endpoint=f"GET {request.url.path}",
            method="GET",
            status_code=500,
            response_time_ms=int((time.time() - start_time) * 1000),
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            error_message=str(e)
        )
        
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/stops", response_model=APIResponse)
def get_public_stops(
    request: Request,
    response: Response,
    active_only: bool = Query(True, description="Return only active stops"),
    route_id: Optional[int] = Query(None, description="Filter by route ID"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of stops to return"),
    offset: int = Query(0, ge=0, description="Number of stops to skip"),
    api_key: APIKey = Depends(check_rate_limit),
    db: Session = Depends(get_db)
):
    """
    Get list of stops
    
    Returns a list of bus stops with their location and route information.
    """
    start_time = time.time()
    
    try:
        # Build query
        query = db.query(Stop)
        
        if active_only:
            query = query.filter(Stop.is_active == True)
        
        if route_id:
            query = query.join(RouteStop).filter(RouteStop.route_id == route_id)
        
        # Apply pagination
        stops = query.offset(offset).limit(limit).all()
        
        # Format response data
        stop_data = []
        for stop in stops:
            # Get routes for this stop
            routes_data = []
            if stop.routes:
                for route in stop.routes:
                    routes_data.append({
                        "id": route.id,
                        "name": route.name,
                        "route_number": route.route_number
                    })
            
            stop_data.append({
                "id": stop.id,
                "name": stop.name,
                "name_kannada": stop.name_kannada,
                "latitude": stop.latitude,
                "longitude": stop.longitude,
                "is_active": stop.is_active,
                "routes": routes_data
            })
        
        # Log API usage
        auth_service = APIAuthService(db)
        auth_service.log_api_usage(
            api_key_id=api_key.id,
            endpoint=f"GET {request.url.path}",
            method="GET",
            status_code=200,
            response_time_ms=int((time.time() - start_time) * 1000),
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
        
        return create_api_response(
            data=stop_data,
            message=f"Retrieved {len(stop_data)} stops",
            request_id=request.headers.get("x-request-id")
        )
        
    except Exception as e:
        # Log error
        auth_service = APIAuthService(db)
        auth_service.log_api_usage(
            api_key_id=api_key.id,
            endpoint=f"GET {request.url.path}",
            method="GET",
            status_code=500,
            response_time_ms=int((time.time() - start_time) * 1000),
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            error_message=str(e)
        )
        
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/realtime/locations", response_model=APIResponse)
def get_realtime_locations(
    request: Request,
    response: Response,
    vehicle_ids: Optional[str] = Query(None, description="Comma-separated list of vehicle IDs"),
    route_ids: Optional[str] = Query(None, description="Comma-separated list of route IDs"),
    recent_only: bool = Query(True, description="Return only recent locations (within last 5 minutes)"),
    limit: int = Query(1000, ge=1, le=5000, description="Maximum number of locations to return"),
    api_key: APIKey = Depends(check_rate_limit),
    db: Session = Depends(get_db)
):
    """
    Get real-time vehicle locations
    
    Returns current locations of vehicles with optional filtering by vehicle or route IDs.
    """
    start_time = time.time()
    
    try:
        # Build query
        query = db.query(VehicleLocation)
        
        if recent_only:
            # Only locations from last 5 minutes
            cutoff_time = datetime.utcnow() - timedelta(minutes=5)
            query = query.filter(VehicleLocation.recorded_at >= cutoff_time)
        
        if vehicle_ids:
            vehicle_id_list = [int(id.strip()) for id in vehicle_ids.split(",")]
            query = query.filter(VehicleLocation.vehicle_id.in_(vehicle_id_list))
        
        if route_ids:
            route_id_list = [int(id.strip()) for id in route_ids.split(",")]
            # Join with trips to filter by route
            query = query.join(Trip, VehicleLocation.vehicle_id == Trip.vehicle_id).filter(
                Trip.route_id.in_(route_id_list),
                Trip.status == TripStatus.ACTIVE
            )
        
        # Apply limit and order by most recent
        locations = query.order_by(VehicleLocation.recorded_at.desc()).limit(limit).all()
        
        # Format response data
        location_data = []
        for location in locations:
            location_data.append({
                "vehicle_id": location.vehicle_id,
                "latitude": location.latitude,
                "longitude": location.longitude,
                "speed": location.speed,
                "bearing": location.bearing,
                "recorded_at": location.recorded_at.isoformat(),
                "is_recent": location.is_recent
            })
        
        # Log API usage
        auth_service = APIAuthService(db)
        auth_service.log_api_usage(
            api_key_id=api_key.id,
            endpoint=f"GET {request.url.path}",
            method="GET",
            status_code=200,
            response_time_ms=int((time.time() - start_time) * 1000),
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
        
        return create_api_response(
            data=location_data,
            message=f"Retrieved {len(location_data)} locations",
            request_id=request.headers.get("x-request-id")
        )
        
    except Exception as e:
        # Log error
        auth_service = APIAuthService(db)
        auth_service.log_api_usage(
            api_key_id=api_key.id,
            endpoint=f"GET {request.url.path}",
            method="GET",
            status_code=500,
            response_time_ms=int((time.time() - start_time) * 1000),
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            error_message=str(e)
        )
        
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/health", response_model=APIResponse)
def get_api_health(
    request: Request,
    response: Response,
    api_key: APIKey = Depends(check_rate_limit),
    db: Session = Depends(get_db)
):
    """
    Get API health status
    
    Returns the current status of the API and its dependencies.
    """
    start_time = time.time()
    
    try:
        # Check database connection
        db_status = "healthy"
        try:
            db.execute("SELECT 1")
        except Exception:
            db_status = "unhealthy"
        
        # Check Redis connection (if available)
        redis_status = "not_configured"
        try:
            from ..services.api_auth_service import redis_client, REDIS_AVAILABLE
            if REDIS_AVAILABLE:
                redis_client.ping()
                redis_status = "healthy"
        except Exception:
            redis_status = "unhealthy"
        
        health_data = {
            "status": "healthy" if db_status == "healthy" else "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "dependencies": {
                "database": db_status,
                "redis": redis_status
            },
            "api_key_info": {
                "key_name": api_key.key_name,
                "total_requests": api_key.total_requests,
                "last_used": api_key.last_used.isoformat() if api_key.last_used else None
            }
        }
        
        # Log API usage
        auth_service = APIAuthService(db)
        auth_service.log_api_usage(
            api_key_id=api_key.id,
            endpoint=f"GET {request.url.path}",
            method="GET",
            status_code=200,
            response_time_ms=int((time.time() - start_time) * 1000),
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
        
        return create_api_response(
            data=health_data,
            message="API health status retrieved",
            request_id=request.headers.get("x-request-id")
        )
        
    except Exception as e:
        # Log error
        auth_service = APIAuthService(db)
        auth_service.log_api_usage(
            api_key_id=api_key.id,
            endpoint=f"GET {request.url.path}",
            method="GET",
            status_code=500,
            response_time_ms=int((time.time() - start_time) * 1000),
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            error_message=str(e)
        )
        
        raise HTTPException(status_code=500, detail="Internal server error")

