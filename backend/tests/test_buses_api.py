"""
Tests for buses API endpoints
"""

import pytest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from main import app
from app.models.vehicle import Vehicle, VehicleStatus
from app.models.location import VehicleLocation
from app.models.route import Route
from app.models.trip import Trip
from app.core.database import get_db

client = TestClient(app)

@pytest.fixture
def test_vehicles(db_session: Session):
    """Create test vehicles with locations"""
    # Create test route
    route = Route(
        name="Test Route",
        route_number="TR001",
        geojson='{"type": "LineString", "coordinates": [[77.5946, 12.9716], [77.6046, 12.9816]]}',
        polyline="test_polyline",
        is_active=True
    )
    db_session.add(route)
    db_session.flush()
    
    # Create test vehicles
    vehicles = []
    for i in range(3):
        vehicle = Vehicle(
            vehicle_number=f"KA01-{1000+i}",
            capacity=50,
            status=VehicleStatus.ACTIVE
        )
        db_session.add(vehicle)
        vehicles.append(vehicle)
    
    db_session.flush()
    
    # Create locations for vehicles
    base_time = datetime.utcnow()
    for i, vehicle in enumerate(vehicles):
        # Recent location
        location = VehicleLocation(
            vehicle_id=vehicle.id,
            latitude=12.9716 + (i * 0.001),
            longitude=77.5946 + (i * 0.001),
            speed=25.5 + i,
            bearing=45 + (i * 10),
            recorded_at=base_time - timedelta(minutes=i)
        )
        db_session.add(location)
        
        # Older location
        old_location = VehicleLocation(
            vehicle_id=vehicle.id,
            latitude=12.9700 + (i * 0.001),
            longitude=77.5930 + (i * 0.001),
            speed=20.0 + i,
            bearing=30 + (i * 10),
            recorded_at=base_time - timedelta(hours=1)
        )
        db_session.add(old_location)
    
    # Create active trip for first vehicle
    trip = Trip(
        vehicle_id=vehicles[0].id,
        route_id=route.id,
        driver_id=1,  # Assuming driver exists
        start_time=base_time - timedelta(minutes=30),
        status="active"
    )
    db_session.add(trip)
    
    db_session.commit()
    return vehicles, route

def test_get_buses_basic(test_vehicles):
    """Test basic buses endpoint"""
    vehicles, route = test_vehicles
    
    response = client.get("/api/v1/buses/")
    assert response.status_code == 200
    
    data = response.json()
    assert "buses" in data
    assert "total" in data
    assert len(data["buses"]) > 0
    
    # Check first bus structure
    bus = data["buses"][0]
    assert "id" in bus
    assert "vehicle_number" in bus
    assert "capacity" in bus
    assert "status" in bus
    assert "current_location" in bus
    assert "occupancy" in bus

def test_get_buses_with_filters(test_vehicles):
    """Test buses endpoint with filters"""
    vehicles, route = test_vehicles
    
    # Test status filter
    response = client.get("/api/v1/buses/?status=active")
    assert response.status_code == 200
    data = response.json()
    assert all(bus["status"] == "active" for bus in data["buses"])
    
    # Test route filter
    response = client.get(f"/api/v1/buses/?route_id={route.id}")
    assert response.status_code == 200
    data = response.json()
    # Should return buses on the route (with active trips)
    
    # Test pagination
    response = client.get("/api/v1/buses/?limit=1")
    assert response.status_code == 200
    data = response.json()
    assert len(data["buses"]) <= 1

def test_get_buses_without_location(test_vehicles):
    """Test buses endpoint without location data"""
    vehicles, route = test_vehicles
    
    response = client.get("/api/v1/buses/?with_location=false")
    assert response.status_code == 200
    
    data = response.json()
    for bus in data["buses"]:
        assert "current_location" not in bus or bus["current_location"] is None

