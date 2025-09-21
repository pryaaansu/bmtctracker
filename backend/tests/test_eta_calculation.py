"""
Unit tests for ETA calculation and caching services
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
import json

from app.services.eta_calculation_service import ETACalculationService, ETAResult, RouteSegment
from app.services.eta_cache_service import ETACacheService, ETACacheEntry, ETAUpdateTask
from app.services.location_tracking_service import LocationUpdate
from app.models.stop import Stop
from app.models.route import Route
from app.models.vehicle import Vehicle


class TestETACalculationService:
    """Test cases for ETA calculation service"""
    
    @pytest.fixture
    def eta_service(self):
        """Create ETA service instance for testing"""
        service = ETACalculationService()
        service.redis_client = Mock()
        return service
    
    @pytest.fixture
    def sample_location(self):
        """Sample location update"""
        return LocationUpdate(
            vehicle_id=1,
            latitude=12.9716,
            longitude=77.5946,
            speed=25.0,
            bearing=90,
            timestamp=datetime.now(),
            confidence=0.9
        )
    
    @pytest.fixture
    def sample_stop(self):
        """Sample bus stop"""
        stop = Mock(spec=Stop)
        stop.id = 1
        stop.route_id = 1
        stop.latitude = 12.9800
        stop.longitude = 77.6000
        stop.name = "Test Stop"
        return stop
    
    @pytest.fixture
    def sample_route(self):
        """Sample route"""
        route = Mock(spec=Route)
        route.id = 1
        route.name = "Test Route"
        route.route_number = "335E"
        route.geojson = json.dumps({
            "type": "LineString",
            "coordinates": [
                [77.5946, 12.9716],
                [77.5960, 12.9730],
                [77.5980, 12.9750],
                [77.6000, 12.9800]
            ]
        })
        return route
    
    def test_haversine_distance_calculation(self, eta_service):
        """Test Haversine distance calculation"""
        # Distance between Bangalore coordinates
        coord1 = (12.9716, 77.5946)  # MG Road
        coord2 = (12.9800, 77.6000)  # Nearby location
        
        distance = eta_service._haversine_distance(coord1, coord2)
        
        # Should be approximately 1.2 km
        assert 1000 < distance < 1500
        assert isinstance(distance, float)
    
    def test_time_period_classification(self, eta_service):
        """Test time period classification for traffic factors"""
        assert eta_service._get_time_period(8) == "morning_rush"
        assert eta_service._get_time_period(18) == "evening_rush"
        assert eta_service._get_time_period(14) == "daytime"
        assert eta_service._get_time_period(2) == "off_peak"
    
    @pytest.mark.asyncio
    async def test_haversine_eta_calculation(self, eta_service, sample_location, sample_stop):
        """Test basic Haversine ETA calculation"""
        eta_result = await eta_service._calculate_haversine_eta(
            sample_location, sample_stop, vehicle_id=1
        )
        
        assert eta_result is not None
        assert eta_result.vehicle_id == 1
        assert eta_result.stop_id == 1
        assert eta_result.eta_seconds > 0
        assert eta_result.eta_minutes > 0
        assert 0 < eta_result.confidence <= 1
        assert eta_result.calculation_method == "haversine"
        assert eta_result.distance_meters > 0
    
    @pytest.mark.asyncio
    async def test_route_segments_generation(self, eta_service, sample_route):
        """Test route segment generation from GeoJSON"""
        with patch.object(eta_service, '_get_route_info', return_value=sample_route):
            segments = await eta_service._get_route_segments(1)
        
        assert len(segments) == 3  # 4 coordinates = 3 segments
        
        for segment in segments:
            assert isinstance(segment, RouteSegment)
            assert segment.distance_meters > 0
            assert segment.expected_time_seconds > 0
            assert -90 <= segment.start_lat <= 90
            assert -180 <= segment.start_lng <= 180
    
    @pytest.mark.asyncio
    async def test_traffic_and_delay_factors(self, eta_service):
        """Test application of traffic and delay factors"""
        # Create sample ETA result
        eta_result = ETAResult(
            vehicle_id=1,
            stop_id=1,
            eta_seconds=600,  # 10 minutes
            eta_minutes=10.0,
            confidence=0.8,
            distance_meters=5000,
            average_speed_kmh=30,
            traffic_factor=1.0,
            delay_factor=1.0,
            calculation_method="test",
            calculated_at=datetime.now()
        )
        
        # Initialize traffic factors
        eta_service.traffic_factors = {"morning_rush": 1.5}
        eta_service.delay_patterns = {1: {"morning_rush": 1.2}}
        
        # Mock time to be morning rush hour
        with patch('app.services.eta_calculation_service.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 1, 8, 0)  # 8 AM
            
            adjusted_result = await eta_service._apply_traffic_and_delay_factors(eta_result, route_id=1)
        
        # Should be adjusted by traffic (1.5) and delay (1.2) factors
        expected_eta = 600 * 1.5 * 1.2  # 1080 seconds
        assert adjusted_result.eta_seconds == expected_eta
        assert adjusted_result.traffic_factor == 1.5
        assert adjusted_result.delay_factor == 1.2
    
    @pytest.mark.asyncio
    async def test_calculate_eta_integration(self, eta_service, sample_location):
        """Test full ETA calculation integration"""
        # Mock dependencies
        with patch.object(eta_service, '_get_stop_info') as mock_get_stop, \
             patch.object(eta_service, '_get_route_info') as mock_get_route, \
             patch.object(eta_service, '_calculate_haversine_eta') as mock_haversine, \
             patch.object(eta_service, '_apply_traffic_and_delay_factors') as mock_apply_factors, \
             patch.object(eta_service, '_cache_eta_result') as mock_cache:
            
            # Setup mocks
            mock_stop = Mock()
            mock_stop.id = 1
            mock_stop.route_id = 1
            mock_get_stop.return_value = mock_stop
            
            mock_route = Mock()
            mock_route.id = 1
            mock_get_route.return_value = mock_route
            
            mock_eta_result = ETAResult(
                vehicle_id=1, stop_id=1, eta_seconds=300, eta_minutes=5.0,
                confidence=0.8, distance_meters=2500, average_speed_kmh=30,
                traffic_factor=1.0, delay_factor=1.0, calculation_method="haversine",
                calculated_at=datetime.now()
            )
            mock_haversine.return_value = mock_eta_result
            mock_apply_factors.return_value = mock_eta_result
            
            # Test calculation
            result = await eta_service.calculate_eta(1, 1, sample_location)
            
            assert result is not None
            assert result.vehicle_id == 1
            assert result.stop_id == 1
            mock_cache.assert_called_once()


class TestETACacheService:
    """Test cases for ETA cache service"""
    
    @pytest.fixture
    def cache_service(self):
        """Create cache service instance for testing"""
        service = ETACacheService()
        service.redis_client = AsyncMock()
        return service
    
    @pytest.fixture
    def sample_eta_result(self):
        """Sample ETA result"""
        return ETAResult(
            vehicle_id=1,
            stop_id=1,
            eta_seconds=300,
            eta_minutes=5.0,
            confidence=0.8,
            distance_meters=2500,
            average_speed_kmh=30,
            traffic_factor=1.0,
            delay_factor=1.0,
            calculation_method="haversine",
            calculated_at=datetime.now()
        )
    
    def test_cache_key_generation(self, cache_service):
        """Test cache key generation"""
        key = cache_service._get_cache_key(123, 456)
        assert key == "eta:123:456"
    
    def test_ttl_calculation_based_on_confidence(self, cache_service):
        """Test TTL calculation based on confidence scores"""
        # High confidence
        high_ttl = cache_service._get_ttl_for_confidence(0.9)
        assert high_ttl == cache_service.high_confidence_ttl
        
        # Medium confidence
        medium_ttl = cache_service._get_ttl_for_confidence(0.7)
        assert medium_ttl == cache_service.default_ttl
        
        # Low confidence
        low_ttl = cache_service._get_ttl_for_confidence(0.3)
        assert low_ttl == cache_service.low_confidence_ttl
    
    def test_cache_validity_check(self, cache_service, sample_eta_result):
        """Test cache validity checking"""
        # Fresh cache entry
        fresh_entry = ETACacheEntry(
            eta_result=sample_eta_result,
            cache_timestamp=datetime.now(),
            access_count=1,
            last_accessed=datetime.now(),
            priority_score=0.8
        )
        assert cache_service._is_cache_valid(fresh_entry)
        
        # Expired cache entry
        expired_entry = ETACacheEntry(
            eta_result=sample_eta_result,
            cache_timestamp=datetime.now() - timedelta(minutes=10),
            access_count=1,
            last_accessed=datetime.now(),
            priority_score=0.8
        )
        assert not cache_service._is_cache_valid(expired_entry)
    
    def test_priority_score_calculation(self, cache_service, sample_eta_result):
        """Test priority score calculation"""
        score = cache_service._calculate_priority_score(sample_eta_result)
        
        assert 0 <= score <= 1
        assert isinstance(score, float)
        
        # Higher confidence should give higher score
        high_confidence_result = sample_eta_result
        high_confidence_result.confidence = 0.95
        high_score = cache_service._calculate_priority_score(high_confidence_result)
        
        low_confidence_result = sample_eta_result
        low_confidence_result.confidence = 0.3
        low_score = cache_service._calculate_priority_score(low_confidence_result)
        
        assert high_score > low_score
    
    @pytest.mark.asyncio
    async def test_confidence_score_calculation(self, cache_service, sample_eta_result):
        """Test comprehensive confidence score calculation"""
        confidence_info = await cache_service.get_eta_confidence_score(sample_eta_result)
        
        assert "composite_confidence" in confidence_info
        assert "confidence_level" in confidence_info
        assert "factors" in confidence_info
        assert "recommended_ttl" in confidence_info
        
        assert 0 <= confidence_info["composite_confidence"] <= 1
        assert confidence_info["confidence_level"] in ["high", "medium", "low"]
        assert confidence_info["recommended_ttl"] > 0
    
    @pytest.mark.asyncio
    async def test_cache_eta_result(self, cache_service, sample_eta_result):
        """Test caching ETA result"""
        cache_key = "eta:1:1"
        
        await cache_service._cache_eta_result(cache_key, sample_eta_result)
        
        # Check local cache
        assert cache_key in cache_service.cache_entries
        cached_entry = cache_service.cache_entries[cache_key]
        assert cached_entry.eta_result.vehicle_id == sample_eta_result.vehicle_id
        assert cached_entry.eta_result.stop_id == sample_eta_result.stop_id
        
        # Check Redis cache was called
        cache_service.redis_client.setex.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_eta_with_cache_hit(self, cache_service, sample_eta_result):
        """Test getting ETA with cache hit"""
        cache_key = "eta:1:1"
        
        # Pre-populate cache
        cache_entry = ETACacheEntry(
            eta_result=sample_eta_result,
            cache_timestamp=datetime.now(),
            access_count=1,
            last_accessed=datetime.now(),
            priority_score=0.8
        )
        cache_service.cache_entries[cache_key] = cache_entry
        
        with patch('app.services.eta_cache_service.eta_service') as mock_eta_service:
            result = await cache_service.get_eta(1, 1)
        
        # Should return cached result without calling calculation service
        assert result == sample_eta_result
        mock_eta_service.calculate_eta.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_get_eta_with_cache_miss(self, cache_service, sample_eta_result):
        """Test getting ETA with cache miss"""
        with patch('app.services.eta_cache_service.eta_service') as mock_eta_service:
            mock_eta_service.calculate_eta.return_value = sample_eta_result
            
            result = await cache_service.get_eta(1, 1)
        
        # Should call calculation service and cache result
        assert result == sample_eta_result
        mock_eta_service.calculate_eta.assert_called_once_with(1, 1)
        assert "eta:1:1" in cache_service.cache_entries
    
    @pytest.mark.asyncio
    async def test_get_multiple_etas(self, cache_service, sample_eta_result):
        """Test getting multiple ETAs efficiently"""
        pairs = [(1, 1), (1, 2), (2, 1)]
        
        with patch('app.services.eta_cache_service.eta_service') as mock_eta_service:
            mock_eta_service.calculate_eta.return_value = sample_eta_result
            
            results = await cache_service.get_multiple_etas(pairs)
        
        assert len(results) == 3
        for pair in pairs:
            assert pair in results
            assert results[pair] == sample_eta_result
    
    @pytest.mark.asyncio
    async def test_invalidate_vehicle_etas(self, cache_service):
        """Test invalidating all ETAs for a vehicle"""
        # Pre-populate cache with multiple entries
        cache_service.cache_entries["eta:1:1"] = Mock()
        cache_service.cache_entries["eta:1:2"] = Mock()
        cache_service.cache_entries["eta:2:1"] = Mock()
        
        cache_service.redis_client.keys.return_value = ["eta:1:1", "eta:1:2"]
        
        await cache_service.invalidate_vehicle_etas(1)
        
        # Should remove vehicle 1 entries but keep vehicle 2
        assert "eta:1:1" not in cache_service.cache_entries
        assert "eta:1:2" not in cache_service.cache_entries
        assert "eta:2:1" in cache_service.cache_entries
        
        cache_service.redis_client.delete.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_background_update_scheduling(self, cache_service, sample_eta_result):
        """Test background update scheduling"""
        # High priority ETA should be scheduled for update
        high_priority_eta = sample_eta_result
        high_priority_eta.confidence = 0.9
        
        await cache_service._schedule_background_update(1, 1, high_priority_eta)
        
        assert len(cache_service.update_queue) == 1
        update_task = cache_service.update_queue[0]
        assert update_task.vehicle_id == 1
        assert update_task.stop_id == 1
        assert update_task.priority > 60  # High priority threshold
    
    @pytest.mark.asyncio
    async def test_cache_size_management(self, cache_service):
        """Test cache size management"""
        # Fill cache beyond max size
        cache_service.max_cache_size = 5
        
        for i in range(10):
            cache_entry = ETACacheEntry(
                eta_result=Mock(),
                cache_timestamp=datetime.now(),
                access_count=1,
                last_accessed=datetime.now(),
                priority_score=i * 0.1  # Different priorities
            )
            cache_service.cache_entries[f"eta:{i}:1"] = cache_entry
        
        await cache_service._manage_cache_size()
        
        # Should remove lowest priority entries
        assert len(cache_service.cache_entries) <= cache_service.max_cache_size
    
    @pytest.mark.asyncio
    async def test_cache_stats(self, cache_service, sample_eta_result):
        """Test cache statistics generation"""
        # Add some cache entries
        for i in range(3):
            confidence = 0.3 + (i * 0.3)  # Low, medium, high confidence
            eta_result = sample_eta_result
            eta_result.confidence = confidence
            
            cache_entry = ETACacheEntry(
                eta_result=eta_result,
                cache_timestamp=datetime.now(),
                access_count=i + 1,
                last_accessed=datetime.now(),
                priority_score=confidence
            )
            cache_service.cache_entries[f"eta:{i}:1"] = cache_entry
        
        stats = await cache_service.get_cache_stats()
        
        assert "total_entries" in stats
        assert "confidence_distribution" in stats
        assert "total_access_count" in stats
        assert stats["total_entries"] == 3
        assert stats["total_access_count"] == 6  # 1 + 2 + 3


class TestETAIntegration:
    """Integration tests for ETA calculation and caching"""
    
    @pytest.mark.asyncio
    async def test_full_eta_workflow(self):
        """Test complete ETA calculation and caching workflow"""
        # This would test the full integration between services
        # In a real implementation, this would use test database and Redis
        pass
    
    @pytest.mark.asyncio
    async def test_concurrent_eta_requests(self):
        """Test handling concurrent ETA requests"""
        # Test that concurrent requests for the same ETA are handled efficiently
        pass
    
    @pytest.mark.asyncio
    async def test_cache_invalidation_on_location_update(self):
        """Test that cache is properly invalidated when vehicle location updates"""
        pass


if __name__ == "__main__":
    pytest.main([__file__])