"""
Notification adapters for different SMS/Voice/WhatsApp gateways
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import logging
import asyncio
import aiohttp
from datetime import datetime

logger = logging.getLogger(__name__)

class NotificationStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    DELIVERED = "delivered"

@dataclass
class NotificationResult:
    """Result of a notification attempt"""
    status: NotificationStatus
    message_id: Optional[str] = None
    error_message: Optional[str] = None
    cost: Optional[float] = None
    delivery_time: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None

class NotificationAdapter(ABC):
    """Base class for notification adapters"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.name = self.__class__.__name__
    
    @abstractmethod
    async def send_sms(self, phone: str, message: str, **kwargs) -> NotificationResult:
        """Send SMS notification"""
        pass
    
    @abstractmethod
    async def send_voice(self, phone: str, message: str, **kwargs) -> NotificationResult:
        """Send voice call notification"""
        pass
    
    @abstractmethod
    async def send_whatsapp(self, phone: str, message: str, **kwargs) -> NotificationResult:
        """Send WhatsApp notification"""
        pass
    
    @abstractmethod
    async def get_delivery_status(self, message_id: str) -> NotificationStatus:
        """Get delivery status of a message"""
        pass
    
    def _format_phone(self, phone: str) -> str:
        """Format phone number to international format"""
        if phone.startswith('+'):
            return phone
        if phone.startswith('91'):
            return f'+{phone}'
        if phone.startswith('0'):
            return f'+91{phone[1:]}'
        return f'+91{phone}'