def test_get_bus_details(test_vehicles):
    """Test individual bus details endpoint"""
    vehicles, route = test_vehicles
    bus_id = vehicles[0].id
    
    response = client.get(f"/api/v1/buses/{bus_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["id"] == bus_id
    assert "vehicle_number" in data
    assert "current_location" in data
    assert "current_trip" in data
    assert "occupancy" in data
    
    # Check location structure
    if data["current_location"]:
        location = data["current_location"]
        assert "latitude" in location
        assert "longitude" in location
        assert "speed" in location
        assert "bearing" in location
        assert "recorded_at" in location
        assert "age_minutes" in location

def test_get_bus_details_with_history(test_vehicles):
    """Test bus details with location history"""
    vehicles, route = test_vehicles
    bus_id = vehicles[0].id
    
    response = client.get(f"/api/v1/buses/{bus_id}?include_location_history=true&history_hours=2")
    assert response.status_code == 200
    
    data = response.json()
    assert "location_history" in data
    assert isinstance(data["location_history"], list)
    
    # Check history structure
    if data["location_history"]:
        history_item = data["location_history"][0]
        assert "latitude" in history_item
        assert "longitude" in history_item
        assert "recorded_at" in history_item

def test_get_bus_location(test_vehicles):
    """Test bus location endpoint"""
    vehicles, route = test_vehicles
    bus_id = vehicles[0].id
    
    response = client.get(f"/api/v1/buses/{bus_id}/location")
    assert response.status_code == 200
    
    data = response.json()
    assert data["vehicle_id"] == bus_id
    assert "vehicle_number" in data
    assert "location" in data
    assert "status" in data
    
    # Check location structure
    location = data["location"]
    assert "latitude" in location
    assert "longitude" in location
    assert "speed" in location
    assert "bearing" in location
    assert "recorded_at" in location
    assert "age_minutes" in location
    assert "is_recent" in location

def test_get_bus_occupancy(test_vehicles):
    """Test bus occupancy endpoint"""
    vehicles, route = test_vehicles
    bus_id = vehicles[0].id
    
    response = client.get(f"/api/v1/buses/{bus_id}/occupancy")
    assert response.status_code == 200
    
    data = response.json()
    assert data["vehicle_id"] == bus_id
    assert "vehicle_number" in data
    assert "capacity" in data
    assert "occupancy" in data
    
    # Check occupancy structure
    occupancy = data["occupancy"]
    assert "level" in occupancy
    assert "percentage" in occupancy
    assert "passenger_count" in occupancy
    assert "available_seats" in occupancy
    assert "last_updated" in occupancy
    
    # Validate occupancy logic
    assert occupancy["level"] in ["low", "medium", "high"]
    assert 0 <= occupancy["percentage"] <= 100
    assert occupancy["passenger_count"] + occupancy["available_seats"] == data["capacity"]

def test_get_nonexistent_bus(test_vehicles):
    """Test endpoints with non-existent bus ID"""
    response = client.get("/api/v1/buses/99999")
    assert response.status_code == 404
    
    response = client.get("/api/v1/buses/99999/location")
    assert response.status_code == 404
    
    response = client.get("/api/v1/buses/99999/occupancy")
    assert response.status_code == 404

def test_get_bus_location_no_data(test_vehicles):
    """Test bus location endpoint when no location data exists"""
    vehicles, route = test_vehicles
    
    # Create a vehicle without location data
    from app.core.database import get_db
    db = next(get_db())
    
    vehicle = Vehicle(
        vehicle_number="KA01-9999",
        capacity=50,
        status=VehicleStatus.ACTIVE
    )
    db.add(vehicle)
    db.commit()
    
    response = client.get(f"/api/v1/buses/{vehicle.id}/location")
    assert response.status_code == 404
    assert "No location data found" in response.json()["detail"]

def test_buses_api_validation():
    """Test API parameter validation"""
    # Test invalid pagination parameters
    response = client.get("/api/v1/buses/?skip=-1")
    assert response.status_code == 422
    
    response = client.get("/api/v1/buses/?limit=0")
    assert response.status_code == 422
    
    response = client.get("/api/v1/buses/?limit=1000")
    assert response.status_code == 422
    
    # Test invalid location max age
    response = client.get("/api/v1/buses/1/location?max_age_minutes=0")
    assert response.status_code == 422
    
    response = client.get("/api/v1/buses/1/location?max_age_minutes=100")
    assert response.status_code == 422

def test_buses_api_performance(test_vehicles):
    """Test API performance with multiple requests"""
    import time
    
    vehicles, route = test_vehicles
    
    # Test multiple concurrent-like requests
    start_time = time.time()
    
    for _ in range(10):
        response = client.get("/api/v1/buses/?limit=10")
        assert response.status_code == 200
    
    end_time = time.time()
    avg_response_time = (end_time - start_time) / 10
    
    # Should respond within reasonable time (adjust threshold as needed)
    assert avg_response_time < 1.0, f"Average response time too slow: {avg_response_time}s"