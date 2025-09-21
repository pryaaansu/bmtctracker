"""
Tests for notification adapters
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from app.services.notification_adapters import (
    NotificationAdapter,
    TwilioAdapter,
    ExotelAdapter,
    SimulatedAdapter,
    NotificationAdapterFactory,
    NotificationResult,
    NotificationStatus
)
from app.models.subscription import NotificationChannel

class TestNotificationAdapterFactory:
    """Test notification adapter factory"""
    
    def test_create_twilio_adapter(self):
        """Test creating Twilio adapter"""
        config = {
            'account_sid': 'test_sid',
            'auth_token': 'test_token',
            'from_number': '+1234567890'
        }
        
        adapter = NotificationAdapterFactory.create_adapter('twilio', config)
        assert isinstance(adapter, TwilioAdapter)
        assert adapter.account_sid == 'test_sid'
        assert adapter.auth_token == 'test_token'
    
    def test_create_exotel_adapter(self):
        """Test creating Exotel adapter"""
        config = {
            'api_key': 'test_key',
            'api_token': 'test_token',
            'account_sid': 'test_sid'
        }
        
        adapter = NotificationAdapterFactory.create_adapter('exotel', config)
        assert isinstance(adapter, ExotelAdapter)
        assert adapter.api_key == 'test_key'
        assert adapter.api_token == 'test_token'
    
    def test_create_simulated_adapter(self):
        """Test creating simulated adapter"""
        config = {'simulate_delay': False, 'failure_rate': 0.0}
        
        adapter = NotificationAdapterFactory.create_adapter('simulated', config)
        assert isinstance(adapter, SimulatedAdapter)
        assert adapter.simulate_delay == False
        assert adapter.failure_rate == 0.0
    
    def test_create_invalid_adapter(self):
        """Test creating invalid adapter type"""
        with pytest.raises(ValueError, match="Unknown adapter type"):
            NotificationAdapterFactory.create_adapter('invalid', {})
    
    def test_get_available_adapters(self):
        """Test getting available adapter types"""
        adapters = NotificationAdapterFactory.get_available_adapters()
        assert 'twilio' in adapters
        assert 'exotel' in adapters
        assert 'simulated' in adapters

class TestSimulatedAdapter:
    """Test simulated notification adapter"""
    
    @pytest.fixture
    def adapter(self):
        """Create simulated adapter for testing"""
        config = {'simulate_delay': False, 'failure_rate': 0.0}
        return SimulatedAdapter(config)
    
    @pytest.fixture
    def failing_adapter(self):
        """Create simulated adapter that always fails"""
        config = {'simulate_delay': False, 'failure_rate': 1.0}
        return SimulatedAdapter(config)
    
    @pytest.mark.asyncio
    async def test_send_sms_success(self, adapter):
        """Test successful SMS sending"""
        result = await adapter.send_sms('+919876543210', 'Test message')
        
        assert result.status == NotificationStatus.SENT
        assert result.message_id is not None
        assert result.message_id.startswith('sim_sms_')
        assert result.cost == 0.05
        assert result.metadata['provider'] == 'simulated'
        assert result.metadata['type'] == 'sms'
    
    @pytest.mark.asyncio
    async def test_send_voice_success(self, adapter):
        """Test successful voice call"""
        result = await adapter.send_voice('+919876543210', 'Test message')
        
        assert result.status == NotificationStatus.SENT
        assert result.message_id is not None
        assert result.message_id.startswith('sim_voice_')
        assert result.cost == 0.15
        assert result.metadata['provider'] == 'simulated'
        assert result.metadata['type'] == 'voice'
    
    @pytest.mark.asyncio
    async def test_send_whatsapp_success(self, adapter):
        """Test successful WhatsApp message"""
        result = await adapter.send_whatsapp('+919876543210', 'Test message')
        
        assert result.status == NotificationStatus.SENT
        assert result.message_id is not None
        assert result.message_id.startswith('sim_whatsapp_')
        assert result.cost == 0.02
        assert result.metadata['provider'] == 'simulated'
        assert result.metadata['type'] == 'whatsapp'
    
    @pytest.mark.asyncio
    async def test_send_sms_failure(self, failing_adapter):
        """Test SMS sending failure"""
        result = await failing_adapter.send_sms('+919876543210', 'Test message')
        
        assert result.status == NotificationStatus.FAILED
        assert result.error_message == 'Simulated network error'
        assert result.metadata['provider'] == 'simulated'
    
    @pytest.mark.asyncio
    async def test_get_delivery_status_success(self, adapter):
        """Test delivery status check success"""
        status = await adapter.get_delivery_status('test_message_id')
        assert status in [NotificationStatus.DELIVERED, NotificationStatus.FAILED]
    
    @pytest.mark.asyncio
    async def test_simulate_delay(self):
        """Test that delay simulation works"""
        config = {'simulate_delay': True, 'failure_rate': 0.0}
        adapter = SimulatedAdapter(config)
        
        start_time = datetime.now()
        await adapter.send_sms('+919876543210', 'Test message')
        end_time = datetime.now()
        
        # Should take at least 0.5 seconds due to simulated delay
        duration = (end_time - start_time).total_seconds()
        assert duration >= 0.4  # Allow some tolerance

class TestTwilioAdapter:
    """Test Twilio notification adapter"""
    
    @pytest.fixture
    def adapter(self):
        """Create Twilio adapter for testing"""
        config = {
            'account_sid': 'test_sid',
            'auth_token': 'test_token',
            'from_number': '+1234567890'
        }
        return TwilioAdapter(config)
    
    @pytest.mark.asyncio
    async def test_send_sms_success(self, adapter):
        """Test successful SMS sending via Twilio"""
        mock_response = {
            'sid': 'SM123456789',
            'status': 'queued',
            'price': '0.0075'
        }
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.return_value.__aenter__.return_value.status = 201
            mock_post.return_value.__aenter__.return_value.json = AsyncMock(return_value=mock_response)
            
            result = await adapter.send_sms('+919876543210', 'Test message')
            
            assert result.status == NotificationStatus.SENT
            assert result.message_id == 'SM123456789'
            assert result.cost == 0.0075
            assert result.metadata['provider'] == 'twilio'
    
    @pytest.mark.asyncio
    async def test_send_sms_failure(self, adapter):
        """Test SMS sending failure via Twilio"""
        mock_response = {
            'message': 'Invalid phone number',
            'code': 21211
        }
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.return_value.__aenter__.return_value.status = 400
            mock_post.return_value.__aenter__.return_value.json = AsyncMock(return_value=mock_response)
            
            result = await adapter.send_sms('+919876543210', 'Test message')
            
            assert result.status == NotificationStatus.FAILED
            assert result.error_message == 'Invalid phone number'
            assert result.metadata['provider'] == 'twilio'
    
    @pytest.mark.asyncio
    async def test_send_voice_success(self, adapter):
        """Test successful voice call via Twilio"""
        mock_response = {
            'sid': 'CA123456789',
            'status': 'queued'
        }
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.return_value.__aenter__.return_value.status = 201
            mock_post.return_value.__aenter__.return_value.json = AsyncMock(return_value=mock_response)
            
            result = await adapter.send_voice('+919876543210', 'Test message')
            
            assert result.status == NotificationStatus.SENT
            assert result.message_id == 'CA123456789'
            assert result.metadata['provider'] == 'twilio'
    
    @pytest.mark.asyncio
    async def test_send_whatsapp_success(self, adapter):
        """Test successful WhatsApp message via Twilio"""
        mock_response = {
            'sid': 'SM123456789',
            'status': 'queued'
        }
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.return_value.__aenter__.return_value.status = 201
            mock_post.return_value.__aenter__.return_value.json = AsyncMock(return_value=mock_response)
            
            result = await adapter.send_whatsapp('+919876543210', 'Test message')
            
            assert result.status == NotificationStatus.SENT
            assert result.message_id == 'SM123456789'
            assert result.metadata['provider'] == 'twilio'
    
    @pytest.mark.asyncio
    async def test_get_delivery_status_delivered(self, adapter):
        """Test delivery status check - delivered"""
        mock_response = {
            'sid': 'SM123456789',
            'status': 'delivered'
        }
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.return_value.__aenter__.return_value.status = 200
            mock_get.return_value.__aenter__.return_value.json = AsyncMock(return_value=mock_response)
            
            status = await adapter.get_delivery_status('SM123456789')
            assert status == NotificationStatus.DELIVERED
    
    @pytest.mark.asyncio
    async def test_get_delivery_status_failed(self, adapter):
        """Test delivery status check - failed"""
        mock_response = {
            'sid': 'SM123456789',
            'status': 'failed'
        }
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.return_value.__aenter__.return_value.status = 200
            mock_get.return_value.__aenter__.return_value.json = AsyncMock(return_value=mock_response)
            
            status = await adapter.get_delivery_status('SM123456789')
            assert status == NotificationStatus.FAILED
    
    def test_format_phone_with_plus(self, adapter):
        """Test phone number formatting with plus"""
        formatted = adapter._format_phone('+919876543210')
        assert formatted == '+919876543210'
    
    def test_format_phone_with_91(self, adapter):
        """Test phone number formatting with 91"""
        formatted = adapter._format_phone('919876543210')
        assert formatted == '+919876543210'
    
    def test_format_phone_with_zero(self, adapter):
        """Test phone number formatting with leading zero"""
        formatted = adapter._format_phone('09876543210')
        assert formatted == '+919876543210'
    
    def test_format_phone_plain(self, adapter):
        """Test phone number formatting plain number"""
        formatted = adapter._format_phone('9876543210')
        assert formatted == '+919876543210'

class TestExotelAdapter:
    """Test Exotel notification adapter"""
    
    @pytest.fixture
    def adapter(self):
        """Create Exotel adapter for testing"""
        config = {
            'api_key': 'test_key',
            'api_token': 'test_token',
            'account_sid': 'test_sid',
            'from_number': '1234567890'
        }
        return ExotelAdapter(config)
    
    @pytest.mark.asyncio
    async def test_send_sms_success(self, adapter):
        """Test successful SMS sending via Exotel"""
        mock_response = {
            'SMSMessage': {
                'Sid': 'SM123456789',
                'Status': 'queued'
            }
        }
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.return_value.__aenter__.return_value.status = 200
            mock_post.return_value.__aenter__.return_value.json = AsyncMock(return_value=mock_response)
            
            result = await adapter.send_sms('+919876543210', 'Test message')
            
            assert result.status == NotificationStatus.SENT
            assert result.message_id == 'SM123456789'
            assert result.metadata['provider'] == 'exotel'
    
    @pytest.mark.asyncio
    async def test_send_voice_success(self, adapter):
        """Test successful voice call via Exotel"""
        mock_response = {
            'Call': {
                'Sid': 'CA123456789',
                'Status': 'queued'
            }
        }
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.return_value.__aenter__.return_value.status = 200
            mock_post.return_value.__aenter__.return_value.json = AsyncMock(return_value=mock_response)
            
            result = await adapter.send_voice('+919876543210', 'Test message')
            
            assert result.status == NotificationStatus.SENT
            assert result.message_id == 'CA123456789'
            assert result.metadata['provider'] == 'exotel'
    
    @pytest.mark.asyncio
    async def test_send_whatsapp_not_supported(self, adapter):
        """Test that WhatsApp is not supported by Exotel"""
        result = await adapter.send_whatsapp('+919876543210', 'Test message')
        
        assert result.status == NotificationStatus.FAILED
        assert result.error_message == 'WhatsApp not supported by Exotel adapter'
        assert result.metadata['provider'] == 'exotel'
    
    @pytest.mark.asyncio
    async def test_get_delivery_status_sent(self, adapter):
        """Test delivery status check - sent"""
        mock_response = {
            'SMSMessage': {
                'Sid': 'SM123456789',
                'Status': 'sent'
            }
        }
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.return_value.__aenter__.return_value.status = 200
            mock_get.return_value.__aenter__.return_value.json = AsyncMock(return_value=mock_response)
            
            status = await adapter.get_delivery_status('SM123456789')
            assert status == NotificationStatus.DELIVERED