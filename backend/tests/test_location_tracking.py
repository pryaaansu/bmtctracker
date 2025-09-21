"""
Tests for Location Tracking Service
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from app.services.location_tracking_service import LocationTrackingService, LocationUpdate
from app.services.mock_data_generator import ScenarioType


class TestLocationTrackingService:
    """Test cases for LocationTrackingService"""
    
    @pytest.fixture
    def service(self):
        """Create a LocationTrackingService instance for testing"""
        service = LocationTrackingService()
        service.redis_client = Mock()
        return service
    
    @pytest.fixture
    def sample_location(self):
        """Sample location update for testing"""
        return LocationUpdate(
            vehicle_id=1,
            latitude=12.9716,
            longitude=77.5946,
            speed=25.0,
            bearing=90,
            timestamp=datetime.now()
        )
    
    def test_location_update_creation(self, sample_location):
        """Test LocationUpdate dataclass creation"""
        assert sample_location.vehicle_id == 1
        assert sample_location.latitude == 12.9716
        assert sample_location.longitude == 77.5946
        assert sample_location.speed == 25.0
        assert sample_location.bearing == 90
        assert not sample_location.interpolated
        assert sample_location.confidence == 1.0
    
    @pytest.mark.asyncio
    async def test_process_location_update(self, service, sample_location):
        """Test processing a location update"""
        # Mock the async methods
        service._cache_location_update = AsyncMock()
        service._store_location_update = AsyncMock()
        service._broadcast_location_update = AsyncMock()
        
        result = await service.process_location_update(
            vehicle_id=sample_location.vehicle_id,
            latitude=sample_location.latitude,
            longitude=sample_location.longitude,
            speed=sample_location.speed,
            bearing=sample_location.bearing
        )
        
        assert result.vehicle_id == sample_location.vehicle_id
        assert result.latitude == sample_location.latitude
        assert result.longitude == sample_location.longitude
        assert result.speed == sample_location.speed
        assert result.bearing == sample_location.bearing
        
        # Verify location is cached
        assert sample_location.vehicle_id in service.location_cache
        
        # Verify async methods were called
        service._cache_location_update.assert_called_once()
        service._store_location_update.assert_called_once()
        service._broadcast_location_update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_location_smoothing(self, service):
        """Test location smoothing algorithm"""
        # First location update
        first_location = await service.process_location_update(
            vehicle_id=1,
            latitude=12.9716,
            longitude=77.5946,
            speed=25.0,
            bearing=90
        )
        
        # Mock async methods to avoid actual I/O
        service._cache_location_update = AsyncMock()
        service._store_location_update = AsyncMock()
        service._broadcast_location_update = AsyncMock()
        
        # Second location update (should be smoothed)
        second_location = await service.process_location_update(
            vehicle_id=1,
            latitude=12.9720,  # Slightly different
            longitude=77.5950,  # Slightly different
            speed=30.0,
            bearing=95
        )
        
        # The smoothed location should be between the two values
        assert first_location.latitude < second_location.latitude < 12.9720
        assert first_location.longitude < second_location.longitude < 77.5950
        assert first_location.speed < second_location.speed < 30.0
    
    def test_distance_calculation(self, service):
        """Test distance calculation between coordinates"""
        coord1 = (12.9716, 77.5946)  # Majestic
        coord2 = (12.9279, 77.5937)  # Jayanagar
        
        distance = service._calculate_distance(coord1, coord2)
        
        # Distance should be approximately 4.9 km
        assert 4800 < distance < 5000  # meters
    
    @pytest.mark.asyncio
    async def test_get_vehicle_location_from_cache(self, service, sample_location):
        """Test getting vehicle location from cache"""
        # Add location to cache
        service.location_cache[sample_location.vehicle_id] = sample_location
        
        result = await service.get_vehicle_location(sample_location.vehicle_id)
        
        assert result == sample_location
    
    @pytest.mark.asyncio
    async def test_get_vehicle_location_not_found(self, service):
        """Test getting vehicle location when not found"""
        # Mock database query to return None
        with patch('app.services.location_tracking_service.get_db') as mock_get_db:
            mock_db = Mock()
            mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
            mock_get_db.return_value = iter([mock_db])
            
            result = await service.get_vehicle_location(999)
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_get_all_active_locations(self, service):
        """Test getting all active locations"""
        # Add some locations to cache
        now = datetime.now()
        
        # Recent location (should be included)
        recent_location = LocationUpdate(
            vehicle_id=1,
            latitude=12.9716,
            longitude=77.5946,
            speed=25.0,
            bearing=90,
            timestamp=now - timedelta(seconds=60)
        )
        
        # Old location (should be excluded)
        old_location = LocationUpdate(
            vehicle_id=2,
            latitude=12.9279,
            longitude=77.5937,
            speed=20.0,
            bearing=180,
            timestamp=now - timedelta(seconds=400)
        )
        
        service.location_cache[1] = recent_location
        service.location_cache[2] = old_location
        
        active_locations = await service.get_all_active_locations()
        
        # Only recent location should be returned
        assert len(active_locations) == 1
        assert active_locations[0].vehicle_id == 1
    
    def test_websocket_connection_management(self, service):
        """Test WebSocket connection management"""
        connection_id = "test_connection_123"
        
        # Add connection
        service.add_websocket_connection(connection_id)
        assert connection_id in service.active_connections
        
        # Remove connection
        service.remove_websocket_connection(connection_id)
        assert connection_id not in service.active_connections
    
    @pytest.mark.asyncio
    async def test_set_vehicle_scenario(self, service):
        """Test setting vehicle scenario"""
        vehicle_id = 1
        scenario = "rush_hour"
        
        await service.set_vehicle_scenario(vehicle_id, scenario)
        
        # Verify scenario was set in mock generator
        bus_state = service.mock_generator.active_buses.get(vehicle_id)
        if bus_state:
            assert bus_state["scenario"] == ScenarioType.RUSH_HOUR
    
    @pytest.mark.asyncio
    async def test_simulate_rush_hour(self, service):
        """Test rush hour simulation"""
        # Add a bus to the mock generator
        service.mock_generator.active_buses[1] = {
            "route_number": "001",
            "current_point_index": 0,
            "progress": 0.0,
            "scenario": ScenarioType.NORMAL,
            "last_update": datetime.now(),
            "speed": 25.0,
            "bearing": 0,
            "occupancy": 50
        }
        
        await service.simulate_rush_hour(True)
        
        # Verify all buses are set to rush hour
        for bus_state in service.mock_generator.active_buses.values():
            assert bus_state["scenario"] == ScenarioType.RUSH_HOUR


class TestLocationInterpolation:
    """Test cases for location interpolation"""
    
    @pytest.fixture
    def service(self):
        service = LocationTrackingService()
        service.redis_client = Mock()
        return service
    
    @pytest.mark.asyncio
    async def test_interpolated_position_generation(self, service):
        """Test generation of interpolated positions"""
        base_location = LocationUpdate(
            vehicle_id=1,
            latitude=12.9716,
            longitude=77.5946,
            speed=36.0,  # 36 km/h = 10 m/s
            bearing=90,  # East
            timestamp=datetime.now() - timedelta(seconds=10)  # 10 seconds ago
        )
        
        interpolated = await service._generate_interpolated_position(base_location)
        
        # Vehicle should have moved east (longitude should increase)
        assert interpolated.longitude > base_location.longitude
        assert interpolated.latitude == pytest.approx(base_location.latitude, abs=0.001)
        assert interpolated.interpolated is True
        assert interpolated.confidence < base_location.confidence


@pytest.mark.asyncio
async def test_location_service_initialization():
    """Test location service initialization"""
    service = LocationTrackingService()
    
    # Mock Redis connection
    with patch('redis.asyncio.from_url') as mock_redis:
        mock_redis.return_value = Mock()
        
        await service.initialize()
        
        # Verify Redis client was created
        mock_redis.assert_called_once_with("redis://localhost:6379")


if __name__ == "__main__":
    pytest.main([__file__])