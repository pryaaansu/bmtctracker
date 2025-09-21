"""
Tests for analytics service
"""

import pytest
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from unittest.mock import Mock, patch

from app.services.analytics_service import AnalyticsService
from app.models.analytics import TripAnalytics, RoutePerformance, SystemMetrics, PredictiveAnalytics
from app.models.trip import Trip, TripStatus
from app.models.vehicle import Vehicle
from app.models.route import Route
from app.models.occupancy import OccupancyReport
from app.models.location import VehicleLocation


class TestAnalyticsService:
    """Test cases for AnalyticsService"""

    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return Mock(spec=Session)

    @pytest.fixture
    def analytics_service(self, mock_db):
        """Analytics service instance with mocked database"""
        return AnalyticsService(mock_db)

    @pytest.fixture
    def sample_trip(self):
        """Sample trip data for testing"""
        return Trip(
            id=1,
            vehicle_id=1,
            route_id=1,
            driver_id=1,
            start_time=datetime.utcnow() - timedelta(hours=1),
            end_time=datetime.utcnow(),
            status=TripStatus.COMPLETED
        )

    @pytest.fixture
    def sample_route(self):
        """Sample route data for testing"""
        return Route(
            id=1,
            name="Test Route",
            route_number="123",
            geojson='{"type": "LineString", "coordinates": [[77.5946, 12.9716], [77.6046, 12.9816]]}'
        )

    def test_calculate_trip_analytics_success(self, analytics_service, mock_db, sample_trip):
        """Test successful trip analytics calculation"""
        # Mock database queries
        mock_db.query.return_value.filter.return_value.first.return_value = sample_trip
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        
        # Mock analytics record creation
        mock_analytics = Mock(spec=TripAnalytics)
        mock_db.query.return_value.filter.return_value.first.return_value = None  # No existing analytics
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        # Test the method
        result = analytics_service.calculate_trip_analytics(1)
        
        # Verify database interactions
        assert mock_db.add.called
        assert mock_db.commit.called
        assert mock_db.refresh.called

    def test_calculate_trip_analytics_trip_not_found(self, analytics_service, mock_db):
        """Test trip analytics calculation when trip not found"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = analytics_service.calculate_trip_analytics(999)
        
        assert result is None

    def test_calculate_trip_analytics_trip_not_completed(self, analytics_service, mock_db):
        """Test trip analytics calculation when trip not completed"""
        incomplete_trip = Trip(
            id=1,
            vehicle_id=1,
            route_id=1,
            driver_id=1,
            start_time=datetime.utcnow() - timedelta(hours=1),
            end_time=None,
            status=TripStatus.ACTIVE
        )
        mock_db.query.return_value.filter.return_value.first.return_value = incomplete_trip
        
        result = analytics_service.calculate_trip_analytics(1)
        
        assert result is None

    def test_get_trip_history(self, analytics_service, mock_db):
        """Test getting trip history"""
        # Mock query results
        mock_analytics = Mock(spec=TripAnalytics)
        mock_analytics.trip_id = 1
        mock_analytics.actual_duration_minutes = 45.0
        mock_analytics.delay_minutes = 5.0
        mock_analytics.on_time_percentage = 88.9
        mock_analytics.total_distance_km = 12.5
        mock_analytics.average_speed_kmh = 16.7
        mock_analytics.total_passengers = 25
        mock_analytics.peak_occupancy_percentage = 80.0
        mock_analytics.co2_saved_kg = 2.5
        mock_analytics.stops_completed = 8
        mock_analytics.stops_skipped = 0

        mock_trip = Mock(spec=Trip)
        mock_trip.id = 1
        mock_trip.start_time = datetime.utcnow() - timedelta(hours=1)
        mock_trip.end_time = datetime.utcnow()

        mock_route = Mock(spec=Route)
        mock_route.route_number = "123"
        mock_route.name = "Test Route"

        mock_vehicle = Mock(spec=Vehicle)
        mock_vehicle.vehicle_number = "KA-01-AB-1234"

        # Mock query chain
        mock_query = Mock()
        mock_query.join.return_value.join.return_value.join.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [
            (mock_analytics, mock_trip, mock_route, mock_vehicle)
        ]
        mock_db.query.return_value = mock_query

        result = analytics_service.get_trip_history(limit=10)

        assert len(result) == 1
        assert result[0]['trip_id'] == 1
        assert result[0]['route_number'] == "123"
        assert result[0]['vehicle_number'] == "KA-01-AB-1234"

    def test_get_performance_metrics(self, analytics_service, mock_db):
        """Test getting performance metrics"""
        # Mock analytics data
        mock_analytics1 = Mock(spec=TripAnalytics)
        mock_analytics1.delay_minutes = 5.0
        mock_analytics1.total_passengers = 25
        mock_analytics1.average_occupancy_percentage = 70.0
        mock_analytics1.co2_saved_kg = 2.5

        mock_analytics2 = Mock(spec=TripAnalytics)
        mock_analytics2.delay_minutes = 10.0
        mock_analytics2.total_passengers = 30
        mock_analytics2.average_occupancy_percentage = 80.0
        mock_analytics2.co2_saved_kg = 3.0

        # Mock query chain
        mock_query = Mock()
        mock_query.join.return_value.filter.return_value.all.return_value = [mock_analytics1, mock_analytics2]
        mock_db.query.return_value = mock_query

        result = analytics_service.get_performance_metrics()

        assert result['total_trips'] == 2
        assert result['on_time_percentage'] == 50.0  # 1 out of 2 trips on time (delay <= 5)
        assert result['average_delay_minutes'] == 7.5
        assert result['total_passengers'] == 55
        assert result['average_occupancy'] == 75.0
        assert result['total_co2_saved_kg'] == 5.5

    def test_get_ridership_estimation(self, analytics_service, mock_db):
        """Test getting ridership estimation"""
        # Mock analytics data
        mock_analytics1 = Mock(spec=TripAnalytics)
        mock_analytics1.total_passengers = 25
        mock_analytics1.peak_occupancy_percentage = 80.0

        mock_analytics2 = Mock(spec=TripAnalytics)
        mock_analytics2.total_passengers = 30
        mock_analytics2.peak_occupancy_percentage = 90.0

        # Mock trip data
        mock_trip1 = Mock(spec=Trip)
        mock_trip1.start_time = datetime.utcnow() - timedelta(days=1)

        mock_trip2 = Mock(spec=Trip)
        mock_trip2.start_time = datetime.utcnow() - timedelta(days=2)

        # Mock query chain
        mock_query = Mock()
        mock_query.join.return_value.filter.return_value.all.return_value = [mock_analytics1, mock_analytics2]
        mock_db.query.return_value = mock_query

        # Mock trip queries
        mock_trip_query = Mock()
        mock_trip_query.filter.return_value.first.side_effect = [mock_trip1, mock_trip2]
        mock_db.query.return_value = mock_trip_query

        result = analytics_service.get_ridership_estimation()

        assert result['total_passengers'] == 55
        assert result['average_daily_passengers'] == 27.5
        assert result['peak_hour_occupancy'] == 90.0

    def test_calculate_carbon_footprint(self, analytics_service, mock_db):
        """Test calculating carbon footprint"""
        # Mock analytics data
        mock_analytics1 = Mock(spec=TripAnalytics)
        mock_analytics1.co2_saved_kg = 2.5
        mock_analytics1.total_distance_km = 10.0
        mock_analytics1.total_passengers = 25

        mock_analytics2 = Mock(spec=TripAnalytics)
        mock_analytics2.co2_saved_kg = 3.0
        mock_analytics2.total_distance_km = 15.0
        mock_analytics2.total_passengers = 30

        # Mock query chain
        mock_query = Mock()
        mock_query.join.return_value.filter.return_value.all.return_value = [mock_analytics1, mock_analytics2]
        mock_db.query.return_value = mock_query

        result = analytics_service.calculate_carbon_footprint()

        assert result['total_co2_saved_kg'] == 5.5
        assert result['total_distance_km'] == 25.0
        assert result['total_passengers'] == 55
        assert result['equivalent_cars_off_road'] > 0

    def test_generate_demand_prediction(self, analytics_service, mock_db):
        """Test generating demand prediction"""
        # Mock historical data
        mock_analytics1 = Mock(spec=TripAnalytics)
        mock_analytics1.total_passengers = 25

        mock_analytics2 = Mock(spec=TripAnalytics)
        mock_analytics2.total_passengers = 30

        # Mock query chain
        mock_query = Mock()
        mock_query.join.return_value.filter.return_value.all.return_value = [mock_analytics1, mock_analytics2]
        mock_db.query.return_value = mock_query

        # Mock prediction storage
        mock_db.add = Mock()
        mock_db.commit = Mock()

        result = analytics_service.generate_demand_prediction(
            route_id=1,
            prediction_date=date.today() + timedelta(days=1)
        )

        assert result['route_id'] == 1
        assert result['predicted_demand'] > 0
        assert result['confidence_score'] >= 0
        assert result['confidence_score'] <= 1

    def test_generate_delay_prediction(self, analytics_service, mock_db):
        """Test generating delay prediction"""
        # Mock historical delay data
        mock_analytics1 = Mock(spec=TripAnalytics)
        mock_analytics1.delay_minutes = 5.0

        mock_analytics2 = Mock(spec=TripAnalytics)
        mock_analytics2.delay_minutes = 10.0

        # Mock trip data
        mock_trip1 = Mock(spec=Trip)
        mock_trip1.start_time = datetime.utcnow().replace(hour=8)  # Morning

        mock_trip2 = Mock(spec=Trip)
        mock_trip2.start_time = datetime.utcnow().replace(hour=9)  # Morning

        # Mock query chain
        mock_query = Mock()
        mock_query.join.return_value.filter.return_value.all.return_value = [mock_analytics1, mock_analytics2]
        mock_db.query.return_value = mock_query

        # Mock trip queries
        mock_trip_query = Mock()
        mock_trip_query.filter.return_value.first.side_effect = [mock_trip1, mock_trip2]
        mock_db.query.return_value = mock_trip_query

        # Mock prediction storage
        mock_db.add = Mock()
        mock_db.commit = Mock()

        result = analytics_service.generate_delay_prediction(
            route_id=1,
            prediction_date=date.today() + timedelta(days=1),
            time_of_day='morning'
        )

        assert result['route_id'] == 1
        assert result['predicted_delay_minutes'] > 0
        assert result['confidence_score'] >= 0
        assert result['confidence_score'] <= 1
        assert 'confidence_interval_lower' in result
        assert 'confidence_interval_upper' in result

    def test_haversine_distance_calculation(self, analytics_service):
        """Test Haversine distance calculation"""
        # Test distance between two known points
        lat1, lon1 = 12.9716, 77.5946  # Bangalore
        lat2, lon2 = 13.0827, 80.2707  # Chennai
        
        distance = analytics_service._haversine_distance(lat1, lon1, lat2, lon2)
        
        # Distance should be approximately 280-290 km
        assert 280 <= distance <= 290

    def test_calculate_demand_trend(self, analytics_service):
        """Test demand trend calculation"""
        # Test with increasing trend
        increasing_data = [10, 15, 20, 25, 30]
        trend = analytics_service._calculate_demand_trend(increasing_data)
        assert trend > 0

        # Test with decreasing trend
        decreasing_data = [30, 25, 20, 15, 10]
        trend = analytics_service._calculate_demand_trend(decreasing_data)
        assert trend < 0

        # Test with no trend
        constant_data = [20, 20, 20, 20, 20]
        trend = analytics_service._calculate_demand_trend(constant_data)
        assert trend == 0

    def test_calculate_co2_saved(self, analytics_service):
        """Test CO2 savings calculation"""
        passengers = 25
        distance_km = 10.0
        
        co2_saved = analytics_service._calculate_co2_saved(passengers, distance_km)
        
        # Should be positive (bus more efficient than cars)
        assert co2_saved > 0
        # Should be reasonable value (not too high or too low)
        assert 0 < co2_saved < 100  # kg CO2

    def test_estimate_fuel_efficiency(self, analytics_service):
        """Test fuel efficiency estimation"""
        distance_km = 50.0
        duration_minutes = 60.0  # 1 hour
        
        efficiency = analytics_service._estimate_fuel_efficiency(distance_km, duration_minutes)
        
        # Should be reasonable efficiency (3-5 km per liter)
        assert 3.0 <= efficiency <= 5.0

