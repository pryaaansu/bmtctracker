"""
Notification scheduler with rate limiting and scheduling functionality
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import redis.asyncio as redis
import json

from ..core.config import settings
from .notification_engine import notification_engine
from .notification_templates import template_manager, TemplateType, Language
from ..models.subscription import NotificationChannel

logger = logging.getLogger(__name__)

class ScheduleType(str, Enum):
    """Types of notification schedules"""
    IMMEDIATE = "immediate"
    DELAYED = "delayed"
    RECURRING = "recurring"
    CONDITIONAL = "conditional"

@dataclass
class NotificationSchedule:
    """Represents a scheduled notification"""
    id: str
    phone: str
    message: str
    channel: NotificationChannel
    schedule_type: ScheduleType
    scheduled_time: datetime
    subscription_id: Optional[int] = None
    priority: int = 0
    max_retries: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)
    conditions: Dict[str, Any] = field(default_factory=dict)  # For conditional notifications
    recurring_pattern: Optional[str] = None  # Cron-like pattern for recurring
    created_at: datetime = field(default_factory=datetime.now)
    attempts: int = 0
    last_attempt: Optional[datetime] = None
    status: str = "pending"  # pending, sent, failed, cancelled

@dataclass
class RateLimitRule:
    """Rate limiting rule"""
    key: str  # e.g., "phone:+919876543210", "subscription:123", "global"
    max_notifications: int
    time_window_minutes: int
    current_count: int = 0
    window_start: datetime = field(default_factory=datetime.now)

class NotificationRateLimiter:
    """Handles rate limiting for notifications"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.rate_limit_key_prefix = "rate_limit"
        
        # Default rate limits
        self.default_limits = {
            "phone": {"max_notifications": 20, "time_window_minutes": 60},  # 20 per hour per phone
            "subscription": {"max_notifications": 10, "time_window_minutes": 60},  # 10 per hour per subscription
            "global": {"max_notifications": 1000, "time_window_minutes": 60},  # 1000 per hour globally
            "emergency": {"max_notifications": 100, "time_window_minutes": 60}  # Higher limit for emergencies
        }
    
    async def check_rate_limit(self, phone: str, subscription_id: Optional[int] = None,
                             is_emergency: bool = False) -> bool:
        """
        Check if notification is within rate limits
        Returns True if allowed, False if rate limited
        """
        try:
            current_time = datetime.now()
            
            # Check phone-level rate limit
            phone_key = f"phone:{phone}"
            if not await self._check_individual_limit(phone_key, "phone", current_time, is_emergency):
                logger.warning(f"Rate limit exceeded for phone: {phone}")
                return False
            
            # Check subscription-level rate limit if subscription_id provided
            if subscription_id:
                sub_key = f"subscription:{subscription_id}"
                if not await self._check_individual_limit(sub_key, "subscription", current_time, is_emergency):
                    logger.warning(f"Rate limit exceeded for subscription: {subscription_id}")
                    return False
            
            # Check global rate limit
            global_key = "global"
            if not await self._check_individual_limit(global_key, "global", current_time, is_emergency):
                logger.warning("Global rate limit exceeded")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking rate limit: {str(e)}")
            # Allow notification on error to avoid blocking legitimate notifications
            return True
    
    async def _check_individual_limit(self, key: str, limit_type: str, 
                                    current_time: datetime, is_emergency: bool) -> bool:
        """Check individual rate limit"""
        try:
            rate_limit_key = f"{self.rate_limit_key_prefix}:{key}"
            
            # Get current rate limit data
            rate_data = await self.redis.get(rate_limit_key)
            
            if rate_data:
                rate_info = json.loads(rate_data)
                window_start = datetime.fromisoformat(rate_info['window_start'])
                current_count = rate_info['current_count']
            else:
                window_start = current_time
                current_count = 0
            
            # Get limits for this type
            limit_config = self.default_limits.get(
                "emergency" if is_emergency else limit_type,
                self.default_limits["phone"]
            )
            
            max_notifications = limit_config["max_notifications"]
            time_window_minutes = limit_config["time_window_minutes"]
            
            # Check if we need to reset the window
            if current_time - window_start > timedelta(minutes=time_window_minutes):
                window_start = current_time
                current_count = 0
            
            # Check if limit exceeded
            if current_count >= max_notifications:
                return False
            
            # Increment counter
            new_count = current_count + 1
            new_rate_info = {
                'current_count': new_count,
                'window_start': window_start.isoformat(),
                'max_notifications': max_notifications,
                'time_window_minutes': time_window_minutes
            }
            
            # Store updated rate limit data with expiration
            await self.redis.setex(
                rate_limit_key,
                timedelta(minutes=time_window_minutes + 5),  # Extra 5 minutes buffer
                json.dumps(new_rate_info)
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking individual rate limit for {key}: {str(e)}")
            return True
    
    async def get_rate_limit_status(self, phone: str, 
                                  subscription_id: Optional[int] = None) -> Dict[str, Any]:
        """Get current rate limit status"""
        try:
            status = {}
            
            # Phone rate limit status
            phone_key = f"{self.rate_limit_key_prefix}:phone:{phone}"
            phone_data = await self.redis.get(phone_key)
            if phone_data:
                phone_info = json.loads(phone_data)
                status['phone'] = {
                    'current_count': phone_info['current_count'],
                    'max_notifications': phone_info['max_notifications'],
                    'window_start': phone_info['window_start'],
                    'remaining': phone_info['max_notifications'] - phone_info['current_count']
                }
            
            # Subscription rate limit status
            if subscription_id:
                sub_key = f"{self.rate_limit_key_prefix}:subscription:{subscription_id}"
                sub_data = await self.redis.get(sub_key)
                if sub_data:
                    sub_info = json.loads(sub_data)
                    status['subscription'] = {
                        'current_count': sub_info['current_count'],
                        'max_notifications': sub_info['max_notifications'],
                        'window_start': sub_info['window_start'],
                        'remaining': sub_info['max_notifications'] - sub_info['current_count']
                    }
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting rate limit status: {str(e)}")
            return {}

class NotificationScheduler:
    """Handles notification scheduling and rate limiting"""
    
    def __init__(self):
        self.redis_client = None
        self.rate_limiter = None
        self.scheduled_notifications: Dict[str, NotificationSchedule] = {}
        self.scheduler_running = False
        self.scheduler_task = None
    
    async def initialize(self):
        """Initialize the scheduler"""
        try:
            self.redis_client = redis.from_url(settings.REDIS_URL)
            self.rate_limiter = NotificationRateLimiter(self.redis_client)
            
            # Load scheduled notifications from Redis
            await self._load_scheduled_notifications()
            
            logger.info("Notification scheduler initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize notification scheduler: {str(e)}")
            raise
    
    async def schedule_notification(self, phone: str, message: str, 
                                  channel: NotificationChannel,
                                  scheduled_time: datetime,
                                  schedule_type: ScheduleType = ScheduleType.DELAYED,
                                  subscription_id: Optional[int] = None,
                                  priority: int = 0,
                                  template_type: Optional[TemplateType] = None,
                                  template_variables: Optional[Dict[str, Any]] = None,
                                  language: Language = Language.ENGLISH,
                                  **kwargs) -> str:
        """Schedule a notification"""
        try:
            # Generate unique schedule ID
            schedule_id = f"sched_{datetime.now().timestamp()}_{hash(phone)}"
            
            # Render message from template if provided
            if template_type and template_variables:
                message = template_manager.render_notification(
                    template_type, channel.value, template_variables, language
                )
            
            # Create schedule
            schedule = NotificationSchedule(
                id=schedule_id,
                phone=phone,
                message=message,
                channel=channel,
                schedule_type=schedule_type,
                scheduled_time=scheduled_time,
                subscription_id=subscription_id,
                priority=priority,
                metadata=kwargs.get('metadata', {}),
                conditions=kwargs.get('conditions', {}),
                recurring_pattern=kwargs.get('recurring_pattern'),
                max_retries=kwargs.get('max_retries', 3)
            )
            
            # Store in memory and Redis
            self.scheduled_notifications[schedule_id] = schedule
            await self._save_scheduled_notification(schedule)
            
            logger.info(f"Scheduled notification {schedule_id} for {scheduled_time}")
            
            return schedule_id
            
        except Exception as e:
            logger.error(f"Failed to schedule notification: {str(e)}")
            raise
    
    async def schedule_immediate_notification(self, phone: str, message: str,
                                            channel: NotificationChannel,
                                            subscription_id: Optional[int] = None,
                                            priority: int = 0,
                                            is_emergency: bool = False,
                                            **kwargs) -> str:
        """Schedule an immediate notification with rate limiting"""
        try:
            # Check rate limits unless it's an emergency
            if not is_emergency:
                rate_limit_ok = await self.rate_limiter.check_rate_limit(
                    phone, subscription_id, is_emergency
                )
                
                if not rate_limit_ok:
                    raise Exception(f"Rate limit exceeded for phone {phone}")
            
            # Send immediately via notification engine
            notification_id = await notification_engine.send_notification(
                phone=phone,
                message=message,
                channel=channel,
                subscription_id=subscription_id,
                priority=priority,
                **kwargs
            )
            
            logger.info(f"Sent immediate notification {notification_id}")
            
            return notification_id
            
        except Exception as e:
            logger.error(f"Failed to send immediate notification: {str(e)}")
            raise
    
    async def cancel_scheduled_notification(self, schedule_id: str) -> bool:
        """Cancel a scheduled notification"""
        try:
            if schedule_id in self.scheduled_notifications:
                schedule = self.scheduled_notifications[schedule_id]
                schedule.status = "cancelled"
                
                # Update in Redis
                await self._save_scheduled_notification(schedule)
                
                logger.info(f"Cancelled scheduled notification {schedule_id}")
                return True
            else:
                logger.warning(f"Scheduled notification {schedule_id} not found")
                return False
                
        except Exception as e:
            logger.error(f"Failed to cancel scheduled notification: {str(e)}")
            return False
    
    async def start_scheduler(self):
        """Start the background scheduler task"""
        if self.scheduler_running:
            return
        
        self.scheduler_running = True
        self.scheduler_task = asyncio.create_task(self._scheduler_loop())
        
        logger.info("Notification scheduler started")
    
    async def stop_scheduler(self):
        """Stop the background scheduler task"""
        self.scheduler_running = False
        
        if self.scheduler_task:
            self.scheduler_task.cancel()
            try:
                await self.scheduler_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Notification scheduler stopped")
    
    async def _scheduler_loop(self):
        """Main scheduler loop"""
        while self.scheduler_running:
            try:
                current_time = datetime.now()
                
                # Process scheduled notifications
                due_notifications = [
                    schedule for schedule in self.scheduled_notifications.values()
                    if (schedule.status == "pending" and 
                        schedule.scheduled_time <= current_time)
                ]
                
                for schedule in due_notifications:
                    await self._process_scheduled_notification(schedule)
                
                # Clean up old completed/failed notifications
                await self._cleanup_old_schedules()
                
                # Sleep for 30 seconds before next check
                await asyncio.sleep(30)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in scheduler loop: {str(e)}")
                await asyncio.sleep(60)  # Wait longer on error
    
    async def _process_scheduled_notification(self, schedule: NotificationSchedule):
        """Process a scheduled notification"""
        try:
            # Check conditions if any
            if schedule.conditions and not await self._check_conditions(schedule.conditions):
                logger.info(f"Conditions not met for scheduled notification {schedule.id}")
                schedule.status = "skipped"
                await self._save_scheduled_notification(schedule)
                return
            
            # Check rate limits
            rate_limit_ok = await self.rate_limiter.check_rate_limit(
                schedule.phone, schedule.subscription_id
            )
            
            if not rate_limit_ok:
                # Reschedule for later
                schedule.scheduled_time = datetime.now() + timedelta(minutes=15)
                schedule.attempts += 1
                schedule.last_attempt = datetime.now()
                
                if schedule.attempts >= schedule.max_retries:
                    schedule.status = "failed"
                    logger.error(f"Scheduled notification {schedule.id} failed due to rate limiting")
                else:
                    logger.info(f"Rescheduled notification {schedule.id} due to rate limiting")
                
                await self._save_scheduled_notification(schedule)
                return
            
            # Send notification
            notification_id = await notification_engine.send_notification(
                phone=schedule.phone,
                message=schedule.message,
                channel=schedule.channel,
                subscription_id=schedule.subscription_id,
                priority=schedule.priority,
                metadata=schedule.metadata
            )
            
            schedule.status = "sent"
            schedule.last_attempt = datetime.now()
            schedule.metadata['notification_id'] = notification_id
            
            # Handle recurring notifications
            if schedule.schedule_type == ScheduleType.RECURRING and schedule.recurring_pattern:
                next_time = self._calculate_next_occurrence(
                    schedule.scheduled_time, schedule.recurring_pattern
                )
                if next_time:
                    # Create new schedule for next occurrence
                    new_schedule_id = await self.schedule_notification(
                        phone=schedule.phone,
                        message=schedule.message,
                        channel=schedule.channel,
                        scheduled_time=next_time,
                        schedule_type=ScheduleType.RECURRING,
                        subscription_id=schedule.subscription_id,
                        priority=schedule.priority,
                        recurring_pattern=schedule.recurring_pattern,
                        metadata=schedule.metadata
                    )
                    logger.info(f"Created recurring notification {new_schedule_id} for {next_time}")
            
            await self._save_scheduled_notification(schedule)
            logger.info(f"Processed scheduled notification {schedule.id}")
            
        except Exception as e:
            logger.error(f"Failed to process scheduled notification {schedule.id}: {str(e)}")
            schedule.status = "failed"
            schedule.last_attempt = datetime.now()
            schedule.attempts += 1
            await self._save_scheduled_notification(schedule)
    
    async def _check_conditions(self, conditions: Dict[str, Any]) -> bool:
        """Check if conditions are met for conditional notifications"""
        # Placeholder for condition checking logic
        # Could check things like weather, traffic, bus status, etc.
        return True
    
    def _calculate_next_occurrence(self, current_time: datetime, pattern: str) -> Optional[datetime]:
        """Calculate next occurrence for recurring notifications"""
        # Simple recurring patterns - could be extended with cron-like syntax
        if pattern == "daily":
            return current_time + timedelta(days=1)
        elif pattern == "weekly":
            return current_time + timedelta(weeks=1)
        elif pattern == "hourly":
            return current_time + timedelta(hours=1)
        else:
            return None
    
    async def _save_scheduled_notification(self, schedule: NotificationSchedule):
        """Save scheduled notification to Redis"""
        try:
            key = f"scheduled_notification:{schedule.id}"
            data = {
                'id': schedule.id,
                'phone': schedule.phone,
                'message': schedule.message,
                'channel': schedule.channel.value,
                'schedule_type': schedule.schedule_type.value,
                'scheduled_time': schedule.scheduled_time.isoformat(),
                'subscription_id': schedule.subscription_id,
                'priority': schedule.priority,
                'max_retries': schedule.max_retries,
                'metadata': schedule.metadata,
                'conditions': schedule.conditions,
                'recurring_pattern': schedule.recurring_pattern,
                'created_at': schedule.created_at.isoformat(),
                'attempts': schedule.attempts,
                'last_attempt': schedule.last_attempt.isoformat() if schedule.last_attempt else None,
                'status': schedule.status
            }
            
            await self.redis_client.setex(
                key,
                timedelta(days=7),  # Keep for 7 days
                json.dumps(data)
            )
            
        except Exception as e:
            logger.error(f"Failed to save scheduled notification: {str(e)}")
    
    async def _load_scheduled_notifications(self):
        """Load scheduled notifications from Redis"""
        try:
            pattern = "scheduled_notification:*"
            keys = await self.redis_client.keys(pattern)
            
            for key in keys:
                data = await self.redis_client.get(key)
                if data:
                    schedule_data = json.loads(data)
                    
                    schedule = NotificationSchedule(
                        id=schedule_data['id'],
                        phone=schedule_data['phone'],
                        message=schedule_data['message'],
                        channel=NotificationChannel(schedule_data['channel']),
                        schedule_type=ScheduleType(schedule_data['schedule_type']),
                        scheduled_time=datetime.fromisoformat(schedule_data['scheduled_time']),
                        subscription_id=schedule_data.get('subscription_id'),
                        priority=schedule_data.get('priority', 0),
                        max_retries=schedule_data.get('max_retries', 3),
                        metadata=schedule_data.get('metadata', {}),
                        conditions=schedule_data.get('conditions', {}),
                        recurring_pattern=schedule_data.get('recurring_pattern'),
                        created_at=datetime.fromisoformat(schedule_data['created_at']),
                        attempts=schedule_data.get('attempts', 0),
                        last_attempt=datetime.fromisoformat(schedule_data['last_attempt']) if schedule_data.get('last_attempt') else None,
                        status=schedule_data.get('status', 'pending')
                    )
                    
                    self.scheduled_notifications[schedule.id] = schedule
            
            logger.info(f"Loaded {len(self.scheduled_notifications)} scheduled notifications")
            
        except Exception as e:
            logger.error(f"Failed to load scheduled notifications: {str(e)}")
    
    async def _cleanup_old_schedules(self):
        """Clean up old completed/failed schedules"""
        try:
            current_time = datetime.now()
            cutoff_time = current_time - timedelta(days=1)  # Keep for 1 day
            
            to_remove = []
            for schedule_id, schedule in self.scheduled_notifications.items():
                if (schedule.status in ["sent", "failed", "cancelled", "skipped"] and
                    schedule.created_at < cutoff_time):
                    to_remove.append(schedule_id)
            
            for schedule_id in to_remove:
                del self.scheduled_notifications[schedule_id]
                # Remove from Redis
                await self.redis_client.delete(f"scheduled_notification:{schedule_id}")
            
            if to_remove:
                logger.info(f"Cleaned up {len(to_remove)} old scheduled notifications")
                
        except Exception as e:
            logger.error(f"Failed to cleanup old schedules: {str(e)}")
    
    async def get_scheduler_stats(self) -> Dict[str, Any]:
        """Get scheduler statistics"""
        try:
            stats = {
                'total_scheduled': len(self.scheduled_notifications),
                'by_status': {},
                'by_type': {},
                'scheduler_running': self.scheduler_running
            }
            
            for schedule in self.scheduled_notifications.values():
                # Count by status
                status = schedule.status
                stats['by_status'][status] = stats['by_status'].get(status, 0) + 1
                
                # Count by type
                schedule_type = schedule.schedule_type.value
                stats['by_type'][schedule_type] = stats['by_type'].get(schedule_type, 0) + 1
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get scheduler stats: {str(e)}")
            return {}
    
    async def cleanup(self):
        """Cleanup resources"""
        await self.stop_scheduler()
        
        if self.redis_client:
            await self.redis_client.close()

# Global notification scheduler instance
notification_scheduler = NotificationScheduler()