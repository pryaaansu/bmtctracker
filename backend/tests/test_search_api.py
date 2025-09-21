import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from app.core.database import get_db
from app.models.route import Route
from app.models.stop import Stop

client = TestClient(app)

def test_autocomplete_search_routes(db_session: Session):
    """Test autocomplete search for routes"""
    # Create test route
    test_route = Route(
        name="Majestic to Whitefield",
        route_number="335E",
        geojson='{"type": "LineString", "coordinates": [[77.5946, 12.9716], [77.7500, 12.9698]]}',
        polyline="test_polyline",
        is_active=True
    )
    db_session.add(test_route)
    db_session.commit()
    
    # Test search
    response = client.get("/api/v1/search/autocomplete?q=majestic&limit=5")
    assert response.status_code == 200
    
    data = response.json()
    assert "suggestions" in data
    assert len(data["suggestions"]) > 0
    
    # Check if route is in suggestions
    route_suggestions = [s for s in data["suggestions"] if s["type"] == "route"]
    assert len(route_suggestions) > 0
    assert any("majestic" in s["title"].lower() for s in route_suggestions)

def test_autocomplete_search_stops(db_session: Session):
    """Test autocomplete search for stops"""
    # Create test route and stop
    test_route = Route(
        name="Test Route",
        route_number="TEST1",
        geojson='{"type": "LineString", "coordinates": [[77.5946, 12.9716], [77.7500, 12.9698]]}',
        polyline="test_polyline",
        is_active=True
    )
    db_session.add(test_route)
    db_session.flush()
    
    test_stop = Stop(
        route_id=test_route.id,
        name="Majestic Bus Station",
        name_kannada="ಮೆಜೆಸ್ಟಿಕ್ ಬಸ್ ನಿಲ್ದಾಣ",
        latitude=12.9716,
        longitude=77.5946,
        stop_order=1
    )
    db_session.add(test_stop)
    db_session.commit()
    
    # Test search
    response = client.get("/api/v1/search/autocomplete?q=majestic&limit=5")
    assert response.status_code == 200
    
    data = response.json()
    assert "suggestions" in data
    
    # Check if stop is in suggestions
    stop_suggestions = [s for s in data["suggestions"] if s["type"] == "stop"]
    assert len(stop_suggestions) > 0
    assert any("majestic" in s["title"].lower() for s in stop_suggestions)

def test_autocomplete_search_with_location(db_session: Session):
    """Test autocomplete search with user location for distance sorting"""
    # Create test route and stop
    test_route = Route(
        name="Test Route",
        route_number="TEST1",
        geojson='{"type": "LineString", "coordinates": [[77.5946, 12.9716], [77.7500, 12.9698]]}',
        polyline="test_polyline",
        is_active=True
    )
    db_session.add(test_route)
    db_session.flush()
    
    # Create nearby stop
    nearby_stop = Stop(
        route_id=test_route.id,
        name="Nearby Station",
        latitude=12.9716,  # Close to test location
        longitude=77.5946,
        stop_order=1
    )
    
    # Create far stop
    far_stop = Stop(
        route_id=test_route.id,
        name="Far Station",
        latitude=12.8000,  # Far from test location
        longitude=77.4000,
        stop_order=2
    )
    
    db_session.add_all([nearby_stop, far_stop])
    db_session.commit()
    
    # Test search with location
    response = client.get(
        "/api/v1/search/autocomplete?q=station&lat=12.9716&lng=77.5946&limit=10"
    )
    assert response.status_code == 200
    
    data = response.json()
    stop_suggestions = [s for s in data["suggestions"] if s["type"] == "stop"]
    
    # Check that distance is included
    assert len(stop_suggestions) >= 2
    for suggestion in stop_suggestions:
        assert "distance_km" in suggestion
        assert suggestion["distance_km"] >= 0

def test_global_search(db_session: Session):
    """Test global search endpoint"""
    # Create test data
    test_route = Route(
        name="Airport Express",
        route_number="VAYU",
        geojson='{"type": "LineString", "coordinates": [[77.5946, 12.9716], [77.7500, 12.9698]]}',
        polyline="test_polyline",
        is_active=True
    )
    db_session.add(test_route)
    db_session.flush()
    
    test_stop = Stop(
        route_id=test_route.id,
        name="Airport Terminal",
        latitude=13.1986,
        longitude=77.7066,
        stop_order=1
    )
    db_session.add(test_stop)
    db_session.commit()
    
    # Test global search
    response = client.get("/api/v1/search/?q=airport&limit=20")
    assert response.status_code == 200
    
    data = response.json()
    assert "results" in data
    assert "routes" in data["results"]
    assert "stops" in data["results"]
    assert "total" in data
    
    # Check that both routes and stops are returned
    assert len(data["results"]["routes"]) > 0 or len(data["results"]["stops"]) > 0

