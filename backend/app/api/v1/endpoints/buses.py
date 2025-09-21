from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, and_, or_
from typing import List, Optional
from datetime import datetime, timedelta
from ....core.database import get_db
from ....models.vehicle import Vehicle, VehicleStatus
from ....models.location import VehicleLocation
from ....models.route import Route
from ....models.trip import Trip
from ....models.stop import Stop
from ....schemas.vehicle import VehicleResponse
from ....services.eta_cache_service import eta_cache_service

router = APIRouter()

@router.get("/", response_model=dict)
def get_buses(
    skip: int = Query(0, ge=0, description="Number of buses to skip"),
    limit: int = Query(100, ge=1, le=500, description="Number of buses to return"),
    status: Optional[VehicleStatus] = Query(None, description="Filter buses by status"),
    route_id: Optional[int] = Query(None, description="Filter buses by route ID"),
    route_number: Optional[str] = Query(None, description="Filter buses by route number"),
    with_location: bool = Query(True, description="Include current location data"),
    active_only: bool = Query(True, description="Show only buses with recent location updates"),
    location_max_age_minutes: int = Query(10, ge=1, le=60, description="Max age of location data in minutes"),
    db: Session = Depends(get_db)
):
    """
    Get buses with live location data and filtering capabilities
    
    - **skip**: Number of buses to skip (for pagination)
    - **limit**: Maximum number of buses to return
    - **status**: Filter by vehicle status (active, maintenance, offline)
    - **route_id**: Filter buses currently on specific route
    - **route_number**: Filter buses currently on route with specific number
    - **with_location**: Include current location data in response
    - **active_only**: Show only buses with recent location updates
    - **location_max_age_minutes**: Maximum age of location data to consider "current"
    """
    query = db.query(Vehicle)
    
    # Filter by status
    if status:
        query = query.filter(Vehicle.status == status)
    elif active_only:
        query = query.filter(Vehicle.status == VehicleStatus.ACTIVE)
    
    # Filter by route (through active trips)
    if route_id or route_number:
        trip_query = db.query(Trip.vehicle_id).filter(Trip.status == "active")
        
        if route_id:
            trip_query = trip_query.filter(Trip.route_id == route_id)
        
        if route_number:
            trip_query = trip_query.join(Route).filter(Route.route_number == route_number)
        
        active_vehicle_ids = [t.vehicle_id for t in trip_query.all()]
        query = query.filter(Vehicle.id.in_(active_vehicle_ids))
    
    # Get total count
    total_count = query.count()
    
    # Apply pagination
    buses = query.offset(skip).limit(limit).all()
    
    # Prepare response data
    buses_data = []
    cutoff_time = datetime.utcnow() - timedelta(minutes=location_max_age_minutes)
    
    for bus in buses:
        bus_data = {
            "id": bus.id,
            "vehicle_number": bus.vehicle_number,
            "capacity": bus.capacity,
            "status": bus.status,
            "created_at": bus.created_at,
            "updated_at": bus.updated_at
        }
        
        if with_location:
            # Get latest location
            latest_location = db.query(VehicleLocation).filter(
                VehicleLocation.vehicle_id == bus.id
            ).order_by(desc(VehicleLocation.recorded_at)).first()
            
            if latest_location:
                location_age_minutes = (datetime.utcnow() - latest_location.recorded_at).total_seconds() / 60
                bus_data["current_location"] = {
                    "latitude": float(latest_location.latitude),
                    "longitude": float(latest_location.longitude),
                    "speed": float(latest_location.speed) if latest_location.speed else 0,
                    "bearing": latest_location.bearing,
                    "recorded_at": latest_location.recorded_at,
                    "age_minutes": round(location_age_minutes, 1),
                    "is_recent": latest_location.recorded_at >= cutoff_time
                }
            else:
                bus_data["current_location"] = None
        
        # Get current trip info
        current_trip = db.query(Trip).filter(
            and_(Trip.vehicle_id == bus.id, Trip.status == "active")
        ).first()
        
        if current_trip:
            bus_data["current_trip"] = {
                "id": current_trip.id,
                "route_id": current_trip.route_id,
                "route_name": current_trip.route.name if current_trip.route else None,
                "route_number": current_trip.route.route_number if current_trip.route else None,
                "start_time": current_trip.start_time,
                "driver_id": current_trip.driver_id
            }
        else:
            bus_data["current_trip"] = None
        
        # Mock occupancy data (will be replaced with real data later)
        bus_data["occupancy"] = {
            "level": "medium",
            "percentage": 65,
            "passenger_count": int(bus.capacity * 0.65)
        }
        
        buses_data.append(bus_data)
    
    # Filter out buses without recent location if active_only is True
    if active_only and with_location:
        buses_data = [bus for bus in buses_data 
                     if bus.get("current_location") and bus["current_location"]["is_recent"]]
    
    return {
        "buses": buses_data,
        "total": len(buses_data),
        "total_in_db": total_count,
        "skip": skip,
        "limit": limit,
        "filters": {
            "status": status,
            "route_id": route_id,
            "route_number": route_number,
            "active_only": active_only,
            "location_max_age_minutes": location_max_age_minutes
        }
    }

