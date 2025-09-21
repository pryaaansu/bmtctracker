from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, func, and_
from typing import List, Optional
from ....core.database import get_db
from ....models.route import Route
from ....models.stop import Stop
from ....schemas.route import RouteResponse

router = APIRouter()

@router.get("/", response_model=dict)
def get_routes(
    skip: int = Query(0, ge=0, description="Number of routes to skip"),
    limit: int = Query(100, ge=1, le=500, description="Number of routes to return"),
    search: Optional[str] = Query(None, description="Search routes by name or route number"),
    active_only: bool = Query(True, description="Filter only active routes"),
    route_numbers: Optional[str] = Query(None, description="Comma-separated list of route numbers to filter"),
    db: Session = Depends(get_db)
):
    """
    Get routes with filtering and pagination
    
    - **skip**: Number of routes to skip (for pagination)
    - **limit**: Maximum number of routes to return
    - **search**: Search term to filter routes by name or route number
    - **active_only**: Whether to return only active routes
    - **route_numbers**: Comma-separated route numbers to filter by
    """
    query = db.query(Route)
    
    # Filter by active status
    if active_only:
        query = query.filter(Route.is_active == True)
    
    # Search filter
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Route.name.ilike(search_term),
                Route.route_number.ilike(search_term)
            )
        )
    
    # Filter by specific route numbers
    if route_numbers:
        route_number_list = [rn.strip() for rn in route_numbers.split(",")]
        query = query.filter(Route.route_number.in_(route_number_list))
    
    # Get total count for pagination
    total_count = query.count()
    
    # Apply pagination
    routes = query.offset(skip).limit(limit).all()
    
    return {
        "routes": routes,
        "total": total_count,
        "skip": skip,
        "limit": limit,
        "has_more": skip + limit < total_count
    }

@router.get("/{route_id}", response_model=RouteResponse)
def get_route(route_id: int, db: Session = Depends(get_db)):
    """Get a specific route by ID"""
    route = db.query(Route).filter(Route.id == route_id).first()
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    return route

@router.get("/{route_id}/stops", response_model=dict)
def get_route_stops(
    route_id: int, 
    include_route_info: bool = Query(False, description="Include route information in response"),
    db: Session = Depends(get_db)
):
    """
    Get all stops for a specific route, ordered by stop sequence
    
    - **route_id**: The ID of the route
    - **include_route_info**: Whether to include route details in the response
    """
    route = db.query(Route).options(joinedload(Route.stops)).filter(Route.id == route_id).first()
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    
    # Sort stops by their order on the route
    stops = sorted(route.stops, key=lambda x: x.stop_order)
    
    response = {
        "route_id": route_id,
        "stops": stops,
        "total_stops": len(stops)
    }
    
    if include_route_info:
        response["route"] = {
            "id": route.id,
            "name": route.name,
            "route_number": route.route_number,
            "is_active": route.is_active,
            "created_at": route.created_at
        }
    
    return response

@router.get("/search", response_model=dict)
def search_routes(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results"),
    include_stops: bool = Query(False, description="Include stops in search results"),
    active_only: bool = Query(True, description="Filter only active routes"),
    db: Session = Depends(get_db)
):
    """
    Search routes with fuzzy matching on name and route number
    
    - **q**: Search query (minimum 1 character)
    - **limit**: Maximum number of results to return
    - **include_stops**: Whether to include stop information
    - **active_only**: Whether to return only active routes
    """
    query = db.query(Route)
    
    if active_only:
        query = query.filter(Route.is_active == True)
    
    # Fuzzy search with different matching strategies
    search_term = f"%{q}%"
    exact_match = q.lower()
    
    # Priority scoring for better relevance
    routes = query.filter(
        or_(
            Route.name.ilike(search_term),
            Route.route_number.ilike(search_term)
        )
    ).all()
    
    # Score and sort results by relevance
    scored_routes = []
    for route in routes:
        score = 0
        route_name_lower = route.name.lower()
        route_number_lower = route.route_number.lower()
        
        # Exact matches get highest score
        if exact_match == route_name_lower or exact_match == route_number_lower:
            score += 100
        # Starts with query gets high score
        elif route_name_lower.startswith(exact_match) or route_number_lower.startswith(exact_match):
            score += 50
        # Contains query gets medium score
        elif exact_match in route_name_lower or exact_match in route_number_lower:
            score += 25
        
        # Shorter names get slight boost for relevance
        score += max(0, 50 - len(route.name))
        
        route_data = {
            "id": route.id,
            "name": route.name,
            "route_number": route.route_number,
            "is_active": route.is_active,
            "created_at": route.created_at,
            "score": score
        }
        
        if include_stops:
            stops = db.query(Stop).filter(Stop.route_id == route.id).order_by(Stop.stop_order).all()
            route_data["stops"] = stops
            route_data["total_stops"] = len(stops)
        
        scored_routes.append(route_data)
    
    # Sort by score (highest first) and limit results
    scored_routes.sort(key=lambda x: x["score"], reverse=True)
    results = scored_routes[:limit]
    
    return {
        "query": q,
        "results": results,
        "total": len(results),
        "has_more": len(scored_routes) > limit
    }