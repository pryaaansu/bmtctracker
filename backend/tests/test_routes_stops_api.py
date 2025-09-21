"""
Tests for routes and stops API endpoints
"""

import pytest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from main import app
from app.models.route import Route
from app.models.stop import Stop
from app.core.database import get_db

client = TestClient(app)

@pytest.fixture
def test_routes_and_stops(db_session: Session):
    """Create test routes and stops"""
    # Create test routes
    routes = []
    for i in range(3):
        route = Route(
            name=f"Test Route {i+1}",
            route_number=f"TR{i+1:03d}",
            geojson=f'{{"type": "LineString", "coordinates": [[77.{5946+i}, 12.{9716+i}], [77.{6046+i}, 12.{9816+i}]]}}',
            polyline=f"test_polyline_{i}",
            is_active=i < 2  # First two routes are active
        )
        db_session.add(route)
        routes.append(route)
    
    db_session.flush()
    
    # Create test stops for each route
    stops = []
    for route_idx, route in enumerate(routes):
        for stop_idx in range(4):  # 4 stops per route
            stop = Stop(
                route_id=route.id,
                name=f"Stop {stop_idx+1} Route {route_idx+1}",
                name_kannada=f"ನಿಲ್ದಾಣ {stop_idx+1} ಮಾರ್ಗ {route_idx+1}",
                latitude=12.9716 + (route_idx * 0.01) + (stop_idx * 0.002),
                longitude=77.5946 + (route_idx * 0.01) + (stop_idx * 0.002),
                stop_order=stop_idx + 1
            )
            db_session.add(stop)
            stops.append(stop)
    
    db_session.commit()
    return routes, stops

def test_get_routes_basic(test_routes_and_stops):
    """Test basic routes endpoint"""
    routes, stops = test_routes_and_stops
    
    response = client.get("/api/v1/routes/")
    assert response.status_code == 200
    
    data = response.json()
    assert "routes" in data
    assert "total" in data
    assert "skip" in data
    assert "limit" in data
    assert "has_more" in data
    
    # Should return only active routes by default
    assert len(data["routes"]) == 2
    
    # Check route structure
    route = data["routes"][0]
    assert "id" in route
    assert "name" in route
    assert "route_number" in route
    assert "geojson" in route
    assert "polyline" in route
    assert "is_active" in route
    assert "created_at" in route

def test_get_routes_with_filters(test_routes_and_stops):
    """Test routes endpoint with filters"""
    routes, stops = test_routes_and_stops
    
    # Test search filter
    response = client.get("/api/v1/routes/?search=Route 1")
    assert response.status_code == 200
    data = response.json()
    assert len(data["routes"]) == 1
    assert "Route 1" in data["routes"][0]["name"]
    
    # Test route number search
    response = client.get("/api/v1/routes/?search=TR001")
    assert response.status_code == 200
    data = response.json()
    assert len(data["routes"]) == 1
    assert data["routes"][0]["route_number"] == "TR001"
    
    # Test include inactive routes
    response = client.get("/api/v1/routes/?active_only=false")
    assert response.status_code == 200
    data = response.json()
    assert len(data["routes"]) == 3
    
    # Test specific route numbers filter
    response = client.get("/api/v1/routes/?route_numbers=TR001,TR002")
    assert response.status_code == 200
    data = response.json()
    assert len(data["routes"]) == 2
    route_numbers = [r["route_number"] for r in data["routes"]]
    assert "TR001" in route_numbers
    assert "TR002" in route_numbers

def test_get_routes_pagination(test_routes_and_stops):
    """Test routes pagination"""
    routes, stops = test_routes_and_stops
    
    # Test limit
    response = client.get("/api/v1/routes/?limit=1&active_only=false")
    assert response.status_code == 200
    data = response.json()
    assert len(data["routes"]) == 1
    assert data["has_more"] == True
    
    # Test skip
    response = client.get("/api/v1/routes/?skip=1&limit=1&active_only=false")
    assert response.status_code == 200
    data = response.json()
    assert len(data["routes"]) == 1
    assert data["skip"] == 1

