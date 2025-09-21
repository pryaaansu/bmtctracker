from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, func, text, and_
from typing import List, Optional
from math import radians, cos, sin, asin, sqrt
from datetime import datetime, timedelta
from ....core.database import get_db
from ....models.stop import Stop
from ....models.route import Route
from ....models.vehicle import Vehicle, VehicleStatus
from ....models.trip import Trip
from ....models.location import VehicleLocation
from ....schemas.stop import StopResponse
from ....services.eta_cache_service import eta_cache_service

router = APIRouter()

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great circle distance between two points on earth in kilometers"""
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371  # Radius of earth in kilometers
    return c * r

@router.get("/", response_model=dict)
def get_stops(
    skip: int = Query(0, ge=0, description="Number of stops to skip"),
    limit: int = Query(100, ge=1, le=500, description="Number of stops to return"),
    lat: Optional[float] = Query(None, description="Latitude for nearby search"),
    lng: Optional[float] = Query(None, description="Longitude for nearby search"),
    radius: Optional[float] = Query(1.0, ge=0.1, le=50.0, description="Search radius in km"),
    search: Optional[str] = Query(None, description="Search stops by name"),
    route_id: Optional[int] = Query(None, description="Filter stops by route ID"),
    route_number: Optional[str] = Query(None, description="Filter stops by route number"),
    db: Session = Depends(get_db)
):
    """
    Get stops with geospatial search and filtering capabilities
    
    - **skip**: Number of stops to skip (for pagination)
    - **limit**: Maximum number of stops to return
    - **lat**: Latitude for nearby search
    - **lng**: Longitude for nearby search  
    - **radius**: Search radius in kilometers (0.1 to 50.0)
    - **search**: Search term to filter stops by name
    - **route_id**: Filter stops by specific route ID
    - **route_number**: Filter stops by route number
    """
    query = db.query(Stop).options(joinedload(Stop.route))
    
    # Filter by route ID
    if route_id:
        query = query.filter(Stop.route_id == route_id)
    
    # Filter by route number
    if route_number:
        query = query.join(Route).filter(Route.route_number == route_number)
    
    # Search filter
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Stop.name.ilike(search_term),
                Stop.name_kannada.ilike(search_term)
            )
        )
    
    # Geospatial filtering
    if lat is not None and lng is not None:
        # Use bounding box for initial filtering (more efficient)
        # Approximate: 1 degree ≈ 111 km
        lat_delta = radius / 111.0
        lng_delta = radius / (111.0 * cos(radians(lat)))
        
        query = query.filter(
            Stop.latitude.between(lat - lat_delta, lat + lat_delta),
            Stop.longitude.between(lng - lng_delta, lng + lng_delta)
        )
    
    # Get total count before pagination
    total_count = query.count()
    
    # Apply pagination
    stops = query.offset(skip).limit(limit).all()
    
    # If geospatial search, calculate actual distances and sort
    if lat is not None and lng is not None:
        stops_with_distance = []
        for stop in stops:
            distance = haversine_distance(
                lat, lng, 
                float(stop.latitude), float(stop.longitude)
            )
            if distance <= radius:
                stops_with_distance.append({
                    "stop": stop,
                    "distance_km": round(distance, 2)
                })
        
        # Sort by distance
        stops_with_distance.sort(key=lambda x: x["distance_km"])
        
        return {
            "stops": [item["stop"] for item in stops_with_distance],
            "distances": [item["distance_km"] for item in stops_with_distance],
            "total": len(stops_with_distance),
            "skip": skip,
            "limit": limit,
            "search_center": {"lat": lat, "lng": lng, "radius_km": radius}
        }
    
    return {
        "stops": stops,
        "total": total_count,
        "skip": skip,
        "limit": limit,
        "has_more": skip + limit < total_count
    }

@router.get("/{stop_id}", response_model=StopResponse)
def get_stop(stop_id: int, db: Session = Depends(get_db)):
    """Get a specific stop by ID"""
    stop = db.query(Stop).filter(Stop.id == stop_id).first()
    if not stop:
        raise HTTPException(status_code=404, detail="Stop not found")
    return stop

@router.get("/{stop_id}/routes", response_model=dict)
def get_stop_routes(
    stop_id: int,
    active_only: bool = Query(True, description="Filter only active routes"),
    db: Session = Depends(get_db)
):
    """
    Get all routes that serve a specific stop
    
    - **stop_id**: The ID of the stop
    - **active_only**: Whether to return only active routes
    """
    stop = db.query(Stop).options(joinedload(Stop.route)).filter(Stop.id == stop_id).first()
    if not stop:
        raise HTTPException(status_code=404, detail="Stop not found")
    
    # Get all routes that have this stop
    query = db.query(Route).join(Stop).filter(Stop.id == stop_id)
    
    if active_only:
        query = query.filter(Route.is_active == True)
    
    routes = query.all()
    
    return {
        "stop": {
            "id": stop.id,
            "name": stop.name,
            "name_kannada": stop.name_kannada,
            "latitude": stop.latitude,
            "longitude": stop.longitude
        },
        "routes": routes,
        "total_routes": len(routes)
    }

@router.get("/{stop_id}/arrivals")
async def get_stop_arrivals(
    stop_id: int, 
    max_arrivals: int = Query(10, ge=1, le=20, description="Maximum number of arrivals to return"),
    max_eta_minutes: int = Query(60, ge=5, le=120, description="Maximum ETA in minutes to include"),
    include_confidence: bool = Query(False, description="Include ETA confidence metrics"),
    db: Session = Depends(get_db)
):
    """
    Get upcoming bus arrivals for a stop with real-time ETA calculations
    
    - **stop_id**: The ID of the stop
    - **max_arrivals**: Maximum number of arrivals to return
    - **max_eta_minutes**: Maximum ETA in minutes to include in results
    - **include_confidence**: Include detailed confidence metrics for ETAs
    """
    stop = db.query(Stop).filter(Stop.id == stop_id).first()
    if not stop:
        raise HTTPException(status_code=404, detail="Stop not found")
    
    # Get active buses on the same route as this stop
    active_buses = db.query(Vehicle).join(Trip).filter(
        and_(
            Trip.route_id == stop.route_id,
            Trip.status == "active",
            Vehicle.status == VehicleStatus.ACTIVE
        )
    ).all()
    
    # Calculate ETAs for all active buses
    arrivals = []
    if active_buses:
        # Prepare vehicle-stop pairs for batch ETA calculation
        vehicle_stop_pairs = [(bus.id, stop_id) for bus in active_buses]
        eta_results = await eta_cache_service.get_multiple_etas(vehicle_stop_pairs)
        
        for bus in active_buses:
            eta_result = eta_results.get((bus.id, stop_id))
            
            if eta_result and eta_result.eta_minutes <= max_eta_minutes:
                # Get current trip info
                current_trip = db.query(Trip).filter(
                    and_(Trip.vehicle_id == bus.id, Trip.status == "active")
                ).first()
                
                # Mock occupancy data
                import random
                occupancy_percentage = random.randint(20, 95)
                if occupancy_percentage < 30:
                    occupancy_level = "low"
                elif occupancy_percentage < 70:
                    occupancy_level = "medium"
                else:
                    occupancy_level = "high"
                
                arrival_info = {
                    "vehicle_id": bus.id,
                    "vehicle_number": bus.vehicle_number,
                    "route_name": current_trip.route.name if current_trip and current_trip.route else "Unknown Route",
                    "route_number": current_trip.route.route_number if current_trip and current_trip.route else "Unknown",
                    "eta": {
                        "seconds": eta_result.eta_seconds,
                        "minutes": round(eta_result.eta_minutes, 1),
                        "formatted": f"{eta_result.eta_seconds // 60}m {eta_result.eta_seconds % 60}s",
                        "arrival_time": (datetime.now() + timedelta(seconds=eta_result.eta_seconds)).isoformat()
                    },
                    "occupancy": {
                        "level": occupancy_level,
                        "percentage": occupancy_percentage
                    },
                    "distance_meters": round(eta_result.distance_meters),
                    "calculation_method": eta_result.calculation_method,
                    "calculated_at": eta_result.calculated_at.isoformat()
                }
                
                if include_confidence:
                    confidence_info = await eta_cache_service.get_eta_confidence_score(eta_result)
                    arrival_info["confidence"] = confidence_info
                
                arrivals.append(arrival_info)
    
    # Sort by ETA (shortest first)
    arrivals.sort(key=lambda x: x["eta"]["seconds"])
    
    # Limit results
    arrivals = arrivals[:max_arrivals]
    
    return {
        "stop": {
            "id": stop.id,
            "name": stop.name,
            "name_kannada": stop.name_kannada,
            "latitude": float(stop.latitude),
            "longitude": float(stop.longitude),
            "route_id": stop.route_id,
            "route_name": stop.route.name if stop.route else None
        },
        "arrivals": arrivals,
        "total_arrivals": len(arrivals),
        "calculated_at": datetime.now().isoformat(),
        "filters": {
            "max_arrivals": max_arrivals,
            "max_eta_minutes": max_eta_minutes
        }
    }

@router.get("/{stop_id}/eta")
async def get_stop_eta_for_all_buses(
    stop_id: int,
    max_eta_minutes: int = Query(30, ge=5, le=120, description="Maximum ETA in minutes"),
    include_confidence: bool = Query(False, description="Include confidence metrics"),
    db: Session = Depends(get_db)
):
    """
    Get ETA for all buses that serve this stop
    
    - **stop_id**: The ID of the stop
    - **max_eta_minutes**: Maximum ETA in minutes to include
    - **include_confidence**: Include detailed confidence metrics
    """
    stop = db.query(Stop).filter(Stop.id == stop_id).first()
    if not stop:
        raise HTTPException(status_code=404, detail="Stop not found")
    
    # Get all active buses that could potentially serve this stop
    # This includes buses on the same route and nearby buses on connecting routes
    
    # Primary: buses on the same route
    same_route_buses = db.query(Vehicle).join(Trip).filter(
        and_(
            Trip.route_id == stop.route_id,
            Trip.status == "active",
            Vehicle.status == VehicleStatus.ACTIVE
        )
    ).all()
    
    # Secondary: nearby buses on other routes (within reasonable distance)
    # For simplicity, we'll focus on same-route buses for now
    all_buses = same_route_buses
    
    if not all_buses:
        return {
            "stop": {
                "id": stop.id,
                "name": stop.name,
                "name_kannada": stop.name_kannada
            },
            "etas": [],
            "message": "No active buses found for this stop"
        }
    
    # Calculate ETAs
    vehicle_stop_pairs = [(bus.id, stop_id) for bus in all_buses]
    eta_results = await eta_cache_service.get_multiple_etas(vehicle_stop_pairs)
    
    # Build response
    etas = []
    for bus in all_buses:
        eta_result = eta_results.get((bus.id, stop_id))
        
        if eta_result and eta_result.eta_minutes <= max_eta_minutes:
            # Get current trip
            current_trip = db.query(Trip).filter(
                and_(Trip.vehicle_id == bus.id, Trip.status == "active")
            ).first()
            
            eta_info = {
                "vehicle_id": bus.id,
                "vehicle_number": bus.vehicle_number,
                "route_name": current_trip.route.name if current_trip and current_trip.route else "Unknown",
                "route_number": current_trip.route.route_number if current_trip and current_trip.route else "Unknown",
                "eta": {
                    "seconds": eta_result.eta_seconds,
                    "minutes": round(eta_result.eta_minutes, 1),
                    "formatted": f"{eta_result.eta_seconds // 60}m {eta_result.eta_seconds % 60}s"
                },
                "distance_meters": round(eta_result.distance_meters),
                "calculation_method": eta_result.calculation_method
            }
            
            if include_confidence:
                confidence_info = await eta_cache_service.get_eta_confidence_score(eta_result)
                eta_info["confidence"] = confidence_info
            
            etas.append(eta_info)
    
    # Sort by ETA
    etas.sort(key=lambda x: x["eta"]["seconds"])
    
    return {
        "stop": {
            "id": stop.id,
            "name": stop.name,
            "name_kannada": stop.name_kannada,
            "latitude": float(stop.latitude),
            "longitude": float(stop.longitude)
        },
        "etas": etas,
        "total_buses": len(etas),
        "calculated_at": datetime.now().isoformat()
    }

@router.get("/search", response_model=dict)
def search_stops(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results"),
    include_route: bool = Query(True, description="Include route information"),
    lat: Optional[float] = Query(None, description="User latitude for distance calculation"),
    lng: Optional[float] = Query(None, description="User longitude for distance calculation"),
    max_distance_km: Optional[float] = Query(None, ge=0.1, le=50.0, description="Maximum distance in km"),
    db: Session = Depends(get_db)
):
    """
    Search stops with fuzzy matching on name (English and Kannada)
    
    - **q**: Search query (minimum 1 character)
    - **limit**: Maximum number of results to return
    - **include_route**: Whether to include route information
    - **lat**: User latitude for distance-based sorting
    - **lng**: User longitude for distance-based sorting
    - **max_distance_km**: Maximum distance to include results (requires lat/lng)
    """
    query = db.query(Stop)
    
    if include_route:
        query = query.options(joinedload(Stop.route))
    
    # Fuzzy search with different matching strategies
    search_term = f"%{q}%"
    exact_match = q.lower()
    
    # Search in both English and Kannada names
    stops = query.filter(
        or_(
            Stop.name.ilike(search_term),
            Stop.name_kannada.ilike(search_term)
        )
    ).all()
    
    # Score and sort results by relevance
    scored_stops = []
    for stop in stops:
        score = 0
        stop_name_lower = stop.name.lower()
        stop_name_kannada_lower = (stop.name_kannada or "").lower()
        
        # Exact matches get highest score
        if exact_match == stop_name_lower or exact_match == stop_name_kannada_lower:
            score += 100
        # Starts with query gets high score
        elif stop_name_lower.startswith(exact_match) or stop_name_kannada_lower.startswith(exact_match):
            score += 50
        # Contains query gets medium score
        elif exact_match in stop_name_lower or exact_match in stop_name_kannada_lower:
            score += 25
        
        # Shorter names get slight boost for relevance
        score += max(0, 50 - len(stop.name))
        
        stop_data = {
            "id": stop.id,
            "name": stop.name,
            "name_kannada": stop.name_kannada,
            "latitude": float(stop.latitude),
            "longitude": float(stop.longitude),
            "stop_order": stop.stop_order,
            "score": score
        }
        
        # Calculate distance if user location provided
        if lat is not None and lng is not None:
            distance = haversine_distance(
                lat, lng, 
                float(stop.latitude), float(stop.longitude)
            )
            stop_data["distance_km"] = round(distance, 2)
            
            # Skip if beyond max distance
            if max_distance_km and distance > max_distance_km:
                continue
            
            # Boost score for nearby stops
            if distance < 0.5:  # Within 500m
                score += 30
            elif distance < 1.0:  # Within 1km
                score += 15
            elif distance < 2.0:  # Within 2km
                score += 5
        
        if include_route and stop.route:
            stop_data["route"] = {
                "id": stop.route.id,
                "name": stop.route.name,
                "route_number": stop.route.route_number,
                "is_active": stop.route.is_active
            }
        
        stop_data["score"] = score
        scored_stops.append(stop_data)
    
    # Sort by score (highest first), then by distance if available
    if lat is not None and lng is not None:
        scored_stops.sort(key=lambda x: (-x["score"], x.get("distance_km", float('inf'))))
    else:
        scored_stops.sort(key=lambda x: x["score"], reverse=True)
    
    # Limit results
    results = scored_stops[:limit]
    
    return {
        "query": q,
        "results": results,
        "total": len(results),
        "has_more": len(scored_stops) > limit,
        "user_location": {"lat": lat, "lng": lng} if lat and lng else None
    }