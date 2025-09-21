"""
Tests for geofence service and trigger system
"""
import pytest
import math
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from app.services.geofence_service import (
    GeofenceCalculator,
    NotificationTriggerEngine,
    GeofenceService,
    GeofenceEvent
)
from app.models.subscription import Subscription, NotificationChannel
from app.models.stop import Stop
from app.models.vehicle import Vehicle

class TestGeofenceCalculator:
    """Test geofence calculation functionality"""
    
    @pytest.fixture
    def calculator(self):
        """Create geofence calculator for testing"""
        return GeofenceCalculator()
    
    def test_haversine_distance_same_point(self, calculator):
        """Test distance calculation for same point"""
        distance = calculator.haversine_distance(12.9716, 77.5946, 12.9716, 77.5946)
        assert distance == 0.0
    
    def test_haversine_distance_known_points(self, calculator):
        """Test distance calculation for known points"""
        # Distance between Bangalore and Mysore (approximately 150km)
        bangalore_lat, bangalore_lon = 12.9716, 77.5946
        mysore_lat, mysore_lon = 12.2958, 76.6394
        
        distance = calculator.haversine_distance(
            bangalore_lat, bangalore_lon, mysore_lat, mysore_lon
        )
        
        # Should be approximately 150,000 meters (150km)
        assert 140000 < distance < 160000
    
    def test_calculate_bearing_north(self, calculator):
        """Test bearing calculation for northward direction"""
        # Point A to Point B (north)
        bearing = calculator.calculate_bearing(12.9716, 77.5946, 13.0716, 77.5946)
        
        # Should be approximately 0 degrees (north)
        assert -5 < bearing < 5 or 355 < bearing < 365
    
    def test_calculate_bearing_east(self, calculator):
        """Test bearing calculation for eastward direction"""
        # Point A to Point B (east)
        bearing = calculator.calculate_bearing(12.9716, 77.5946, 12.9716, 77.6946)
        
        # Should be approximately 90 degrees (east)
        assert 85 < bearing < 95
    
    def test_is_approaching_true(self, calculator):
        """Test approaching detection when vehicle is approaching"""
        # Vehicle moving east (90 degrees) towards a stop that's east
        vehicle_lat, vehicle_lon = 12.9716, 77.5946
        vehicle_bearing = 90
        stop_lat, stop_lon = 12.9716, 77.6046  # East of vehicle
        
        is_approaching = calculator.is_approaching(
            vehicle_lat, vehicle_lon, vehicle_bearing,
            stop_lat, stop_lon
        )
        
        assert is_approaching == True
    
    def test_is_approaching_false(self, calculator):
        """Test approaching detection when vehicle is not approaching"""
        # Vehicle moving east (90 degrees) but stop is west
        vehicle_lat, vehicle_lon = 12.9716, 77.5946
        vehicle_bearing = 90
        stop_lat, stop_lon = 12.9716, 77.5846  # West of vehicle
        
        is_approaching = calculator.is_approaching(
            vehicle_lat, vehicle_lon, vehicle_bearing,
            stop_lat, stop_lon
        )
        
        assert is_approaching == False
    
    def test_calculate_eta_from_distance(self, calculator):
        """Test ETA calculation from distance and speed"""
        # 1000 meters at 20 km/h should take 3 minutes
        eta = calculator.calculate_eta_from_distance(1000, 20)
        assert eta == 3
        
        # 500 meters at 30 km/h should take 1 minute
        eta = calculator.calculate_eta_from_distance(500, 30)
        assert eta == 1
        
        # Zero speed should use default speed
        eta = calculator.calculate_eta_from_distance(1000, 0)
        assert eta > 0
    
    def test_check_geofence_events_within_range(self, calculator):
        """Test geofence event detection within range"""
        # Create mock vehicle location
        vehicle_locations = [{
            'vehicle_id': 1,
            'latitude': 12.9716,
            'longitude': 77.5946,
            'speed': 25,
            'bearing': 90,
            'timestamp': datetime.now()
        }]
        
        # Create mock stop nearby (about 100m away)
        stop = Mock(spec=Stop)
        stop.id = 1
        stop.latitude = 12.9726  # Slightly north
        stop.longitude = 77.5946
        
        events = calculator.check_geofence_events(vehicle_locations, [stop])
        
        assert len(events) == 1
        assert events[0].vehicle_id == 1
        assert events[0].stop_id == 1
        assert events[0].distance_meters < 200
        assert events[0].eta_minutes > 0
        assert events[0].confidence > 0.6
    
    def test_check_geofence_events_too_far(self, calculator):
        """Test geofence event detection when too far"""
        # Create mock vehicle location
        vehicle_locations = [{
            'vehicle_id': 1,
            'latitude': 12.9716,
            'longitude': 77.5946,
            'speed': 25,
            'bearing': 90,
            'timestamp': datetime.now()
        }]
        
        # Create mock stop far away (about 1km away)
        stop = Mock(spec=Stop)
        stop.id = 1
        stop.latitude = 12.9816  # Much further north
        stop.longitude = 77.5946
        
        events = calculator.check_geofence_events(vehicle_locations, [stop])
        
        # Should not generate events for stops too far away
        assert len(events) == 0

