"""
Notification Engine with Redis queue and background processing
"""
import json
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import asdict
import redis.asyncio as redis
from sqlalchemy.orm import Session

from .notification_adapters import (
    NotificationAdapter, 
    NotificationAdapterFactory, 
    NotificationResult, 
    NotificationStatus
)
from ..core.config import settings
from ..core.database import get_db
from ..models.notification import Notification
from ..models.subscription import Subscription, NotificationChannel
from ..repositories.subscription import SubscriptionRepository

logger = logging.getLogger(__name__)

class NotificationQueue:
    """Redis-based notification queue"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.queue_key = "notification_queue"
        self.processing_key = "notification_processing"
        self.retry_key = "notification_retry"
        self.dlq_key = "notification_dlq"  # Dead letter queue
    
    async def enqueue(self, notification_data: Dict[str, Any], priority: int = 0) -> bool:
        """Add notification to queue with priority"""
        try:
            # Add timestamp and priority
            notification_data['queued_at'] = datetime.now().isoformat()
            notification_data['priority'] = priority
            notification_data['retry_count'] = 0
            
            # Use priority queue (lower score = higher priority)
            score = priority * 1000 + datetime.now().timestamp()
            
            await self.redis.zadd(
                self.queue_key, 
                {json.dumps(notification_data): score}
            )
            
            logger.info(f"Notification queued: {notification_data.get('id', 'unknown')}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to enqueue notification: {str(e)}")
            return False
    
    async def dequeue(self, timeout: int = 10) -> Optional[Dict[str, Any]]:
        """Get next notification from queue (blocking)"""
        try:
            # Get highest priority item (lowest score)
            result = await self.redis.bzpopmin(self.queue_key, timeout=timeout)
            
            if result:
                _, notification_json, _ = result
                notification_data = json.loads(notification_json)
                
                # Move to processing queue
                await self.redis.hset(
                    self.processing_key,
                    notification_data['id'],
                    notification_json
                )
                
                return notification_data
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to dequeue notification: {str(e)}")
            return None
    
    async def mark_completed(self, notification_id: str) -> bool:
        """Mark notification as completed"""
        try:
            await self.redis.hdel(self.processing_key, notification_id)
            return True
        except Exception as e:
            logger.error(f"Failed to mark notification completed: {str(e)}")
            return False
    
    async def mark_failed(self, notification_data: Dict[str, Any], error: str) -> bool:
        """Mark notification as failed and handle retry logic"""
        try:
            notification_id = notification_data['id']
            retry_count = notification_data.get('retry_count', 0)
            max_retries = notification_data.get('max_retries', 3)
            
            # Remove from processing queue
            await self.redis.hdel(self.processing_key, notification_id)
            
            if retry_count < max_retries:
                # Schedule retry with exponential backoff
                retry_delay = min(300, 30 * (2 ** retry_count))  # Max 5 minutes
                retry_time = datetime.now() + timedelta(seconds=retry_delay)
                
                notification_data['retry_count'] = retry_count + 1
                notification_data['last_error'] = error
                notification_data['retry_at'] = retry_time.isoformat()
                
                await self.redis.zadd(
                    self.retry_key,
                    {json.dumps(notification_data): retry_time.timestamp()}
                )
                
                logger.info(f"Notification scheduled for retry: {notification_id} (attempt {retry_count + 1})")
            else:
                # Move to dead letter queue
                notification_data['failed_at'] = datetime.now().isoformat()
                notification_data['final_error'] = error
                
                await self.redis.lpush(
                    self.dlq_key,
                    json.dumps(notification_data)
                )
                
                logger.error(f"Notification moved to DLQ: {notification_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to mark notification failed: {str(e)}")
            return False
    
    async def process_retries(self) -> int:
        """Process notifications ready for retry"""
        try:
            current_time = datetime.now().timestamp()
            
            # Get notifications ready for retry
            retry_items = await self.redis.zrangebyscore(
                self.retry_key, 
                0, 
                current_time, 
                withscores=True
            )
            
            count = 0
            for notification_json, _ in retry_items:
                notification_data = json.loads(notification_json)
                
                # Move back to main queue
                await self.enqueue(notification_data, priority=1)  # Higher priority for retries
                
                # Remove from retry queue
                await self.redis.zrem(self.retry_key, notification_json)
                count += 1
            
            if count > 0:
                logger.info(f"Processed {count} retry notifications")
            
            return count
            
        except Exception as e:
            logger.error(f"Failed to process retries: {str(e)}")
            return 0
    
    async def get_queue_stats(self) -> Dict[str, int]:
        """Get queue statistics"""
        try:
            stats = {
                'queued': await self.redis.zcard(self.queue_key),
                'processing': await self.redis.hlen(self.processing_key),
                'retry': await self.redis.zcard(self.retry_key),
                'dlq': await self.redis.llen(self.dlq_key)
            }
            return stats
        except Exception as e:
            logger.error(f"Failed to get queue stats: {str(e)}")
            return {}

class NotificationEngine:
    """Main notification engine"""
    
    def __init__(self):
        self.redis_client = None
        self.queue = None
        self.adapters: Dict[str, NotificationAdapter] = {}
        self.running = False
        self.worker_tasks = []
        
    async def initialize(self):
        """Initialize the notification engine"""
        try:
            # Initialize Redis connection
            self.redis_client = redis.from_url(settings.REDIS_URL)
            self.queue = NotificationQueue(self.redis_client)
            
            # Initialize adapters based on configuration
            await self._initialize_adapters()
            
            logger.info("Notification engine initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize notification engine: {str(e)}")
            raise
    
    async def _initialize_adapters(self):
        """Initialize notification adapters"""
        try:
            if settings.DEMO_MODE:
                # Use simulated adapter in demo mode
                self.adapters['simulated'] = NotificationAdapterFactory.create_adapter(
                    'simulated', 
                    {'simulate_delay': True, 'failure_rate': 0.05}
                )
                logger.info("Initialized simulated adapter for demo mode")
            else:
                # Initialize real adapters
                if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN:
                    self.adapters['twilio'] = NotificationAdapterFactory.create_adapter(
                        'twilio',
                        {
                            'account_sid': settings.TWILIO_ACCOUNT_SID,
                            'auth_token': settings.TWILIO_AUTH_TOKEN,
                            'from_number': getattr(settings, 'TWILIO_FROM_NUMBER', '+1234567890')
                        }
                    )
                    logger.info("Initialized Twilio adapter")
                
                if settings.EXOTEL_API_KEY and settings.EXOTEL_API_TOKEN:
                    self.adapters['exotel'] = NotificationAdapterFactory.create_adapter(
                        'exotel',
                        {
                            'api_key': settings.EXOTEL_API_KEY,
                            'api_token': settings.EXOTEL_API_TOKEN,
                            'account_sid': getattr(settings, 'EXOTEL_ACCOUNT_SID', ''),
                            'from_number': getattr(settings, 'EXOTEL_FROM_NUMBER', '')
                        }
                    )
                    logger.info("Initialized Exotel adapter")
                
                # Fallback to simulated if no real adapters configured
                if not self.adapters:
                    self.adapters['simulated'] = NotificationAdapterFactory.create_adapter(
                        'simulated', 
                        {'simulate_delay': False, 'failure_rate': 0.0}
                    )
                    logger.warning("No real adapters configured, using simulated adapter")
                    
        except Exception as e:
            logger.error(f"Failed to initialize adapters: {str(e)}")
            raise
    
    async def send_notification(self, 
                              phone: str, 
                              message: str, 
                              channel: NotificationChannel,
                              subscription_id: Optional[int] = None,
                              priority: int = 0,
                              **kwargs) -> str:
        """Queue a notification for sending"""
        try:
            notification_id = f"notif_{datetime.now().timestamp()}_{hash(phone)}"
            
            notification_data = {
                'id': notification_id,
                'phone': phone,
                'message': message,
                'channel': channel.value,
                'subscription_id': subscription_id,
                'priority': priority,
                'max_retries': kwargs.get('max_retries', 3),
                'metadata': kwargs.get('metadata', {})
            }
            
            success = await self.queue.enqueue(notification_data, priority)
            
            if success:
                # Create notification record in database
                await self._create_notification_record(notification_data)
                return notification_id
            else:
                raise Exception("Failed to queue notification")
                
        except Exception as e:
            logger.error(f"Failed to send notification: {str(e)}")
            raise
    
    async def _create_notification_record(self, notification_data: Dict[str, Any]):
        """Create notification record in database"""
        try:
            db = next(get_db())
            
            notification = Notification(
                subscription_id=notification_data.get('subscription_id'),
                message=notification_data['message'],
                channel=notification_data['channel'],
                status=NotificationStatus.PENDING
            )
            
            db.add(notification)
            db.commit()
            
            # Update notification data with database ID
            notification_data['db_id'] = notification.id
            
        except Exception as e:
            logger.error(f"Failed to create notification record: {str(e)}")
    
    async def start_workers(self, num_workers: int = 3):
        """Start background worker tasks"""
        if self.running:
            return
        
        self.running = True
        
        # Start notification processing workers
        for i in range(num_workers):
            task = asyncio.create_task(self._notification_worker(f"worker-{i}"))
            self.worker_tasks.append(task)
        
        # Start retry processor
        retry_task = asyncio.create_task(self._retry_processor())
        self.worker_tasks.append(retry_task)
        
        logger.info(f"Started {num_workers} notification workers and retry processor")
    
    async def stop_workers(self):
        """Stop background worker tasks"""
        self.running = False
        
        # Cancel all worker tasks
        for task in self.worker_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        if self.worker_tasks:
            await asyncio.gather(*self.worker_tasks, return_exceptions=True)
        
        self.worker_tasks.clear()
        logger.info("Stopped notification workers")
    
    async def _notification_worker(self, worker_name: str):
        """Background worker for processing notifications"""
        logger.info(f"Notification worker {worker_name} started")
        
        while self.running:
            try:
                # Get next notification from queue
                notification_data = await self.queue.dequeue(timeout=5)
                
                if not notification_data:
                    continue
                
                notification_id = notification_data['id']
                logger.info(f"Worker {worker_name} processing notification {notification_id}")
                
                # Process the notification
                success = await self._process_notification(notification_data)
                
                if success:
                    await self.queue.mark_completed(notification_id)
                    await self._update_notification_status(
                        notification_data, 
                        NotificationStatus.SENT
                    )
                else:
                    await self.queue.mark_failed(
                        notification_data, 
                        "Processing failed"
                    )
                    await self._update_notification_status(
                        notification_data, 
                        NotificationStatus.FAILED
                    )
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker {worker_name} error: {str(e)}")
                await asyncio.sleep(1)
        
        logger.info(f"Notification worker {worker_name} stopped")
    
    async def _process_notification(self, notification_data: Dict[str, Any]) -> bool:
        """Process a single notification"""
        try:
            phone = notification_data['phone']
            message = notification_data['message']
            channel = notification_data['channel']
            
            # Select appropriate adapter
            adapter = self._select_adapter(channel)
            if not adapter:
                logger.error(f"No adapter available for channel: {channel}")
                return False
            
            # Send notification based on channel
            result = None
            if channel == NotificationChannel.SMS.value:
                result = await adapter.send_sms(phone, message)
            elif channel == NotificationChannel.VOICE.value:
                result = await adapter.send_voice(phone, message)
            elif channel == NotificationChannel.WHATSAPP.value:
                result = await adapter.send_whatsapp(phone, message)
            else:
                logger.error(f"Unsupported channel: {channel}")
                return False
            
            # Log result
            if result.status == NotificationStatus.SENT:
                logger.info(f"Notification sent successfully: {notification_data['id']}")
                
                # Store message ID for status tracking
                if result.message_id:
                    notification_data['message_id'] = result.message_id
                
                return True
            else:
                logger.error(f"Notification failed: {result.error_message}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to process notification: {str(e)}")
            return False
    
    def _select_adapter(self, channel: str) -> Optional[NotificationAdapter]:
        """Select appropriate adapter for channel"""
        # In demo mode, always use simulated adapter
        if settings.DEMO_MODE:
            return self.adapters.get('simulated')
        
        # Select based on availability and channel
        if channel in [NotificationChannel.SMS.value, NotificationChannel.VOICE.value]:
            # Prefer Twilio, fallback to Exotel, then simulated
            for adapter_name in ['twilio', 'exotel', 'simulated']:
                if adapter_name in self.adapters:
                    return self.adapters[adapter_name]
        elif channel == NotificationChannel.WHATSAPP.value:
            # Only Twilio supports WhatsApp in our setup
            return self.adapters.get('twilio') or self.adapters.get('simulated')
        
        return None
    
    async def _retry_processor(self):
        """Background task for processing retries"""
        logger.info("Retry processor started")
        
        while self.running:
            try:
                await self.queue.process_retries()
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Retry processor error: {str(e)}")
                await asyncio.sleep(60)
        
        logger.info("Retry processor stopped")
    
    async def _update_notification_status(self, 
                                        notification_data: Dict[str, Any], 
                                        status: NotificationStatus):
        """Update notification status in database"""
        try:
            db_id = notification_data.get('db_id')
            if not db_id:
                return
            
            db = next(get_db())
            notification = db.query(Notification).filter(Notification.id == db_id).first()
            
            if notification:
                notification.status = status
                if status == NotificationStatus.SENT:
                    notification.sent_at = datetime.now()
                elif status == NotificationStatus.DELIVERED:
                    notification.delivered_at = datetime.now()
                
                db.commit()
                
        except Exception as e:
            logger.error(f"Failed to update notification status: {str(e)}")
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get notification engine statistics"""
        try:
            queue_stats = await self.queue.get_queue_stats()
            
            return {
                'queue_stats': queue_stats,
                'adapters': list(self.adapters.keys()),
                'workers_running': len(self.worker_tasks),
                'demo_mode': settings.DEMO_MODE
            }
            
        except Exception as e:
            logger.error(f"Failed to get stats: {str(e)}")
            return {}
    
    async def cleanup(self):
        """Cleanup resources"""
        await self.stop_workers()
        
        if self.redis_client:
            await self.redis_client.close()

# Global notification engine instance
notification_engine = NotificationEngine()