"""
Tests for notification engine
"""
import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from app.services.notification_engine import (
    NotificationEngine,
    NotificationQueue
)
from app.services.notification_adapters import NotificationStatus
from app.models.subscription import NotificationChannel

class TestNotificationQueue:
    """Test notification queue functionality"""
    
    @pytest.fixture
    async def redis_mock(self):
        """Mock Redis client"""
        redis_mock = AsyncMock()
        redis_mock.zadd = AsyncMock(return_value=1)
        redis_mock.bzpopmin = AsyncMock()
        redis_mock.hset = AsyncMock(return_value=1)
        redis_mock.hdel = AsyncMock(return_value=1)
        redis_mock.zrem = AsyncMock(return_value=1)
        redis_mock.zcard = AsyncMock(return_value=0)
        redis_mock.hlen = AsyncMock(return_value=0)
        redis_mock.llen = AsyncMock(return_value=0)
        redis_mock.lpush = AsyncMock(return_value=1)
        redis_mock.zrangebyscore = AsyncMock(return_value=[])
        return redis_mock
    
    @pytest.fixture
    def queue(self, redis_mock):
        """Create notification queue for testing"""
        return NotificationQueue(redis_mock)
    
    @pytest.mark.asyncio
    async def test_enqueue_notification(self, queue, redis_mock):
        """Test enqueueing a notification"""
        notification_data = {
            'id': 'test_123',
            'phone': '+919876543210',
            'message': 'Test message',
            'channel': 'sms'
        }
        
        result = await queue.enqueue(notification_data, priority=0)
        
        assert result == True
        redis_mock.zadd.assert_called_once()
        
        # Check that the data was enriched
        call_args = redis_mock.zadd.call_args
        queue_key, data_dict = call_args[0]
        assert queue_key == queue.queue_key
        
        # Parse the JSON data
        json_data = list(data_dict.keys())[0]
        parsed_data = json.loads(json_data)
        assert parsed_data['id'] == 'test_123'
        assert 'queued_at' in parsed_data
        assert parsed_data['priority'] == 0
        assert parsed_data['retry_count'] == 0
    
    @pytest.mark.asyncio
    async def test_dequeue_notification(self, queue, redis_mock):
        """Test dequeuing a notification"""
        notification_data = {
            'id': 'test_123',
            'phone': '+919876543210',
            'message': 'Test message'
        }
        
        # Mock Redis response
        redis_mock.bzpopmin.return_value = (
            'notification_queue',
            json.dumps(notification_data),
            1234567890.0
        )
        
        result = await queue.dequeue(timeout=10)
        
        assert result == notification_data
        redis_mock.bzpopmin.assert_called_once_with(queue.queue_key, timeout=10)
        redis_mock.hset.assert_called_once_with(
            queue.processing_key,
            'test_123',
            json.dumps(notification_data)
        )
    
    @pytest.mark.asyncio
    async def test_dequeue_timeout(self, queue, redis_mock):
        """Test dequeue timeout"""
        redis_mock.bzpopmin.return_value = None
        
        result = await queue.dequeue(timeout=1)
        
        assert result is None
        redis_mock.bzpopmin.assert_called_once_with(queue.queue_key, timeout=1)
    
    @pytest.mark.asyncio
    async def test_mark_completed(self, queue, redis_mock):
        """Test marking notification as completed"""
        result = await queue.mark_completed('test_123')
        
        assert result == True
        redis_mock.hdel.assert_called_once_with(queue.processing_key, 'test_123')
    
    @pytest.mark.asyncio
    async def test_mark_failed_with_retry(self, queue, redis_mock):
        """Test marking notification as failed with retry"""
        notification_data = {
            'id': 'test_123',
            'retry_count': 0,
            'max_retries': 3
        }
        
        result = await queue.mark_failed(notification_data, 'Test error')
        
        assert result == True
        redis_mock.hdel.assert_called_once_with(queue.processing_key, 'test_123')
        redis_mock.zadd.assert_called_once()
        
        # Check retry queue was used
        call_args = redis_mock.zadd.call_args
        queue_key = call_args[0][0]
        assert queue_key == queue.retry_key
    
    @pytest.mark.asyncio
    async def test_mark_failed_max_retries(self, queue, redis_mock):
        """Test marking notification as failed after max retries"""
        notification_data = {
            'id': 'test_123',
            'retry_count': 3,
            'max_retries': 3
        }
        
        result = await queue.mark_failed(notification_data, 'Final error')
        
        assert result == True
        redis_mock.hdel.assert_called_once_with(queue.processing_key, 'test_123')
        redis_mock.lpush.assert_called_once()
        
        # Check DLQ was used
        call_args = redis_mock.lpush.call_args
        queue_key = call_args[0][0]
        assert queue_key == queue.dlq_key
    
    @pytest.mark.asyncio
    async def test_process_retries(self, queue, redis_mock):
        """Test processing retry notifications"""
        retry_data = {
            'id': 'test_123',
            'retry_count': 1
        }
        
        redis_mock.zrangebyscore.return_value = [
            (json.dumps(retry_data), 1234567890.0)
        ]
        
        count = await queue.process_retries()
        
        assert count == 1
        redis_mock.zrangebyscore.assert_called_once()
        redis_mock.zrem.assert_called_once_with(queue.retry_key, json.dumps(retry_data))
    
    @pytest.mark.asyncio
    async def test_get_queue_stats(self, queue, redis_mock):
        """Test getting queue statistics"""
        redis_mock.zcard.return_value = 5
        redis_mock.hlen.return_value = 2
        redis_mock.llen.return_value = 1
        
        stats = await queue.get_queue_stats()
        
        expected_stats = {
            'queued': 5,
            'processing': 2,
            'retry': 5,  # zcard called twice
            'dlq': 1
        }
        assert stats == expected_stats

