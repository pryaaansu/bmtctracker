from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from typing import Optional
from ....core.database import get_db
from ....models.route import Route
from ....models.stop import Stop
from math import radians, cos, sin, asin, sqrt

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

@router.get("/autocomplete")
def autocomplete_search(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(8, ge=1, le=20, description="Maximum number of suggestions"),
    include_routes: bool = Query(True, description="Include routes in suggestions"),
    include_stops: bool = Query(True, description="Include stops in suggestions"),
    lat: Optional[float] = Query(None, description="User latitude for distance-based sorting"),
    lng: Optional[float] = Query(None, description="User longitude for distance-based sorting"),
    db: Session = Depends(get_db)
):
    """
    Autocomplete search for routes and stops with fuzzy matching
    
    - **q**: Search query (minimum 1 character)
    - **limit**: Maximum number of suggestions to return
    - **include_routes**: Whether to include routes in suggestions
    - **include_stops**: Whether to include stops in suggestions
    - **lat**: User latitude for distance-based sorting
    - **lng**: User longitude for distance-based sorting
    """
    suggestions = []
    search_term = f"%{q}%"
    exact_match = q.lower()
    
    # Search routes
    if include_routes:
        routes = db.query(Route).filter(
            Route.is_active == True,
            or_(
                Route.name.ilike(search_term),
                Route.route_number.ilike(search_term)
            )
        ).limit(limit // 2 if include_stops else limit).all()
        
        for route in routes:
            score = 0
            route_name_lower = route.name.lower()
            route_number_lower = route.route_number.lower()
            
            # Scoring logic
            if exact_match == route_name_lower or exact_match == route_number_lower:
                score += 100
            elif route_name_lower.startswith(exact_match) or route_number_lower.startswith(exact_match):
                score += 50
            elif exact_match in route_name_lower or exact_match in route_number_lower:
                score += 25
            
            suggestions.append({
                "type": "route",
                "id": route.id,
                "title": route.name,
                "subtitle": f"Route {route.route_number}",
                "route_number": route.route_number,
                "score": score,
                "icon": "route"
            })
    
    # Search stops
    if include_stops:
        stops_query = db.query(Stop).options(joinedload(Stop.route)).filter(
            or_(
                Stop.name.ilike(search_term),
                Stop.name_kannada.ilike(search_term)
            )
        )
        
        stops = stops_query.limit(limit // 2 if include_routes else limit).all()
        
        for stop in stops:
            score = 0
            stop_name_lower = stop.name.lower()
            stop_name_kannada_lower = (stop.name_kannada or "").lower()
            
            # Scoring logic
            if exact_match == stop_name_lower or exact_match == stop_name_kannada_lower:
                score += 100
            elif stop_name_lower.startswith(exact_match) or stop_name_kannada_lower.startswith(exact_match):
                score += 50
            elif exact_match in stop_name_lower or exact_match in stop_name_kannada_lower:
                score += 25
            
            # Calculate distance if user location provided
            distance_km = None
            if lat is not None and lng is not None:
                distance_km = haversine_distance(
                    lat, lng, 
                    float(stop.latitude), float(stop.longitude)
                )
                
                # Boost score for nearby stops
                if distance_km < 0.5:  # Within 500m
                    score += 30
                elif distance_km < 1.0:  # Within 1km
                    score += 15
                elif distance_km < 2.0:  # Within 2km
                    score += 5
            
            subtitle = stop.route.name if stop.route else "Bus Stop"
            if distance_km is not None:
                if distance_km < 1:
                    subtitle += f" • {int(distance_km * 1000)}m away"
                else:
                    subtitle += f" • {distance_km:.1f}km away"
            
            suggestions.append({
                "type": "stop",
                "id": stop.id,
                "title": stop.name,
                "title_kannada": stop.name_kannada,
                "subtitle": subtitle,
                "latitude": float(stop.latitude),
                "longitude": float(stop.longitude),
                "route_id": stop.route_id,
                "route_name": stop.route.name if stop.route else None,
                "route_number": stop.route.route_number if stop.route else None,
                "distance_km": round(distance_km, 2) if distance_km else None,
                "score": score,
                "icon": "stop"
            })
    
    # Sort by score (highest first), then by distance if available
    if lat is not None and lng is not None:
        suggestions.sort(key=lambda x: (-x["score"], x.get("distance_km", float('inf'))))
    else:
        suggestions.sort(key=lambda x: x["score"], reverse=True)
    
    # Limit final results
    suggestions = suggestions[:limit]
    
    return {
        "query": q,
        "suggestions": suggestions,
        "total": len(suggestions),
        "user_location": {"lat": lat, "lng": lng} if lat and lng else None
    }

@router.get("/")
def global_search(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results"),
    type_filter: Optional[str] = Query(None, regex="^(routes|stops|all)$", description="Filter by type: routes, stops, or all"),
    lat: Optional[float] = Query(None, description="User latitude for distance-based sorting"),
    lng: Optional[float] = Query(None, description="User longitude for distance-based sorting"),
    max_distance_km: Optional[float] = Query(None, ge=0.1, le=50.0, description="Maximum distance in km for stops"),
    db: Session = Depends(get_db)
):
    """
    Global search across routes and stops with detailed results
    
    - **q**: Search query (minimum 1 character)
    - **limit**: Maximum number of results to return
    - **type_filter**: Filter results by type (routes, stops, or all)
    - **lat**: User latitude for distance-based sorting
    - **lng**: User longitude for distance-based sorting
    - **max_distance_km**: Maximum distance to include stops (requires lat/lng)
    """
    results = {
        "routes": [],
        "stops": []
    }
    
    search_term = f"%{q}%"
    exact_match = q.lower()
    
    # Search routes
    if type_filter in [None, "all", "routes"]:
        routes = db.query(Route).filter(
            Route.is_active == True,
            or_(
                Route.name.ilike(search_term),
                Route.route_number.ilike(search_term)
            )
        ).all()
        
        for route in routes:
            score = 0
            route_name_lower = route.name.lower()
            route_number_lower = route.route_number.lower()
            
            # Scoring logic
            if exact_match == route_name_lower or exact_match == route_number_lower:
                score += 100
            elif route_name_lower.startswith(exact_match) or route_number_lower.startswith(exact_match):
                score += 50
            elif exact_match in route_name_lower or exact_match in route_number_lower:
                score += 25
            
            # Get stop count
            stop_count = db.query(Stop).filter(Stop.route_id == route.id).count()
            
            results["routes"].append({
                "id": route.id,
                "name": route.name,
                "route_number": route.route_number,
                "is_active": route.is_active,
                "stop_count": stop_count,
                "score": score,
                "created_at": route.created_at
            })
    
    # Search stops
    if type_filter in [None, "all", "stops"]:
        stops_query = db.query(Stop).options(joinedload(Stop.route)).filter(
            or_(
                Stop.name.ilike(search_term),
                Stop.name_kannada.ilike(search_term)
            )
        )
        
        stops = stops_query.all()
        
        for stop in stops:
            score = 0
            stop_name_lower = stop.name.lower()
            stop_name_kannada_lower = (stop.name_kannada or "").lower()
            
            # Scoring logic
            if exact_match == stop_name_lower or exact_match == stop_name_kannada_lower:
                score += 100
            elif stop_name_lower.startswith(exact_match) or stop_name_kannada_lower.startswith(exact_match):
                score += 50
            elif exact_match in stop_name_lower or exact_match in stop_name_kannada_lower:
                score += 25
            
            # Calculate distance if user location provided
            distance_km = None
            if lat is not None and lng is not None:
                distance_km = haversine_distance(
                    lat, lng, 
                    float(stop.latitude), float(stop.longitude)
                )
                
                # Skip if beyond max distance
                if max_distance_km and distance_km > max_distance_km:
                    continue
                
                # Boost score for nearby stops
                if distance_km < 0.5:  # Within 500m
                    score += 30
                elif distance_km < 1.0:  # Within 1km
                    score += 15
                elif distance_km < 2.0:  # Within 2km
                    score += 5
            
            stop_data = {
                "id": stop.id,
                "name": stop.name,
                "name_kannada": stop.name_kannada,
                "latitude": float(stop.latitude),
                "longitude": float(stop.longitude),
                "stop_order": stop.stop_order,
                "score": score
            }
            
            if distance_km is not None:
                stop_data["distance_km"] = round(distance_km, 2)
            
            if stop.route:
                stop_data["route"] = {
                    "id": stop.route.id,
                    "name": stop.route.name,
                    "route_number": stop.route.route_number,
                    "is_active": stop.route.is_active
                }
            
            results["stops"].append(stop_data)
    
    # Sort results by score
    results["routes"].sort(key=lambda x: x["score"], reverse=True)
    
    if lat is not None and lng is not None:
        results["stops"].sort(key=lambda x: (-x["score"], x.get("distance_km", float('inf'))))
    else:
        results["stops"].sort(key=lambda x: x["score"], reverse=True)
    
    # Apply limit across all results
    total_results = len(results["routes"]) + len(results["stops"])
    if total_results > limit:
        # Distribute limit proportionally
        route_limit = min(len(results["routes"]), limit // 2)
        stop_limit = min(len(results["stops"]), limit - route_limit)
        
        results["routes"] = results["routes"][:route_limit]
        results["stops"] = results["stops"][:stop_limit]
    
    return {
        "query": q,
        "results": results,
        "total": {
            "routes": len(results["routes"]),
            "stops": len(results["stops"]),
            "all": len(results["routes"]) + len(results["stops"])
        },
        "has_more": total_results > limit,
        "user_location": {"lat": lat, "lng": lng} if lat and lng else None,
        "filters": {
            "type": type_filter,
            "max_distance_km": max_distance_km
        }
    }