class TwilioAdapter(NotificationAdapter):
    """Twilio SMS/Voice adapter"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.account_sid = config.get('account_sid')
        self.auth_token = config.get('auth_token')
        self.from_number = config.get('from_number', '+1234567890')
        self.base_url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}"
    
    async def send_sms(self, phone: str, message: str, **kwargs) -> NotificationResult:
        """Send SMS via Twilio"""
        try:
            formatted_phone = self._format_phone(phone)
            
            async with aiohttp.ClientSession() as session:
                auth = aiohttp.BasicAuth(self.account_sid, self.auth_token)
                data = {
                    'From': self.from_number,
                    'To': formatted_phone,
                    'Body': message
                }
                
                async with session.post(
                    f"{self.base_url}/Messages.json",
                    auth=auth,
                    data=data
                ) as response:
                    result = await response.json()
                    
                    if response.status == 201:
                        return NotificationResult(
                            status=NotificationStatus.SENT,
                            message_id=result.get('sid'),
                            cost=float(result.get('price', 0)) if result.get('price') else None,
                            metadata={'provider': 'twilio', 'response': result}
                        )
                    else:
                        return NotificationResult(
                            status=NotificationStatus.FAILED,
                            error_message=result.get('message', 'Unknown error'),
                            metadata={'provider': 'twilio', 'response': result}
                        )
        
        except Exception as e:
            logger.error(f"Twilio SMS error: {str(e)}")
            return NotificationResult(
                status=NotificationStatus.FAILED,
                error_message=str(e),
                metadata={'provider': 'twilio'}
            )
    
    async def send_voice(self, phone: str, message: str, **kwargs) -> NotificationResult:
        """Send voice call via Twilio"""
        try:
            formatted_phone = self._format_phone(phone)
            
            # Create TwiML for voice message
            twiml_url = kwargs.get('twiml_url') or self._create_twiml_url(message)
            
            async with aiohttp.ClientSession() as session:
                auth = aiohttp.BasicAuth(self.account_sid, self.auth_token)
                data = {
                    'From': self.from_number,
                    'To': formatted_phone,
                    'Url': twiml_url
                }
                
                async with session.post(
                    f"{self.base_url}/Calls.json",
                    auth=auth,
                    data=data
                ) as response:
                    result = await response.json()
                    
                    if response.status == 201:
                        return NotificationResult(
                            status=NotificationStatus.SENT,
                            message_id=result.get('sid'),
                            metadata={'provider': 'twilio', 'response': result}
                        )
                    else:
                        return NotificationResult(
                            status=NotificationStatus.FAILED,
                            error_message=result.get('message', 'Unknown error'),
                            metadata={'provider': 'twilio', 'response': result}
                        )
        
        except Exception as e:
            logger.error(f"Twilio Voice error: {str(e)}")
            return NotificationResult(
                status=NotificationStatus.FAILED,
                error_message=str(e),
                metadata={'provider': 'twilio'}
            )
    
    async def send_whatsapp(self, phone: str, message: str, **kwargs) -> NotificationResult:
        """Send WhatsApp message via Twilio"""
        try:
            formatted_phone = self._format_phone(phone)
            
            async with aiohttp.ClientSession() as session:
                auth = aiohttp.BasicAuth(self.account_sid, self.auth_token)
                data = {
                    'From': f'whatsapp:{self.from_number}',
                    'To': f'whatsapp:{formatted_phone}',
                    'Body': message
                }
                
                async with session.post(
                    f"{self.base_url}/Messages.json",
                    auth=auth,
                    data=data
                ) as response:
                    result = await response.json()
                    
                    if response.status == 201:
                        return NotificationResult(
                            status=NotificationStatus.SENT,
                            message_id=result.get('sid'),
                            metadata={'provider': 'twilio', 'response': result}
                        )
                    else:
                        return NotificationResult(
                            status=NotificationStatus.FAILED,
                            error_message=result.get('message', 'Unknown error'),
                            metadata={'provider': 'twilio', 'response': result}
                        )
        
        except Exception as e:
            logger.error(f"Twilio WhatsApp error: {str(e)}")
            return NotificationResult(
                status=NotificationStatus.FAILED,
                error_message=str(e),
                metadata={'provider': 'twilio'}
            )
    
    async def get_delivery_status(self, message_id: str) -> NotificationStatus:
        """Get delivery status from Twilio"""
        try:
            async with aiohttp.ClientSession() as session:
                auth = aiohttp.BasicAuth(self.account_sid, self.auth_token)
                
                async with session.get(
                    f"{self.base_url}/Messages/{message_id}.json",
                    auth=auth
                ) as response:
                    result = await response.json()
                    
                    if response.status == 200:
                        status = result.get('status', '').lower()
                        if status in ['delivered']:
                            return NotificationStatus.DELIVERED
                        elif status in ['sent', 'queued']:
                            return NotificationStatus.SENT
                        elif status in ['failed', 'undelivered']:
                            return NotificationStatus.FAILED
                        else:
                            return NotificationStatus.PENDING
                    else:
                        return NotificationStatus.FAILED
        
        except Exception as e:
            logger.error(f"Twilio status check error: {str(e)}")
            return NotificationStatus.FAILED
    
    def _create_twiml_url(self, message: str) -> str:
        """Create TwiML URL for voice message (simplified)"""
        # In production, this would be a proper TwiML endpoint
        return f"http://twimlets.com/message?Message={message}"

class ExotelAdapter(NotificationAdapter):
    """Exotel SMS/Voice adapter"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get('api_key')
        self.api_token = config.get('api_token')
        self.account_sid = config.get('account_sid')
        self.from_number = config.get('from_number')
        self.base_url = f"https://api.exotel.com/v1/Accounts/{self.account_sid}"
    
    async def send_sms(self, phone: str, message: str, **kwargs) -> NotificationResult:
        """Send SMS via Exotel"""
        try:
            formatted_phone = self._format_phone(phone)
            
            async with aiohttp.ClientSession() as session:
                auth = aiohttp.BasicAuth(self.api_key, self.api_token)
                data = {
                    'From': self.from_number,
                    'To': formatted_phone,
                    'Body': message
                }
                
                async with session.post(
                    f"{self.base_url}/Sms/send.json",
                    auth=auth,
                    data=data
                ) as response:
                    result = await response.json()
                    
                    if response.status == 200:
                        sms_data = result.get('SMSMessage', {})
                        return NotificationResult(
                            status=NotificationStatus.SENT,
                            message_id=sms_data.get('Sid'),
                            metadata={'provider': 'exotel', 'response': result}
                        )
                    else:
                        return NotificationResult(
                            status=NotificationStatus.FAILED,
                            error_message=result.get('message', 'Unknown error'),
                            metadata={'provider': 'exotel', 'response': result}
                        )
        
        except Exception as e:
            logger.error(f"Exotel SMS error: {str(e)}")
            return NotificationResult(
                status=NotificationStatus.FAILED,
                error_message=str(e),
                metadata={'provider': 'exotel'}
            )
    
    async def send_voice(self, phone: str, message: str, **kwargs) -> NotificationResult:
        """Send voice call via Exotel"""
        try:
            formatted_phone = self._format_phone(phone)
            
            async with aiohttp.ClientSession() as session:
                auth = aiohttp.BasicAuth(self.api_key, self.api_token)
                data = {
                    'From': self.from_number,
                    'To': formatted_phone,
                    'Url': kwargs.get('callback_url', ''),
                    'Method': 'GET'
                }
                
                async with session.post(
                    f"{self.base_url}/Calls/connect.json",
                    auth=auth,
                    data=data
                ) as response:
                    result = await response.json()
                    
                    if response.status == 200:
                        call_data = result.get('Call', {})
                        return NotificationResult(
                            status=NotificationStatus.SENT,
                            message_id=call_data.get('Sid'),
                            metadata={'provider': 'exotel', 'response': result}
                        )
                    else:
                        return NotificationResult(
                            status=NotificationStatus.FAILED,
                            error_message=result.get('message', 'Unknown error'),
                            metadata={'provider': 'exotel', 'response': result}
                        )
        
        except Exception as e:
            logger.error(f"Exotel Voice error: {str(e)}")
            return NotificationResult(
                status=NotificationStatus.FAILED,
                error_message=str(e),
                metadata={'provider': 'exotel'}
            )
    
    async def send_whatsapp(self, phone: str, message: str, **kwargs) -> NotificationResult:
        """Exotel doesn't support WhatsApp directly"""
        return NotificationResult(
            status=NotificationStatus.FAILED,
            error_message="WhatsApp not supported by Exotel adapter",
            metadata={'provider': 'exotel'}
        )
    
    async def get_delivery_status(self, message_id: str) -> NotificationStatus:
        """Get delivery status from Exotel"""
        try:
            async with aiohttp.ClientSession() as session:
                auth = aiohttp.BasicAuth(self.api_key, self.api_token)
                
                async with session.get(
                    f"{self.base_url}/Sms/Messages/{message_id}.json",
                    auth=auth
                ) as response:
                    result = await response.json()
                    
                    if response.status == 200:
                        sms_data = result.get('SMSMessage', {})
                        status = sms_data.get('Status', '').lower()
                        if status in ['sent']:
                            return NotificationStatus.DELIVERED
                        elif status in ['queued']:
                            return NotificationStatus.SENT
                        elif status in ['failed']:
                            return NotificationStatus.FAILED
                        else:
                            return NotificationStatus.PENDING
                    else:
                        return NotificationStatus.FAILED
        
        except Exception as e:
            logger.error(f"Exotel status check error: {str(e)}")
            return NotificationStatus.FAILED