class TestNotificationEngine:
    """Test notification engine functionality"""
    
    @pytest.fixture
    def engine(self):
        """Create notification engine for testing"""
        return NotificationEngine()
    
    @pytest.mark.asyncio
    async def test_initialize_demo_mode(self, engine):
        """Test initialization in demo mode"""
        with patch('app.services.notification_engine.settings') as mock_settings:
            mock_settings.DEMO_MODE = True
            mock_settings.REDIS_URL = 'redis://localhost:6379/0'
            
            with patch('redis.asyncio.from_url') as mock_redis:
                mock_redis_client = AsyncMock()
                mock_redis.return_value = mock_redis_client
                
                await engine.initialize()
                
                assert engine.redis_client == mock_redis_client
                assert 'simulated' in engine.adapters
                assert len(engine.adapters) == 1
    
    @pytest.mark.asyncio
    async def test_initialize_production_mode(self, engine):
        """Test initialization in production mode"""
        with patch('app.services.notification_engine.settings') as mock_settings:
            mock_settings.DEMO_MODE = False
            mock_settings.REDIS_URL = 'redis://localhost:6379/0'
            mock_settings.TWILIO_ACCOUNT_SID = 'test_sid'
            mock_settings.TWILIO_AUTH_TOKEN = 'test_token'
            mock_settings.EXOTEL_API_KEY = 'test_key'
            mock_settings.EXOTEL_API_TOKEN = 'test_token'
            
            with patch('redis.asyncio.from_url') as mock_redis:
                mock_redis_client = AsyncMock()
                mock_redis.return_value = mock_redis_client
                
                await engine.initialize()
                
                assert 'twilio' in engine.adapters
                assert 'exotel' in engine.adapters
                assert len(engine.adapters) == 2
    
    @pytest.mark.asyncio
    async def test_send_notification(self, engine):
        """Test sending a notification"""
        # Mock the queue
        mock_queue = AsyncMock()
        mock_queue.enqueue.return_value = True
        engine.queue = mock_queue
        
        with patch('app.services.notification_engine.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = iter([mock_db])
            
            notification_id = await engine.send_notification(
                phone='+919876543210',
                message='Test message',
                channel=NotificationChannel.SMS,
                subscription_id=123,
                priority=0
            )
            
            assert notification_id is not None
            assert notification_id.startswith('notif_')
            mock_queue.enqueue.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_start_stop_workers(self, engine):
        """Test starting and stopping workers"""
        engine.queue = AsyncMock()
        
        # Start workers
        await engine.start_workers(num_workers=2)
        
        assert engine.running == True
        assert len(engine.worker_tasks) == 3  # 2 workers + 1 retry processor
        
        # Stop workers
        await engine.stop_workers()
        
        assert engine.running == False
        assert len(engine.worker_tasks) == 0
    
    @pytest.mark.asyncio
    async def test_process_notification_sms(self, engine):
        """Test processing SMS notification"""
        # Mock adapter
        mock_adapter = AsyncMock()
        mock_result = Mock()
        mock_result.status = NotificationStatus.SENT
        mock_result.message_id = 'test_123'
        mock_adapter.send_sms.return_value = mock_result
        
        engine.adapters = {'simulated': mock_adapter}
        
        notification_data = {
            'id': 'test_123',
            'phone': '+919876543210',
            'message': 'Test message',
            'channel': NotificationChannel.SMS.value
        }
        
        with patch('app.services.notification_engine.settings') as mock_settings:
            mock_settings.DEMO_MODE = True
            
            result = await engine._process_notification(notification_data)
            
            assert result == True
            mock_adapter.send_sms.assert_called_once_with('+919876543210', 'Test message')
    
    @pytest.mark.asyncio
    async def test_process_notification_voice(self, engine):
        """Test processing voice notification"""
        # Mock adapter
        mock_adapter = AsyncMock()
        mock_result = Mock()
        mock_result.status = NotificationStatus.SENT
        mock_adapter.send_voice.return_value = mock_result
        
        engine.adapters = {'simulated': mock_adapter}
        
        notification_data = {
            'id': 'test_123',
            'phone': '+919876543210',
            'message': 'Test message',
            'channel': NotificationChannel.VOICE.value
        }
        
        with patch('app.services.notification_engine.settings') as mock_settings:
            mock_settings.DEMO_MODE = True
            
            result = await engine._process_notification(notification_data)
            
            assert result == True
            mock_adapter.send_voice.assert_called_once_with('+919876543210', 'Test message')
    
    @pytest.mark.asyncio
    async def test_process_notification_whatsapp(self, engine):
        """Test processing WhatsApp notification"""
        # Mock adapter
        mock_adapter = AsyncMock()
        mock_result = Mock()
        mock_result.status = NotificationStatus.SENT
        mock_adapter.send_whatsapp.return_value = mock_result
        
        engine.adapters = {'simulated': mock_adapter}
        
        notification_data = {
            'id': 'test_123',
            'phone': '+919876543210',
            'message': 'Test message',
            'channel': NotificationChannel.WHATSAPP.value
        }
        
        with patch('app.services.notification_engine.settings') as mock_settings:
            mock_settings.DEMO_MODE = True
            
            result = await engine._process_notification(notification_data)
            
            assert result == True
            mock_adapter.send_whatsapp.assert_called_once_with('+919876543210', 'Test message')
    
    @pytest.mark.asyncio
    async def test_process_notification_failure(self, engine):
        """Test processing notification failure"""
        # Mock adapter
        mock_adapter = AsyncMock()
        mock_result = Mock()
        mock_result.status = NotificationStatus.FAILED
        mock_result.error_message = 'Test error'
        mock_adapter.send_sms.return_value = mock_result
        
        engine.adapters = {'simulated': mock_adapter}
        
        notification_data = {
            'id': 'test_123',
            'phone': '+919876543210',
            'message': 'Test message',
            'channel': NotificationChannel.SMS.value
        }
        
        with patch('app.services.notification_engine.settings') as mock_settings:
            mock_settings.DEMO_MODE = True
            
            result = await engine._process_notification(notification_data)
            
            assert result == False
    
    def test_select_adapter_demo_mode(self, engine):
        """Test adapter selection in demo mode"""
        engine.adapters = {'simulated': Mock()}
        
        with patch('app.services.notification_engine.settings') as mock_settings:
            mock_settings.DEMO_MODE = True
            
            adapter = engine._select_adapter(NotificationChannel.SMS.value)
            assert adapter == engine.adapters['simulated']
    
    def test_select_adapter_production_sms(self, engine):
        """Test adapter selection for SMS in production"""
        mock_twilio = Mock()
        mock_exotel = Mock()
        engine.adapters = {'twilio': mock_twilio, 'exotel': mock_exotel}
        
        with patch('app.services.notification_engine.settings') as mock_settings:
            mock_settings.DEMO_MODE = False
            
            adapter = engine._select_adapter(NotificationChannel.SMS.value)
            assert adapter == mock_twilio  # Twilio has priority
    
    def test_select_adapter_production_whatsapp(self, engine):
        """Test adapter selection for WhatsApp in production"""
        mock_twilio = Mock()
        mock_exotel = Mock()
        engine.adapters = {'twilio': mock_twilio, 'exotel': mock_exotel}
        
        with patch('app.services.notification_engine.settings') as mock_settings:
            mock_settings.DEMO_MODE = False
            
            adapter = engine._select_adapter(NotificationChannel.WHATSAPP.value)
            assert adapter == mock_twilio  # Only Twilio supports WhatsApp
    
    @pytest.mark.asyncio
    async def test_get_stats(self, engine):
        """Test getting engine statistics"""
        mock_queue = AsyncMock()
        mock_queue.get_queue_stats.return_value = {
            'queued': 5,
            'processing': 2,
            'retry': 1,
            'dlq': 0
        }
        engine.queue = mock_queue
        engine.adapters = {'simulated': Mock()}
        engine.worker_tasks = [Mock(), Mock()]
        
        with patch('app.services.notification_engine.settings') as mock_settings:
            mock_settings.DEMO_MODE = True
            
            stats = await engine.get_stats()
            
            expected_stats = {
                'queue_stats': {
                    'queued': 5,
                    'processing': 2,
                    'retry': 1,
                    'dlq': 0
                },
                'adapters': ['simulated'],
                'workers_running': 2,
                'demo_mode': True
            }
            assert stats == expected_stats