class TestNotificationTriggerEngine:
    """Test notification trigger engine"""
    
    @pytest.fixture
    def trigger_engine(self):
        """Create trigger engine for testing"""
        return NotificationTriggerEngine()
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database session"""
        return Mock()
    
    @pytest.fixture
    def sample_geofence_event(self):
        """Create sample geofence event"""
        return GeofenceEvent(
            vehicle_id=1,
            stop_id=1,
            distance_meters=100,
            eta_minutes=3,
            event_type='entering',
            timestamp=datetime.now(),
            confidence=0.85
        )
    
    @pytest.fixture
    def sample_subscription(self):
        """Create sample subscription"""
        subscription = Mock(spec=Subscription)
        subscription.id = 1
        subscription.phone = '+919876543210'
        subscription.channel = NotificationChannel.SMS
        subscription.eta_threshold = 5
        subscription.is_active = True
        return subscription
    
    def test_should_trigger_notification_valid(self, trigger_engine, sample_geofence_event, sample_subscription):
        """Test trigger decision for valid notification"""
        should_trigger = trigger_engine._should_trigger_notification(
            sample_geofence_event, sample_subscription
        )
        
        assert should_trigger == True
    
    def test_should_trigger_notification_eta_too_high(self, trigger_engine, sample_subscription):
        """Test trigger decision when ETA exceeds threshold"""
        event = GeofenceEvent(
            vehicle_id=1,
            stop_id=1,
            distance_meters=1000,
            eta_minutes=10,  # Exceeds threshold of 5
            event_type='entering',
            timestamp=datetime.now(),
            confidence=0.85
        )
        
        should_trigger = trigger_engine._should_trigger_notification(event, sample_subscription)
        
        assert should_trigger == False
    
    def test_should_trigger_notification_low_confidence(self, trigger_engine, sample_subscription):
        """Test trigger decision with low confidence"""
        event = GeofenceEvent(
            vehicle_id=1,
            stop_id=1,
            distance_meters=100,
            eta_minutes=3,
            event_type='entering',
            timestamp=datetime.now(),
            confidence=0.5  # Below threshold of 0.6
        )
        
        should_trigger = trigger_engine._should_trigger_notification(event, sample_subscription)
        
        assert should_trigger == False
    
    def test_should_trigger_notification_rate_limited(self, trigger_engine, sample_geofence_event, sample_subscription):
        """Test trigger decision with rate limiting"""
        # First trigger should work
        should_trigger = trigger_engine._should_trigger_notification(
            sample_geofence_event, sample_subscription
        )
        assert should_trigger == True
        
        # Add to active triggers
        trigger_key = f"{sample_subscription.id}_{sample_geofence_event.vehicle_id}_{sample_geofence_event.stop_id}"
        trigger_engine.active_triggers[trigger_key] = datetime.now()
        
        # Second trigger should be rate limited
        should_trigger = trigger_engine._should_trigger_notification(
            sample_geofence_event, sample_subscription
        )
        assert should_trigger == False
    
    def test_create_notification_message_sms(self, trigger_engine, sample_geofence_event):
        """Test SMS notification message creation"""
        vehicle = Mock(spec=Vehicle)
        vehicle.vehicle_number = 'KA01AB1234'
        
        stop = {
            'name': 'Majestic',
            'name_kannada': 'ಮೆಜೆಸ್ಟಿಕ್',
            'route': {
                'route_number': '500D'
            }
        }
        
        message = trigger_engine._create_notification_message(
            sample_geofence_event, vehicle, stop, NotificationChannel.SMS
        )
        
        assert 'KA01AB1234' in message
        assert '500D' in message
        assert 'Majestic' in message
        assert '3 min' in message
    
    def test_create_notification_message_voice(self, trigger_engine, sample_geofence_event):
        """Test voice notification message creation"""
        vehicle = Mock(spec=Vehicle)
        vehicle.vehicle_number = 'KA01AB1234'
        
        stop = {
            'name': 'Majestic',
            'route': {
                'route_number': '500D'
            }
        }
        
        message = trigger_engine._create_notification_message(
            sample_geofence_event, vehicle, stop, NotificationChannel.VOICE
        )
        
        assert 'KA01AB1234' in message
        assert '500D' in message
        assert 'Majestic' in message
        assert '3 minutes' in message
        # Voice messages should be simpler
        assert 'arriving at' in message.lower()
    
    def test_create_notification_message_whatsapp(self, trigger_engine, sample_geofence_event):
        """Test WhatsApp notification message creation"""
        vehicle = Mock(spec=Vehicle)
        vehicle.vehicle_number = 'KA01AB1234'
        
        stop = {
            'name': 'Majestic',
            'name_kannada': 'ಮೆಜೆಸ್ಟಿಕ್',
            'route': {
                'route_number': '500D'
            }
        }
        
        message = trigger_engine._create_notification_message(
            sample_geofence_event, vehicle, stop, NotificationChannel.WHATSAPP
        )
        
        assert 'KA01AB1234' in message
        assert '500D' in message
        assert 'Majestic' in message
        assert 'ಮೆಜೆಸ್ಟಿಕ್' in message
        assert '*Bus Alert*' in message  # WhatsApp formatting
    
    def test_create_notification_message_urgent(self, trigger_engine):
        """Test urgent notification message creation"""
        urgent_event = GeofenceEvent(
            vehicle_id=1,
            stop_id=1,
            distance_meters=50,
            eta_minutes=1,  # Very urgent
            event_type='within',
            timestamp=datetime.now(),
            confidence=0.95
        )
        
        vehicle = Mock(spec=Vehicle)
        vehicle.vehicle_number = 'KA01AB1234'
        
        stop = {
            'name': 'Majestic',
            'route': {
                'route_number': '500D'
            }
        }
        
        message = trigger_engine._create_notification_message(
            urgent_event, vehicle, stop, NotificationChannel.SMS
        )
        
        # Should contain urgency indicator
        assert 'Hurry' in message or '🏃‍♂️' in message
    
    def test_cleanup_old_triggers(self, trigger_engine):
        """Test cleanup of old trigger records"""
        # Add some old triggers
        old_time = datetime.now() - timedelta(hours=2)
        recent_time = datetime.now() - timedelta(minutes=5)
        
        trigger_engine.active_triggers = {
            'old_trigger': old_time,
            'recent_trigger': recent_time
        }
        
        trigger_engine.trigger_history = {
            'sub_1': [old_time, recent_time],
            'sub_2': [old_time]  # Only old entries
        }
        
        trigger_engine.cleanup_old_triggers()
        
        # Old active trigger should be removed
        assert 'old_trigger' not in trigger_engine.active_triggers
        assert 'recent_trigger' in trigger_engine.active_triggers
        
        # Old history entries should be removed
        assert len(trigger_engine.trigger_history['sub_1']) == 1
        assert 'sub_2' not in trigger_engine.trigger_history

class TestGeofenceService:
    """Test main geofence service"""
    
    @pytest.fixture
    def geofence_service(self):
        """Create geofence service for testing"""
        from app.services.geofence_service import GeofenceService
        return GeofenceService()
    
    @pytest.mark.asyncio
    async def test_process_vehicle_locations(self, geofence_service):
        """Test processing vehicle locations"""
        vehicle_locations = [{
            'vehicle_id': 1,
            'latitude': 12.9716,
            'longitude': 77.5946,
            'speed': 25,
            'bearing': 90,
            'timestamp': datetime.now()
        }]
        
        with patch('app.services.geofence_service.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = iter([mock_db])
            
            with patch.object(geofence_service.trigger_engine.geofence_calculator, 'check_geofence_events') as mock_check:
                mock_check.return_value = []
                
                with patch.object(geofence_service.trigger_engine, 'evaluate_triggers') as mock_evaluate:
                    mock_evaluate.return_value = []
                    
                    notifications = await geofence_service.process_vehicle_locations(vehicle_locations)
                    
                    assert isinstance(notifications, list)
                    mock_check.assert_called_once()
                    mock_evaluate.assert_called_once()
    
    def test_get_proximity_stats(self, geofence_service):
        """Test getting proximity statistics"""
        # Add some test data
        geofence_service.trigger_engine.active_triggers = {'test': datetime.now()}
        geofence_service.trigger_engine.trigger_history = {'sub_1': [datetime.now()]}
        
        stats = geofence_service.get_proximity_stats()
        
        assert 'active_triggers' in stats
        assert 'trigger_history_entries' in stats
        assert 'last_cleanup' in stats
        assert stats['active_triggers'] == 1
        assert stats['trigger_history_entries'] == 1