class SimulatedAdapter(NotificationAdapter):
    """Simulated adapter for demo mode"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.simulate_delay = config.get('simulate_delay', True)
        self.failure_rate = config.get('failure_rate', 0.1)  # 10% failure rate
    
    async def send_sms(self, phone: str, message: str, **kwargs) -> NotificationResult:
        """Simulate SMS sending"""
        if self.simulate_delay:
            await asyncio.sleep(0.5)  # Simulate network delay
        
        # Simulate occasional failures
        import random
        if random.random() < self.failure_rate:
            return NotificationResult(
                status=NotificationStatus.FAILED,
                error_message="Simulated network error",
                metadata={'provider': 'simulated', 'type': 'sms'}
            )
        
        message_id = f"sim_sms_{datetime.now().timestamp()}"
        logger.info(f"[SIMULATED SMS] To: {phone}, Message: {message}")
        
        return NotificationResult(
            status=NotificationStatus.SENT,
            message_id=message_id,
            cost=0.05,  # Simulated cost
            metadata={'provider': 'simulated', 'type': 'sms', 'phone': phone, 'message': message}
        )
    
    async def send_voice(self, phone: str, message: str, **kwargs) -> NotificationResult:
        """Simulate voice call"""
        if self.simulate_delay:
            await asyncio.sleep(1.0)  # Simulate call setup delay
        
        import random
        if random.random() < self.failure_rate:
            return NotificationResult(
                status=NotificationStatus.FAILED,
                error_message="Simulated call failed",
                metadata={'provider': 'simulated', 'type': 'voice'}
            )
        
        message_id = f"sim_voice_{datetime.now().timestamp()}"
        logger.info(f"[SIMULATED VOICE] To: {phone}, Message: {message}")
        
        return NotificationResult(
            status=NotificationStatus.SENT,
            message_id=message_id,
            cost=0.15,  # Simulated cost
            metadata={'provider': 'simulated', 'type': 'voice', 'phone': phone, 'message': message}
        )
    
    async def send_whatsapp(self, phone: str, message: str, **kwargs) -> NotificationResult:
        """Simulate WhatsApp message"""
        if self.simulate_delay:
            await asyncio.sleep(0.3)
        
        import random
        if random.random() < self.failure_rate:
            return NotificationResult(
                status=NotificationStatus.FAILED,
                error_message="Simulated WhatsApp error",
                metadata={'provider': 'simulated', 'type': 'whatsapp'}
            )
        
        message_id = f"sim_whatsapp_{datetime.now().timestamp()}"
        logger.info(f"[SIMULATED WHATSAPP] To: {phone}, Message: {message}")
        
        return NotificationResult(
            status=NotificationStatus.SENT,
            message_id=message_id,
            cost=0.02,  # Simulated cost
            metadata={'provider': 'simulated', 'type': 'whatsapp', 'phone': phone, 'message': message}
        )
    
    async def get_delivery_status(self, message_id: str) -> NotificationStatus:
        """Simulate delivery status check"""
        await asyncio.sleep(0.1)
        
        # Simulate delivery after some time
        import random
        if random.random() < 0.9:  # 90% delivery success
            return NotificationStatus.DELIVERED
        else:
            return NotificationStatus.FAILED

class NotificationAdapterFactory:
    """Factory for creating notification adapters"""
    
    _adapters = {
        'twilio': TwilioAdapter,
        'exotel': ExotelAdapter,
        'simulated': SimulatedAdapter
    }
    
    @classmethod
    def create_adapter(cls, adapter_type: str, config: Dict[str, Any]) -> NotificationAdapter:
        """Create notification adapter instance"""
        if adapter_type not in cls._adapters:
            raise ValueError(f"Unknown adapter type: {adapter_type}")
        
        adapter_class = cls._adapters[adapter_type]
        return adapter_class(config)
    
    @classmethod
    def get_available_adapters(cls) -> list:
        """Get list of available adapter types"""
        return list(cls._adapters.keys())