@router.get("/{bus_id}", response_model=dict)
def get_bus_details(
    bus_id: int, 
    include_location_history: bool = Query(False, description="Include recent location history"),
    history_hours: int = Query(2, ge=1, le=24, description="Hours of location history to include"),
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific bus
    
    - **bus_id**: The ID of the bus
    - **include_location_history**: Whether to include recent location history
    - **history_hours**: Number of hours of location history to include
    """
    bus = db.query(Vehicle).filter(Vehicle.id == bus_id).first()
    if not bus:
        raise HTTPException(status_code=404, detail="Bus not found")
    
    # Get latest location
    latest_location = db.query(VehicleLocation).filter(
        VehicleLocation.vehicle_id == bus.id
    ).order_by(desc(VehicleLocation.recorded_at)).first()
    
    # Get current trip
    current_trip = db.query(Trip).filter(
        and_(Trip.vehicle_id == bus.id, Trip.status == "active")
    ).first()
    
    response = {
        "id": bus.id,
        "vehicle_number": bus.vehicle_number,
        "capacity": bus.capacity,
        "status": bus.status,
        "created_at": bus.created_at,
        "updated_at": bus.updated_at,
        "current_location": None,
        "current_trip": None,
        "occupancy": {
            "level": "medium",
            "percentage": 65,
            "passenger_count": int(bus.capacity * 0.65),
            "last_updated": datetime.utcnow()
        }
    }
    
    if latest_location:
        location_age_minutes = (datetime.utcnow() - latest_location.recorded_at).total_seconds() / 60
        response["current_location"] = {
            "latitude": float(latest_location.latitude),
            "longitude": float(latest_location.longitude),
            "speed": float(latest_location.speed) if latest_location.speed else 0,
            "bearing": latest_location.bearing,
            "recorded_at": latest_location.recorded_at,
            "age_minutes": round(location_age_minutes, 1)
        }
    
    if current_trip:
        response["current_trip"] = {
            "id": current_trip.id,
            "route_id": current_trip.route_id,
            "route_name": current_trip.route.name if current_trip.route else None,
            "route_number": current_trip.route.route_number if current_trip.route else None,
            "start_time": current_trip.start_time,
            "end_time": current_trip.end_time,
            "status": current_trip.status,
            "driver_id": current_trip.driver_id
        }
    
    # Include location history if requested
    if include_location_history:
        cutoff_time = datetime.utcnow() - timedelta(hours=history_hours)
        location_history = db.query(VehicleLocation).filter(
            and_(
                VehicleLocation.vehicle_id == bus.id,
                VehicleLocation.recorded_at >= cutoff_time
            )
        ).order_by(desc(VehicleLocation.recorded_at)).limit(100).all()
        
        response["location_history"] = [
            {
                "latitude": float(loc.latitude),
                "longitude": float(loc.longitude),
                "speed": float(loc.speed) if loc.speed else 0,
                "bearing": loc.bearing,
                "recorded_at": loc.recorded_at
            }
            for loc in location_history
        ]
    
    return response

@router.get("/{bus_id}/location", response_model=dict)
def get_bus_location(
    bus_id: int, 
    max_age_minutes: int = Query(10, ge=1, le=60, description="Maximum age of location data in minutes"),
    db: Session = Depends(get_db)
):
    """
    Get current location of a specific bus
    
    - **bus_id**: The ID of the bus
    - **max_age_minutes**: Maximum age of location data to consider "current"
    """
    bus = db.query(Vehicle).filter(Vehicle.id == bus_id).first()
    if not bus:
        raise HTTPException(status_code=404, detail="Bus not found")
    
    # Get latest location
    latest_location = db.query(VehicleLocation).filter(
        VehicleLocation.vehicle_id == bus.id
    ).order_by(desc(VehicleLocation.recorded_at)).first()
    
    if not latest_location:
        raise HTTPException(status_code=404, detail="No location data found for this bus")
    
    # Check if location is recent enough
    location_age_minutes = (datetime.utcnow() - latest_location.recorded_at).total_seconds() / 60
    is_recent = location_age_minutes <= max_age_minutes
    
    return {
        "vehicle_id": bus.id,
        "vehicle_number": bus.vehicle_number,
        "location": {
            "latitude": float(latest_location.latitude),
            "longitude": float(latest_location.longitude),
            "speed": float(latest_location.speed) if latest_location.speed else 0,
            "bearing": latest_location.bearing,
            "recorded_at": latest_location.recorded_at,
            "age_minutes": round(location_age_minutes, 1),
            "is_recent": is_recent
        },
        "status": bus.status
    }

@router.get("/{bus_id}/occupancy", response_model=dict)
def get_bus_occupancy(bus_id: int, db: Session = Depends(get_db)):
    """
    Get current occupancy information for a specific bus
    
    - **bus_id**: The ID of the bus
    """
    bus = db.query(Vehicle).filter(Vehicle.id == bus_id).first()
    if not bus:
        raise HTTPException(status_code=404, detail="Bus not found")
    
    # Mock occupancy data (will be replaced with real data from driver reports)
    import random
    occupancy_percentage = random.randint(20, 95)
    passenger_count = int(bus.capacity * (occupancy_percentage / 100))
    
    if occupancy_percentage < 30:
        level = "low"
    elif occupancy_percentage < 70:
        level = "medium"
    else:
        level = "high"
    
    return {
        "vehicle_id": bus.id,
        "vehicle_number": bus.vehicle_number,
        "capacity": bus.capacity,
        "occupancy": {
            "level": level,
            "percentage": occupancy_percentage,
            "passenger_count": passenger_count,
            "available_seats": bus.capacity - passenger_count,
            "last_updated": datetime.utcnow()
        }
    }

@router.get("/{bus_id}/eta/{stop_id}", response_model=dict)
async def get_bus_eta_to_stop(
    bus_id: int, 
    stop_id: int,
    force_recalculate: bool = Query(False, description="Force ETA recalculation"),
    include_confidence: bool = Query(True, description="Include confidence metrics"),
    db: Session = Depends(get_db)
):
    """
    Get ETA for a specific bus to reach a specific stop
    
    - **bus_id**: The ID of the bus
    - **stop_id**: The ID of the destination stop
    - **force_recalculate**: Force recalculation even if cached ETA exists
    - **include_confidence**: Include detailed confidence metrics
    """
    # Verify bus exists
    bus = db.query(Vehicle).filter(Vehicle.id == bus_id).first()
    if not bus:
        raise HTTPException(status_code=404, detail="Bus not found")
    
    # Verify stop exists
    stop = db.query(Stop).filter(Stop.id == stop_id).first()
    if not stop:
        raise HTTPException(status_code=404, detail="Stop not found")
    
    # Calculate ETA
    eta_result = await eta_cache_service.get_eta(bus_id, stop_id, force_recalculate)
    
    if not eta_result:
        raise HTTPException(
            status_code=503, 
            detail="Unable to calculate ETA. Bus location data may be unavailable."
        )
    
    response = {
        "vehicle_id": bus_id,
        "vehicle_number": bus.vehicle_number,
        "stop_id": stop_id,
        "stop_name": stop.name,
        "stop_name_kannada": stop.name_kannada,
        "eta": {
            "seconds": eta_result.eta_seconds,
            "minutes": round(eta_result.eta_minutes, 1),
            "formatted": f"{eta_result.eta_seconds // 60}m {eta_result.eta_seconds % 60}s",
            "arrival_time": (datetime.now() + timedelta(seconds=eta_result.eta_seconds)).isoformat()
        },
        "distance_meters": round(eta_result.distance_meters),
        "average_speed_kmh": round(eta_result.average_speed_kmh, 1),
        "calculation_method": eta_result.calculation_method,
        "calculated_at": eta_result.calculated_at.isoformat()
    }
    
    if include_confidence:
        confidence_info = await eta_cache_service.get_eta_confidence_score(eta_result)
        response["confidence"] = confidence_info
        response["traffic_factor"] = eta_result.traffic_factor
        response["delay_factor"] = eta_result.delay_factor
    
    return response

@router.get("/{bus_id}/eta", response_model=dict)
async def get_bus_eta_to_multiple_stops(
    bus_id: int,
    stop_ids: str = Query(..., description="Comma-separated list of stop IDs"),
    include_confidence: bool = Query(False, description="Include confidence metrics"),
    db: Session = Depends(get_db)
):
    """
    Get ETA for a specific bus to multiple stops
    
    - **bus_id**: The ID of the bus
    - **stop_ids**: Comma-separated list of stop IDs (e.g., "1,2,3")
    - **include_confidence**: Include detailed confidence metrics
    """
    # Verify bus exists
    bus = db.query(Vehicle).filter(Vehicle.id == bus_id).first()
    if not bus:
        raise HTTPException(status_code=404, detail="Bus not found")
    
    # Parse stop IDs
    try:
        stop_id_list = [int(sid.strip()) for sid in stop_ids.split(",")]
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid stop IDs format")
    
    if len(stop_id_list) > 20:  # Limit to prevent abuse
        raise HTTPException(status_code=400, detail="Too many stops requested (max 20)")
    
    # Verify stops exist
    stops = db.query(Stop).filter(Stop.id.in_(stop_id_list)).all()
    found_stop_ids = {stop.id for stop in stops}
    missing_stops = set(stop_id_list) - found_stop_ids
    
    if missing_stops:
        raise HTTPException(
            status_code=404, 
            detail=f"Stops not found: {list(missing_stops)}"
        )
    
    # Calculate ETAs for all stops
    vehicle_stop_pairs = [(bus_id, stop_id) for stop_id in stop_id_list]
    eta_results = await eta_cache_service.get_multiple_etas(vehicle_stop_pairs)
    
    # Build response
    stops_dict = {stop.id: stop for stop in stops}
    eta_data = []
    
    for stop_id in stop_id_list:
        stop = stops_dict[stop_id]
        eta_result = eta_results.get((bus_id, stop_id))
        
        if eta_result:
            eta_info = {
                "stop_id": stop_id,
                "stop_name": stop.name,
                "stop_name_kannada": stop.name_kannada,
                "eta": {
                    "seconds": eta_result.eta_seconds,
                    "minutes": round(eta_result.eta_minutes, 1),
                    "formatted": f"{eta_result.eta_seconds // 60}m {eta_result.eta_seconds % 60}s",
                    "arrival_time": (datetime.now() + timedelta(seconds=eta_result.eta_seconds)).isoformat()
                },
                "distance_meters": round(eta_result.distance_meters),
                "calculation_method": eta_result.calculation_method,
                "calculated_at": eta_result.calculated_at.isoformat()
            }
            
            if include_confidence:
                confidence_info = await eta_cache_service.get_eta_confidence_score(eta_result)
                eta_info["confidence"] = confidence_info
                eta_info["traffic_factor"] = eta_result.traffic_factor
                eta_info["delay_factor"] = eta_result.delay_factor
        else:
            eta_info = {
                "stop_id": stop_id,
                "stop_name": stop.name,
                "stop_name_kannada": stop.name_kannada,
                "eta": None,
                "error": "Unable to calculate ETA"
            }
        
        eta_data.append(eta_info)
    
    return {
        "vehicle_id": bus_id,
        "vehicle_number": bus.vehicle_number,
        "etas": eta_data,
        "calculated_at": datetime.now().isoformat()
    }