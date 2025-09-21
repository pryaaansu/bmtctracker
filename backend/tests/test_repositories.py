"""
Unit tests for repository classes
"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from app.repositories.vehicle import VehicleRepository
from app.repositories.route import RouteRepository
from app.repositories.stop import StopRepository
from app.repositories.subscription import SubscriptionRepository
from app.repositories.location import VehicleLocationRepository
from app.models.vehicle import Vehicle, VehicleStatus
from app.models.route import Route
from app.models.stop import Stop
from app.models.subscription import Subscription, NotificationChannel
from app.models.location import VehicleLocation

class TestVehicleRepository:
    """Test VehicleRepository functionality"""
    
    def test_create_vehicle(self, db_session, sample_vehicle_data):
        """Test creating a vehicle"""
        repo = VehicleRepository(db_session)
        
        # Mock the create schema
        create_data = Mock()
        create_data.dict.return_value = sample_vehicle_data
        
        vehicle = repo.create(create_data)
        
        assert vehicle.vehicle_number == "KA01-TEST"
        assert vehicle.capacity == 40
        assert vehicle.status == VehicleStatus.ACTIVE
    
    def test_get_vehicle_by_id(self, db_session, sample_vehicle_data):
        """Test getting vehicle by ID"""
        repo = VehicleRepository(db_session)
        
        # Create a vehicle first
        vehicle = Vehicle(**sample_vehicle_data)
        db_session.add(vehicle)
        db_session.commit()
        
        # Test retrieval
        retrieved = repo.get(vehicle.id, use_cache=False)
        assert retrieved.vehicle_number == "KA01-TEST"
    
    def test_get_by_vehicle_number(self, db_session, sample_vehicle_data):
        """Test getting vehicle by vehicle number"""
        repo = VehicleRepository(db_session)
        
        # Create a vehicle
        vehicle = Vehicle(**sample_vehicle_data)
        db_session.add(vehicle)
        db_session.commit()
        
        # Test retrieval by vehicle number
        retrieved = repo.get_by_vehicle_number("KA01-TEST")
        assert retrieved.id == vehicle.id
    
    def test_get_active_vehicles(self, db_session):
        """Test getting active vehicles"""
        repo = VehicleRepository(db_session)
        
        # Create vehicles with different statuses
        active_vehicle = Vehicle(vehicle_number="KA01-ACTIVE", capacity=40, status=VehicleStatus.ACTIVE)
        inactive_vehicle = Vehicle(vehicle_number="KA01-INACTIVE", capacity=40, status=VehicleStatus.MAINTENANCE)
        
        db_session.add_all([active_vehicle, inactive_vehicle])
        db_session.commit()
        
        # Test getting active vehicles
        active_vehicles = repo.get_active_vehicles()
        assert len(active_vehicles) == 1
        assert active_vehicles[0].vehicle_number == "KA01-ACTIVE"
    
    def test_update_status(self, db_session, sample_vehicle_data):
        """Test updating vehicle status"""
        repo = VehicleRepository(db_session)
        
        # Create a vehicle
        vehicle = Vehicle(**sample_vehicle_data)
        db_session.add(vehicle)
        db_session.commit()
        
        # Update status
        updated = repo.update_status(vehicle.id, VehicleStatus.MAINTENANCE)
        assert updated.status == VehicleStatus.MAINTENANCE

class TestRouteRepository:
    """Test RouteRepository functionality"""
    
    def test_create_route(self, db_session, sample_route_data):
        """Test creating a route"""
        repo = RouteRepository(db_session)
        
        # Mock the create schema
        create_data = Mock()
        create_data.dict.return_value = sample_route_data
        
        route = repo.create(create_data)
        
        assert route.name == "Test Route"
        assert route.route_number == "TEST1"
        assert route.is_active == True
    
    def test_get_by_route_number(self, db_session, sample_route_data):
        """Test getting route by route number"""
        repo = RouteRepository(db_session)
        
        # Create a route
        route = Route(**sample_route_data)
        db_session.add(route)
        db_session.commit()
        
        # Test retrieval
        retrieved = repo.get_by_route_number("TEST1")
        assert retrieved.id == route.id
    
    def test_get_active_routes(self, db_session):
        """Test getting active routes"""
        repo = RouteRepository(db_session)
        
        # Create routes with different statuses
        active_route = Route(
            name="Active Route", route_number="ACTIVE1", 
            geojson='{}', polyline='test', is_active=True
        )
        inactive_route = Route(
            name="Inactive Route", route_number="INACTIVE1",
            geojson='{}', polyline='test', is_active=False
        )
        
        db_session.add_all([active_route, inactive_route])
        db_session.commit()
        
        # Test getting active routes
        active_routes = repo.get_active_routes()
        assert len(active_routes) == 1
        assert active_routes[0].route_number == "ACTIVE1"
    
    def test_search_routes(self, db_session):
        """Test searching routes"""
        repo = RouteRepository(db_session)
        
        # Create test routes
        route1 = Route(
            name="Majestic Express", route_number="335E",
            geojson='{}', polyline='test', is_active=True
        )
        route2 = Route(
            name="Airport Shuttle", route_number="VAYU",
            geojson='{}', polyline='test', is_active=True
        )
        
        db_session.add_all([route1, route2])
        db_session.commit()
        
        # Test search by name
        results = repo.search_routes("Majestic")
        assert len(results) == 1
        assert results[0].name == "Majestic Express"
        
        # Test search by route number
        results = repo.search_routes("335")
        assert len(results) == 1
        assert results[0].route_number == "335E"

class TestStopRepository:
    """Test StopRepository functionality"""
    
    def test_create_stop(self, db_session, sample_route_data, sample_stop_data):
        """Test creating a stop"""
        # First create a route
        route = Route(**sample_route_data)
        db_session.add(route)
        db_session.commit()
        
        # Update stop data with route ID
        sample_stop_data["route_id"] = route.id
        
        repo = StopRepository(db_session)
        
        # Mock the create schema
        create_data = Mock()
        create_data.dict.return_value = sample_stop_data
        
        stop = repo.create(create_data)
        
        assert stop.name == "Test Stop"
        assert stop.name_kannada == "ಟೆಸ್ಟ್ ಸ್ಟಾಪ್"
        assert float(stop.latitude) == 12.9716
    
    def test_get_by_route(self, db_session, sample_route_data):
        """Test getting stops by route"""
        # Create a route
        route = Route(**sample_route_data)
        db_session.add(route)
        db_session.commit()
        
        # Create stops for the route
        stop1 = Stop(
            route_id=route.id, name="Stop 1", latitude=12.9716, 
            longitude=77.5946, stop_order=1
        )
        stop2 = Stop(
            route_id=route.id, name="Stop 2", latitude=12.9800, 
            longitude=77.6000, stop_order=2
        )
        
        db_session.add_all([stop1, stop2])
        db_session.commit()
        
        repo = StopRepository(db_session)
        stops = repo.get_by_route(route.id)
        
        assert len(stops) == 2
        assert stops[0].stop_order == 1
        assert stops[1].stop_order == 2
    
    def test_search_stops(self, db_session, sample_route_data):
        """Test searching stops"""
        # Create a route
        route = Route(**sample_route_data)
        db_session.add(route)
        db_session.commit()
        
        # Create test stops
        stop1 = Stop(
            route_id=route.id, name="Majestic Bus Station", 
            name_kannada="ಮೆಜೆಸ್ಟಿಕ್ ಬಸ್ ನಿಲ್ದಾಣ",
            latitude=12.9716, longitude=77.5946, stop_order=1
        )
        stop2 = Stop(
            route_id=route.id, name="Electronic City",
            latitude=12.8456, longitude=77.6648, stop_order=2
        )
        
        db_session.add_all([stop1, stop2])
        db_session.commit()
        
        repo = StopRepository(db_session)
        
        # Test search by English name
        results = repo.search_stops("Majestic")
        assert len(results) == 1
        assert results[0].name == "Majestic Bus Station"
        
        # Test search by Kannada name
        results = repo.search_stops("ಮೆಜೆಸ್ಟಿಕ್")
        assert len(results) == 1
    
    @patch('app.repositories.stop.StopRepository._cache_get')
    @patch('app.repositories.stop.StopRepository._cache_set')
    def test_caching_behavior(self, mock_cache_set, mock_cache_get, db_session, sample_route_data):
        """Test that caching is working correctly"""
        mock_cache_get.return_value = None  # Simulate cache miss
        
        # Create a route
        route = Route(**sample_route_data)
        db_session.add(route)
        db_session.commit()
        
        repo = StopRepository(db_session)
        stops = repo.get_by_route(route.id)
        
        # Verify cache methods were called
        mock_cache_get.assert_called()
        mock_cache_set.assert_called()

class TestSubscriptionRepository:
    """Test SubscriptionRepository functionality"""
    
    def test_create_subscription(self, db_session, sample_route_data):
        """Test creating a subscription"""
        # Create route and stop
        route = Route(**sample_route_data)
        db_session.add(route)
        db_session.commit()
        
        stop = Stop(
            route_id=route.id, name="Test Stop",
            latitude=12.9716, longitude=77.5946, stop_order=1
        )
        db_session.add(stop)
        db_session.commit()
        
        repo = SubscriptionRepository(db_session)
        
        # Create subscription
        subscription = repo.create_or_update_subscription(
            phone="+919876543210",
            stop_id=stop.id,
            channel=NotificationChannel.SMS,
            eta_threshold=5
        )
        
        assert subscription.phone == "+919876543210"
        assert subscription.channel == NotificationChannel.SMS
        assert subscription.is_active == True
    
    def test_get_by_phone(self, db_session, sample_route_data):
        """Test getting subscriptions by phone"""
        # Setup route and stop
        route = Route(**sample_route_data)
        db_session.add(route)
        db_session.commit()
        
        stop = Stop(
            route_id=route.id, name="Test Stop",
            latitude=12.9716, longitude=77.5946, stop_order=1
        )
        db_session.add(stop)
        db_session.commit()
        
        # Create subscriptions
        sub1 = Subscription(
            phone="+919876543210", stop_id=stop.id,
            channel=NotificationChannel.SMS, is_active=True
        )
        sub2 = Subscription(
            phone="+919876543210", stop_id=stop.id,
            channel=NotificationChannel.WHATSAPP, is_active=True
        )
        
        db_session.add_all([sub1, sub2])
        db_session.commit()
        
        repo = SubscriptionRepository(db_session)
        subscriptions = repo.get_by_phone("+919876543210")
        
        assert len(subscriptions) == 2
    
    def test_deactivate_subscription(self, db_session, sample_route_data):
        """Test deactivating a subscription"""
        # Setup
        route = Route(**sample_route_data)
        db_session.add(route)
        db_session.commit()
        
        stop = Stop(
            route_id=route.id, name="Test Stop",
            latitude=12.9716, longitude=77.5946, stop_order=1
        )
        db_session.add(stop)
        db_session.commit()
        
        subscription = Subscription(
            phone="+919876543210", stop_id=stop.id,
            channel=NotificationChannel.SMS, is_active=True
        )
        db_session.add(subscription)
        db_session.commit()
        
        repo = SubscriptionRepository(db_session)
        
        # Deactivate
        deactivated = repo.deactivate_subscription(subscription.id)
        assert deactivated.is_active == False

class TestVehicleLocationRepository:
    """Test VehicleLocationRepository functionality"""
    
    def test_add_location_update(self, db_session, sample_vehicle_data):
        """Test adding location update"""
        # Create vehicle
        vehicle = Vehicle(**sample_vehicle_data)
        db_session.add(vehicle)
        db_session.commit()
        
        repo = VehicleLocationRepository(db_session)
        
        # Add location
        location = repo.add_location_update(
            vehicle_id=vehicle.id,
            latitude=12.9716,
            longitude=77.5946,
            speed=25.5,
            bearing=90
        )
        
        assert location.vehicle_id == vehicle.id
        assert float(location.latitude) == 12.9716
        assert float(location.speed) == 25.5
    
    def test_get_latest_by_vehicle(self, db_session, sample_vehicle_data):
        """Test getting latest location for vehicle"""
        # Create vehicle
        vehicle = Vehicle(**sample_vehicle_data)
        db_session.add(vehicle)
        db_session.commit()
        
        # Create multiple locations
        loc1 = VehicleLocation(
            vehicle_id=vehicle.id, latitude=12.9716, longitude=77.5946,
            recorded_at=datetime(2023, 1, 1, 10, 0, 0)
        )
        loc2 = VehicleLocation(
            vehicle_id=vehicle.id, latitude=12.9800, longitude=77.6000,
            recorded_at=datetime(2023, 1, 1, 11, 0, 0)  # Later time
        )
        
        db_session.add_all([loc1, loc2])
        db_session.commit()
        
        repo = VehicleLocationRepository(db_session)
        latest = repo.get_latest_by_vehicle(vehicle.id)
        
        assert float(latest.latitude) == 12.9800  # Should be the later location
    
    def test_calculate_distance(self):
        """Test distance calculation utility"""
        # Test known distance (approximately)
        # Bangalore to Chennai is roughly 350km
        bangalore_lat, bangalore_lng = 12.9716, 77.5946
        chennai_lat, chennai_lng = 13.0827, 80.2707
        
        distance = StopRepository.calculate_distance(
            bangalore_lat, bangalore_lng, chennai_lat, chennai_lng
        )
        
        # Should be roughly 350km (allowing for some variance)
        assert 300 < distance < 400