def test_get_route_by_id(test_routes_and_stops):
    """Test get specific route by ID"""
    routes, stops = test_routes_and_stops
    route_id = routes[0].id
    
    response = client.get(f"/api/v1/routes/{route_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["id"] == route_id
    assert "name" in data
    assert "route_number" in data

def test_get_route_stops(test_routes_and_stops):
    """Test get stops for a specific route"""
    routes, stops = test_routes_and_stops
    route_id = routes[0].id
    
    response = client.get(f"/api/v1/routes/{route_id}/stops")
    assert response.status_code == 200
    
    data = response.json()
    assert "route_id" in data
    assert "stops" in data
    assert "total_stops" in data
    assert data["route_id"] == route_id
    assert len(data["stops"]) == 4
    
    # Check stops are ordered correctly
    stops_data = data["stops"]
    for i in range(len(stops_data) - 1):
        assert stops_data[i]["stop_order"] <= stops_data[i + 1]["stop_order"]

def test_get_route_stops_with_info(test_routes_and_stops):
    """Test get route stops with route information"""
    routes, stops = test_routes_and_stops
    route_id = routes[0].id
    
    response = client.get(f"/api/v1/routes/{route_id}/stops?include_route_info=true")
    assert response.status_code == 200
    
    data = response.json()
    assert "route" in data
    route_info = data["route"]
    assert route_info["id"] == route_id
    assert "name" in route_info
    assert "route_number" in route_info

def test_get_stops_basic(test_routes_and_stops):
    """Test basic stops endpoint"""
    routes, stops = test_routes_and_stops
    
    response = client.get("/api/v1/stops/")
    assert response.status_code == 200
    
    data = response.json()
    assert "stops" in data
    assert "total" in data
    assert "skip" in data
    assert "limit" in data
    assert "has_more" in data
    
    # Should return all stops
    assert len(data["stops"]) == 12  # 3 routes * 4 stops each
    
    # Check stop structure
    stop = data["stops"][0]
    assert "id" in stop
    assert "name" in stop
    assert "name_kannada" in stop
    assert "latitude" in stop
    assert "longitude" in stop
    assert "stop_order" in stop
    assert "route_id" in stop

def test_get_stops_with_search(test_routes_and_stops):
    """Test stops endpoint with search"""
    routes, stops = test_routes_and_stops
    
    # Test English name search
    response = client.get("/api/v1/stops/?search=Stop 1")
    assert response.status_code == 200
    data = response.json()
    assert len(data["stops"]) == 3  # One "Stop 1" per route
    
    # Test Kannada name search
    response = client.get("/api/v1/stops/?search=ನಿಲ್ದಾಣ")
    assert response.status_code == 200
    data = response.json()
    assert len(data["stops"]) == 12  # All stops have Kannada names

def test_get_stops_by_route(test_routes_and_stops):
    """Test stops filtered by route"""
    routes, stops = test_routes_and_stops
    route_id = routes[0].id
    
    # Test by route ID
    response = client.get(f"/api/v1/stops/?route_id={route_id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data["stops"]) == 4
    assert all(stop["route_id"] == route_id for stop in data["stops"])
    
    # Test by route number
    route_number = routes[0].route_number
    response = client.get(f"/api/v1/stops/?route_number={route_number}")
    assert response.status_code == 200
    data = response.json()
    assert len(data["stops"]) == 4

def test_get_stops_geospatial_search(test_routes_and_stops):
    """Test stops geospatial search"""
    routes, stops = test_routes_and_stops
    
    # Search near the first stop
    lat, lng = 12.9716, 77.5946
    response = client.get(f"/api/v1/stops/?lat={lat}&lng={lng}&radius=1.0")
    assert response.status_code == 200
    
    data = response.json()
    assert "stops" in data
    assert "distances" in data
    assert "search_center" in data
    
    # Should find nearby stops
    assert len(data["stops"]) > 0
    assert len(data["distances"]) == len(data["stops"])
    
    # Check search center info
    search_center = data["search_center"]
    assert search_center["lat"] == lat
    assert search_center["lng"] == lng
    assert search_center["radius_km"] == 1.0
    
    # Distances should be sorted
    distances = data["distances"]
    for i in range(len(distances) - 1):
        assert distances[i] <= distances[i + 1]

def test_get_stops_geospatial_with_filters(test_routes_and_stops):
    """Test geospatial search with other filters"""
    routes, stops = test_routes_and_stops
    route_id = routes[0].id
    
    # Combine geospatial search with route filter
    lat, lng = 12.9716, 77.5946
    response = client.get(f"/api/v1/stops/?lat={lat}&lng={lng}&radius=2.0&route_id={route_id}")
    assert response.status_code == 200
    
    data = response.json()
    # Should only return stops from the specified route
    assert all(stop["route_id"] == route_id for stop in data["stops"])

def test_get_stop_by_id(test_routes_and_stops):
    """Test get specific stop by ID"""
    routes, stops = test_routes_and_stops
    stop_id = stops[0].id
    
    response = client.get(f"/api/v1/stops/{stop_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["id"] == stop_id
    assert "name" in data
    assert "latitude" in data
    assert "longitude" in data

def test_get_stop_routes(test_routes_and_stops):
    """Test get routes that serve a specific stop"""
    routes, stops = test_routes_and_stops
    stop_id = stops[0].id  # First stop of first route
    
    response = client.get(f"/api/v1/stops/{stop_id}/routes")
    assert response.status_code == 200
    
    data = response.json()
    assert "stop" in data
    assert "routes" in data
    assert "total_routes" in data
    
    # Should return the route that serves this stop
    assert len(data["routes"]) == 1
    assert data["routes"][0]["id"] == routes[0].id

def test_get_stop_arrivals(test_routes_and_stops):
    """Test get arrivals for a specific stop"""
    routes, stops = test_routes_and_stops
    stop_id = stops[0].id
    
    response = client.get(f"/api/v1/stops/{stop_id}/arrivals")
    assert response.status_code == 200
    
    data = response.json()
    assert "stop" in data
    assert "arrivals" in data
    
    # Check mock arrivals structure
    arrivals = data["arrivals"]
    assert len(arrivals) > 0
    arrival = arrivals[0]
    assert "bus_number" in arrival
    assert "route_name" in arrival
    assert "eta_minutes" in arrival
    assert "occupancy" in arrival

def test_nonexistent_routes_stops(test_routes_and_stops):
    """Test endpoints with non-existent IDs"""
    # Non-existent route
    response = client.get("/api/v1/routes/99999")
    assert response.status_code == 404
    
    response = client.get("/api/v1/routes/99999/stops")
    assert response.status_code == 404
    
    # Non-existent stop
    response = client.get("/api/v1/stops/99999")
    assert response.status_code == 404
    
    response = client.get("/api/v1/stops/99999/routes")
    assert response.status_code == 404
    
    response = client.get("/api/v1/stops/99999/arrivals")
    assert response.status_code == 404

def test_api_parameter_validation():
    """Test API parameter validation"""
    # Test invalid pagination parameters
    response = client.get("/api/v1/routes/?skip=-1")
    assert response.status_code == 422
    
    response = client.get("/api/v1/routes/?limit=0")
    assert response.status_code == 422
    
    response = client.get("/api/v1/routes/?limit=1000")
    assert response.status_code == 422
    
    # Test invalid geospatial parameters
    response = client.get("/api/v1/stops/?lat=invalid")
    assert response.status_code == 422
    
    response = client.get("/api/v1/stops/?lat=12.9716&lng=77.5946&radius=-1")
    assert response.status_code == 422
    
    response = client.get("/api/v1/stops/?lat=12.9716&lng=77.5946&radius=100")
    assert response.status_code == 422

def test_haversine_distance_calculation():
    """Test the haversine distance calculation function"""
    from app.api.v1.endpoints.stops import haversine_distance
    
    # Test same point
    distance = haversine_distance(12.9716, 77.5946, 12.9716, 77.5946)
    assert distance == 0.0
    
    # Test known distance (approximately)
    # Distance between Bangalore and Mysore is roughly 150km
    bangalore_lat, bangalore_lng = 12.9716, 77.5946
    mysore_lat, mysore_lng = 12.2958, 76.6394
    
    distance = haversine_distance(bangalore_lat, bangalore_lng, mysore_lat, mysore_lng)
    assert 140 < distance < 160  # Approximate range
    
    # Test distance is symmetric
    distance1 = haversine_distance(12.9716, 77.5946, 12.9816, 77.6046)
    distance2 = haversine_distance(12.9816, 77.6046, 12.9716, 77.5946)
    assert abs(distance1 - distance2) < 0.001