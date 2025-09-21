"""
Tests for public API endpoints
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from main import app
from app.models.api_key import APIKey
from app.services.api_auth_service import APIAuthService

client = TestClient(app)

class TestPublicAPI:
    """Test cases for public API endpoints"""

    @pytest.fixture
    def mock_api_key(self):
        """Mock API key for testing"""
        return APIKey(
            id=1,
            key_name="Test API Key",
            key_hash="test_hash",
            key_prefix="test_",
            is_active=True,
            requests_per_minute=100,
            requests_per_hour=1000,
            requests_per_day=10000,
            total_requests=0
        )

    @pytest.fixture
    def mock_bus_data(self):
        """Mock bus data for testing"""
        return {
            "id": 1,
            "vehicle_number": "KA-01-AB-1234",
            "status": "active",
            "current_location": {
                "latitude": 12.9716,
                "longitude": 77.5946,
                "speed": 25.5,
                "bearing": 45.0,
                "recorded_at": datetime.utcnow().isoformat(),
                "is_recent": True
            },
            "current_trip": {
                "id": 1,
                "route_id": 1,
                "route_number": "335E",
                "route_name": "Test Route",
                "start_time": datetime.utcnow().isoformat()
            },
            "last_updated": datetime.utcnow().isoformat()
        }

    def test_get_public_buses_success(self, mock_api_key, mock_bus_data):
        """Test successful retrieval of public buses"""
        with patch('app.api.v1.endpoints.public.check_rate_limit') as mock_auth, \
             patch('app.api.v1.endpoints.public.db') as mock_db:
            
            # Mock authentication
            mock_auth.return_value = mock_api_key
            
            # Mock database query
            mock_bus = Mock()
            mock_bus.id = 1
            mock_bus.vehicle_number = "KA-01-AB-1234"
            mock_bus.status = "active"
            mock_bus.is_active = True
            
            mock_db.query.return_value.filter.return_value.offset.return_value.limit.return_value.all.return_value = [mock_bus]
            mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
            
            response = client.get("/api/v1/public/buses?api_key=test_key")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "data" in data
            assert "message" in data
            assert "timestamp" in data

    def test_get_public_buses_unauthorized(self):
        """Test unauthorized access to public buses"""
        response = client.get("/api/v1/public/buses")
        
        assert response.status_code == 401

    def test_get_public_buses_rate_limited(self, mock_api_key):
        """Test rate limiting for public buses"""
        with patch('app.api.v1.endpoints.public.check_rate_limit') as mock_auth:
            # Mock rate limit exceeded
            from fastapi import HTTPException
            mock_auth.side_effect = HTTPException(status_code=429, detail="Rate limit exceeded")
            
            response = client.get("/api/v1/public/buses?api_key=test_key")
            
            assert response.status_code == 429

    def test_get_public_bus_by_id_success(self, mock_api_key):
        """Test successful retrieval of specific bus"""
        with patch('app.api.v1.endpoints.public.check_rate_limit') as mock_auth, \
             patch('app.api.v1.endpoints.public.db') as mock_db:
            
            # Mock authentication
            mock_auth.return_value = mock_api_key
            
            # Mock database query
            mock_bus = Mock()
            mock_bus.id = 1
            mock_bus.vehicle_number = "KA-01-AB-1234"
            mock_bus.status = "active"
            mock_bus.is_active = True
            
            mock_db.query.return_value.filter.return_value.first.return_value = mock_bus
            mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
            
            response = client.get("/api/v1/public/buses/1?api_key=test_key")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["id"] == 1

    def test_get_public_bus_not_found(self, mock_api_key):
        """Test bus not found scenario"""
        with patch('app.api.v1.endpoints.public.check_rate_limit') as mock_auth, \
             patch('app.api.v1.endpoints.public.db') as mock_db:
            
            # Mock authentication
            mock_auth.return_value = mock_api_key
            
            # Mock database query returning None
            mock_db.query.return_value.filter.return_value.first.return_value = None
            
            response = client.get("/api/v1/public/buses/999?api_key=test_key")
            
            assert response.status_code == 404

    def test_get_public_routes_success(self, mock_api_key):
        """Test successful retrieval of public routes"""
        with patch('app.api.v1.endpoints.public.check_rate_limit') as mock_auth, \
             patch('app.api.v1.endpoints.public.db') as mock_db:
            
            # Mock authentication
            mock_auth.return_value = mock_api_key
            
            # Mock database query
            mock_route = Mock()
            mock_route.id = 1
            mock_route.name = "Test Route"
            mock_route.route_number = "335E"
            mock_route.is_active = True
            mock_route.stops = []
            
            mock_db.query.return_value.filter.return_value.offset.return_value.limit.return_value.all.return_value = [mock_route]
            
            response = client.get("/api/v1/public/routes?api_key=test_key")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert len(data["data"]) == 1
            assert data["data"][0]["route_number"] == "335E"

    def test_get_public_route_by_id_success(self, mock_api_key):
        """Test successful retrieval of specific route"""
        with patch('app.api.v1.endpoints.public.check_rate_limit') as mock_auth, \
             patch('app.api.v1.endpoints.public.db') as mock_db:
            
            # Mock authentication
            mock_auth.return_value = mock_api_key
            
            # Mock database query
            mock_route = Mock()
            mock_route.id = 1
            mock_route.name = "Test Route"
            mock_route.route_number = "335E"
            mock_route.is_active = True
            mock_route.stops = []
            
            mock_db.query.return_value.filter.return_value.first.return_value = mock_route
            mock_db.query.return_value.filter.return_value.all.return_value = []
            
            response = client.get("/api/v1/public/routes/1?api_key=test_key")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["id"] == 1

    def test_get_public_stops_success(self, mock_api_key):
        """Test successful retrieval of public stops"""
        with patch('app.api.v1.endpoints.public.check_rate_limit') as mock_auth, \
             patch('app.api.v1.endpoints.public.db') as mock_db:
            
            # Mock authentication
            mock_auth.return_value = mock_api_key
            
            # Mock database query
            mock_stop = Mock()
            mock_stop.id = 1
            mock_stop.name = "Test Stop"
            mock_stop.name_kannada = "ಪರೀಕ್ಷಾ ನಿಲ್ದಾಣ"
            mock_stop.latitude = 12.9716
            mock_stop.longitude = 77.5946
            mock_stop.is_active = True
            mock_stop.routes = []
            
            mock_db.query.return_value.filter.return_value.offset.return_value.limit.return_value.all.return_value = [mock_stop]
            
            response = client.get("/api/v1/public/stops?api_key=test_key")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert len(data["data"]) == 1
            assert data["data"][0]["name"] == "Test Stop"

    def test_get_realtime_locations_success(self, mock_api_key):
        """Test successful retrieval of real-time locations"""
        with patch('app.api.v1.endpoints.public.check_rate_limit') as mock_auth, \
             patch('app.api.v1.endpoints.public.db') as mock_db:
            
            # Mock authentication
            mock_auth.return_value = mock_api_key
            
            # Mock database query
            mock_location = Mock()
            mock_location.vehicle_id = 1
            mock_location.latitude = 12.9716
            mock_location.longitude = 77.5946
            mock_location.speed = 25.5
            mock_location.bearing = 45.0
            mock_location.recorded_at = datetime.utcnow()
            mock_location.is_recent = True
            
            mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [mock_location]
            
            response = client.get("/api/v1/public/realtime/locations?api_key=test_key")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert len(data["data"]) == 1
            assert data["data"][0]["vehicle_id"] == 1

    def test_get_api_health_success(self, mock_api_key):
        """Test API health check"""
        with patch('app.api.v1.endpoints.public.check_rate_limit') as mock_auth, \
             patch('app.api.v1.endpoints.public.db') as mock_db:
            
            # Mock authentication
            mock_auth.return_value = mock_api_key
            
            # Mock database query
            mock_db.execute.return_value = None
            
            response = client.get("/api/v1/public/health?api_key=test_key")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "status" in data["data"]
            assert "timestamp" in data["data"]
            assert "version" in data["data"]

    def test_api_response_format(self, mock_api_key):
        """Test that API responses follow the correct format"""
        with patch('app.api.v1.endpoints.public.check_rate_limit') as mock_auth, \
             patch('app.api.v1.endpoints.public.db') as mock_db:
            
            # Mock authentication
            mock_auth.return_value = mock_api_key
            
            # Mock database query
            mock_db.query.return_value.filter.return_value.offset.return_value.limit.return_value.all.return_value = []
            
            response = client.get("/api/v1/public/buses?api_key=test_key")
            
            assert response.status_code == 200
            data = response.json()
            
            # Check required fields
            assert "success" in data
            assert "data" in data
            assert "timestamp" in data
            assert data["success"] is True
            assert isinstance(data["data"], list)

    def test_api_error_handling(self, mock_api_key):
        """Test API error handling"""
        with patch('app.api.v1.endpoints.public.check_rate_limit') as mock_auth, \
             patch('app.api.v1.endpoints.public.db') as mock_db:
            
            # Mock authentication
            mock_auth.return_value = mock_api_key
            
            # Mock database error
            mock_db.query.side_effect = Exception("Database error")
            
            response = client.get("/api/v1/public/buses?api_key=test_key")
            
            assert response.status_code == 500

    def test_api_key_authentication(self):
        """Test API key authentication"""
        with patch('app.services.api_auth_service.APIAuthService.authenticate_api_key') as mock_auth:
            # Mock invalid API key
            mock_auth.return_value = None
            
            response = client.get("/api/v1/public/buses?api_key=invalid_key")
            
            assert response.status_code == 401

    def test_rate_limiting(self, mock_api_key):
        """Test rate limiting functionality"""
        with patch('app.api.v1.endpoints.public.check_rate_limit') as mock_auth:
            # Mock rate limit exceeded
            from fastapi import HTTPException
            mock_auth.side_effect = HTTPException(
                status_code=429, 
                detail="Rate limit exceeded",
                headers={"Retry-After": "60"}
            )
            
            response = client.get("/api/v1/public/buses?api_key=test_key")
            
            assert response.status_code == 429
            assert "Retry-After" in response.headers

    def test_permission_denied(self, mock_api_key):
        """Test permission denied scenario"""
        with patch('app.api.v1.endpoints.public.check_rate_limit') as mock_auth:
            # Mock permission denied
            from fastapi import HTTPException
            mock_auth.side_effect = HTTPException(
                status_code=403, 
                detail="Permission denied"
            )
            
            response = client.get("/api/v1/public/buses?api_key=test_key")
            
            assert response.status_code == 403

    def test_pagination_parameters(self, mock_api_key):
        """Test pagination parameters"""
        with patch('app.api.v1.endpoints.public.check_rate_limit') as mock_auth, \
             patch('app.api.v1.endpoints.public.db') as mock_db:
            
            # Mock authentication
            mock_auth.return_value = mock_api_key
            
            # Mock database query
            mock_db.query.return_value.filter.return_value.offset.return_value.limit.return_value.all.return_value = []
            
            response = client.get("/api/v1/public/buses?api_key=test_key&limit=50&offset=10")
            
            assert response.status_code == 200
            # Verify that offset and limit were applied
            mock_db.query.return_value.filter.return_value.offset.assert_called_with(10)
            mock_db.query.return_value.filter.return_value.offset.return_value.limit.assert_called_with(50)

    def test_filtering_parameters(self, mock_api_key):
        """Test filtering parameters"""
        with patch('app.api.v1.endpoints.public.check_rate_limit') as mock_auth, \
             patch('app.api.v1.endpoints.public.db') as mock_db:
            
            # Mock authentication
            mock_auth.return_value = mock_api_key
            
            # Mock database query
            mock_db.query.return_value.filter.return_value.offset.return_value.limit.return_value.all.return_value = []
            
            response = client.get("/api/v1/public/buses?api_key=test_key&status=active&route_id=1")
            
            assert response.status_code == 200
            # Verify that filters were applied
            assert mock_db.query.return_value.filter.call_count >= 2  # At least 2 filter calls

    def test_request_id_header(self, mock_api_key):
        """Test request ID header handling"""
        with patch('app.api.v1.endpoints.public.check_rate_limit') as mock_auth, \
             patch('app.api.v1.endpoints.public.db') as mock_db:
            
            # Mock authentication
            mock_auth.return_value = mock_api_key
            
            # Mock database query
            mock_db.query.return_value.filter.return_value.offset.return_value.limit.return_value.all.return_value = []
            
            response = client.get(
                "/api/v1/public/buses?api_key=test_key",
                headers={"X-Request-ID": "test-request-123"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["request_id"] == "test-request-123"