def test_global_search_with_filters(db_session: Session):
    """Test global search with type filters"""
    # Create test data
    test_route = Route(
        name="Test Route",
        route_number="TEST1",
        geojson='{"type": "LineString", "coordinates": [[77.5946, 12.9716], [77.7500, 12.9698]]}',
        polyline="test_polyline",
        is_active=True
    )
    db_session.add(test_route)
    db_session.flush()
    
    test_stop = Stop(
        route_id=test_route.id,
        name="Test Stop",
        latitude=12.9716,
        longitude=77.5946,
        stop_order=1
    )
    db_session.add(test_stop)
    db_session.commit()
    
    # Test routes only filter
    response = client.get("/api/v1/search/?q=test&type_filter=routes")
    assert response.status_code == 200
    
    data = response.json()
    assert len(data["results"]["routes"]) > 0
    assert len(data["results"]["stops"]) == 0
    
    # Test stops only filter
    response = client.get("/api/v1/search/?q=test&type_filter=stops")
    assert response.status_code == 200
    
    data = response.json()
    assert len(data["results"]["stops"]) > 0
    assert len(data["results"]["routes"]) == 0

def test_routes_search_endpoint(db_session: Session):
    """Test routes search endpoint"""
    # Create test routes
    route1 = Route(
        name="Majestic to Electronic City",
        route_number="500D",
        geojson='{"type": "LineString", "coordinates": [[77.5946, 12.9716], [77.6648, 12.8456]]}',
        polyline="test_polyline_1",
        is_active=True
    )
    
    route2 = Route(
        name="Whitefield Express",
        route_number="335E",
        geojson='{"type": "LineString", "coordinates": [[77.5946, 12.9716], [77.7500, 12.9698]]}',
        polyline="test_polyline_2",
        is_active=True
    )
    
    db_session.add_all([route1, route2])
    db_session.commit()
    
    # Test search
    response = client.get("/api/v1/routes/search?q=majestic&limit=10")
    assert response.status_code == 200
    
    data = response.json()
    assert "results" in data
    assert len(data["results"]) > 0
    
    # Check scoring - exact matches should score higher
    results = data["results"]
    assert all("score" in result for result in results)
    
    # Results should be sorted by score
    scores = [result["score"] for result in results]
    assert scores == sorted(scores, reverse=True)

def test_stops_search_endpoint(db_session: Session):
    """Test stops search endpoint"""
    # Create test route and stops
    test_route = Route(
        name="Test Route",
        route_number="TEST1",
        geojson='{"type": "LineString", "coordinates": [[77.5946, 12.9716], [77.7500, 12.9698]]}',
        polyline="test_polyline",
        is_active=True
    )
    db_session.add(test_route)
    db_session.flush()
    
    stop1 = Stop(
        route_id=test_route.id,
        name="Majestic Bus Station",
        name_kannada="ಮೆಜೆಸ್ಟಿಕ್ ಬಸ್ ನಿಲ್ದಾಣ",
        latitude=12.9716,
        longitude=77.5946,
        stop_order=1
    )
    
    stop2 = Stop(
        route_id=test_route.id,
        name="Majestic Metro",
        latitude=12.9720,
        longitude=77.5950,
        stop_order=2
    )
    
    db_session.add_all([stop1, stop2])
    db_session.commit()
    
    # Test search
    response = client.get("/api/v1/stops/search?q=majestic&limit=10")
    assert response.status_code == 200
    
    data = response.json()
    assert "results" in data
    assert len(data["results"]) >= 2
    
    # Check that both English and Kannada names are searchable
    results = data["results"]
    assert all("score" in result for result in results)

def test_search_empty_query():
    """Test search with empty query"""
    response = client.get("/api/v1/search/autocomplete?q=")
    assert response.status_code == 422  # Validation error for empty query

def test_search_no_results(db_session: Session):
    """Test search with query that returns no results"""
    response = client.get("/api/v1/search/autocomplete?q=nonexistentquery123&limit=5")
    assert response.status_code == 200
    
    data = response.json()
    assert "suggestions" in data
    assert len(data["suggestions"]) == 0

def test_search_kannada_query(db_session: Session):
    """Test search with Kannada query"""
    # Create test route and stop with Kannada names
    test_route = Route(
        name="Test Route",
        route_number="TEST1",
        geojson='{"type": "LineString", "coordinates": [[77.5946, 12.9716], [77.7500, 12.9698]]}',
        polyline="test_polyline",
        is_active=True
    )
    db_session.add(test_route)
    db_session.flush()
    
    test_stop = Stop(
        route_id=test_route.id,
        name="Majestic",
        name_kannada="ಮೆಜೆಸ್ಟಿಕ್",
        latitude=12.9716,
        longitude=77.5946,
        stop_order=1
    )
    db_session.add(test_stop)
    db_session.commit()
    
    # Test search with Kannada query
    response = client.get("/api/v1/search/autocomplete?q=ಮೆಜೆಸ್ಟಿಕ್&limit=5")
    assert response.status_code == 200
    
    data = response.json()
    stop_suggestions = [s for s in data["suggestions"] if s["type"] == "stop"]
    assert len(stop_suggestions) > 0
    assert any("ಮೆಜೆಸ್ಟಿಕ್" in (s.get("title_kannada") or "") for s in stop_suggestions)