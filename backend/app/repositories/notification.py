"""
Notification repository for managing notification records
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, desc, func
from datetime import datetime, timedelta

from .base import BaseRepository
from ..models.notification import Notification, NotificationStatus
from ..schemas.notification import NotificationCreate, NotificationUpdate

class NotificationRepository(BaseRepository[Notification, NotificationCreate, NotificationUpdate]):
    """Repository for Notification model"""
    
    def __init__(self, db: Session):
        super().__init__(Notification, db)
    
    def get_by_subscription(self, subscription_id: int, limit: int = 50) -> List[Notification]:
        """Get notifications for a subscription"""
        cache_key = self._get_cache_key("subscription", f"{subscription_id}_{limit}")
        
        cached_data = self._cache_get(cache_key)
        if cached_data:
            return cached_data
        
        notifications = self.db.query(Notification).filter(
            Notification.subscription_id == subscription_id
        ).order_by(desc(Notification.created_at)).limit(limit).all()
        
        if notifications:
            data = [self._model_to_dict(notif) for notif in notifications]
            self._cache_set(cache_key, data, ttl=300)  # 5 minutes TTL
        
        return notifications
    
    def get_by_phone(self, phone: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get notifications for a phone number with subscription details"""
        cache_key = self._get_cache_key("phone", f"{phone}_{limit}")
        
        cached_data = self._cache_get(cache_key)
        if cached_data:
            return cached_data
        
        notifications = self.db.query(Notification).join(
            Notification.subscription
        ).filter(
            Notification.subscription.has(phone=phone)
        ).options(
            joinedload(Notification.subscription).joinedload('stop')
        ).order_by(desc(Notification.created_at)).limit(limit).all()
        
        result = []
        for notification in notifications:
            notif_data = self._model_to_dict(notification)
            if notification.subscription:
                notif_data['subscription'] = {
                    'id': notification.subscription.id,
                    'phone': notification.subscription.phone,
                    'channel': notification.subscription.channel.value,
                    'eta_threshold': notification.subscription.eta_threshold
                }
                if notification.subscription.stop:
                    notif_data['stop'] = {
                        'id': notification.subscription.stop.id,
                        'name': notification.subscription.stop.name,
                        'name_kannada': notification.subscription.stop.name_kannada
                    }
            result.append(notif_data)
        
        if result:
            self._cache_set(cache_key, result, ttl=180)  # 3 minutes TTL
        
        return result
    
    def get_by_status(self, status: NotificationStatus, limit: int = 100) -> List[Notification]:
        """Get notifications by status"""
        cache_key = self._get_cache_key("status", f"{status.value}_{limit}")
        
        cached_data = self._cache_get(cache_key)
        if cached_data:
            return cached_data
        
        notifications = self.db.query(Notification).filter(
            Notification.status == status
        ).order_by(desc(Notification.created_at)).limit(limit).all()
        
        if notifications:
            data = [self._model_to_dict(notif) for notif in notifications]
            self._cache_set(cache_key, data, ttl=60)  # 1 minute TTL for status queries
        
        return notifications
    
    def get_pending_notifications(self, older_than_minutes: int = 5) -> List[Notification]:
        """Get notifications that are pending for too long"""
        cutoff_time = datetime.now() - timedelta(minutes=older_than_minutes)
        
        return self.db.query(Notification).filter(
            and_(
                Notification.status == NotificationStatus.PENDING,
                Notification.created_at < cutoff_time
            )
        ).all()
    
    def get_failed_notifications(self, since_hours: int = 24) -> List[Notification]:
        """Get failed notifications within time period"""
        since_time = datetime.now() - timedelta(hours=since_hours)
        
        return self.db.query(Notification).filter(
            and_(
                Notification.status == NotificationStatus.FAILED,
                Notification.created_at >= since_time
            )
        ).order_by(desc(Notification.created_at)).all()
    
    def get_delivery_stats(self, since_hours: int = 24) -> Dict[str, Any]:
        """Get notification delivery statistics"""
        cache_key = self._get_cache_key("stats", f"delivery_{since_hours}")
        
        cached_data = self._cache_get(cache_key)
        if cached_data:
            return cached_data
        
        since_time = datetime.now() - timedelta(hours=since_hours)
        
        # Get counts by status
        status_counts = self.db.query(
            Notification.status,
            func.count(Notification.id).label('count')
        ).filter(
            Notification.created_at >= since_time
        ).group_by(Notification.status).all()
        
        # Get counts by channel
        channel_counts = self.db.query(
            Notification.channel,
            func.count(Notification.id).label('count')
        ).filter(
            Notification.created_at >= since_time
        ).group_by(Notification.channel).all()
        
        # Calculate success rate
        total_notifications = sum(count for _, count in status_counts)
        successful_notifications = sum(
            count for status, count in status_counts 
            if status in [NotificationStatus.SENT, NotificationStatus.DELIVERED]
        )
        
        success_rate = (successful_notifications / total_notifications * 100) if total_notifications > 0 else 0
        
        stats = {
            'total_notifications': total_notifications,
            'success_rate': round(success_rate, 2),
            'status_breakdown': {status.value: count for status, count in status_counts},
            'channel_breakdown': {channel: count for channel, count in channel_counts},
            'period_hours': since_hours
        }
        
        self._cache_set(cache_key, stats, ttl=300)  # 5 minutes TTL
        return stats
    
    def update_status(self, notification_id: int, status: NotificationStatus, 
                     error_message: Optional[str] = None) -> Optional[Notification]:
        """Update notification status"""
        notification = self.get(notification_id, use_cache=False)
        if not notification:
            return None
        
        notification.status = status
        
        if status == NotificationStatus.SENT:
            notification.sent_at = datetime.now()
        elif status == NotificationStatus.DELIVERED:
            notification.delivered_at = datetime.now()
        elif status == NotificationStatus.FAILED and error_message:
            notification.error_message = error_message
        
        self.db.commit()
        self.db.refresh(notification)
        
        # Invalidate related cache
        self._cache_delete_pattern(f"{self.model.__tablename__}:*")
        
        return notification
    
    def bulk_update_status(self, notification_ids: List[int], 
                          status: NotificationStatus) -> int:
        """Bulk update notification status"""
        updated_count = self.db.query(Notification).filter(
            Notification.id.in_(notification_ids)
        ).update(
            {
                'status': status,
                'sent_at': datetime.now() if status == NotificationStatus.SENT else None,
                'delivered_at': datetime.now() if status == NotificationStatus.DELIVERED else None
            },
            synchronize_session=False
        )
        
        self.db.commit()
        
        # Invalidate cache
        self._cache_delete_pattern(f"{self.model.__tablename__}:*")
        
        return updated_count
    
    def cleanup_old_notifications(self, older_than_days: int = 30) -> int:
        """Clean up old notification records"""
        cutoff_date = datetime.now() - timedelta(days=older_than_days)
        
        deleted_count = self.db.query(Notification).filter(
            Notification.created_at < cutoff_date
        ).delete(synchronize_session=False)
        
        self.db.commit()
        
        # Invalidate cache
        self._cache_delete_pattern(f"{self.model.__tablename__}:*")
        
        return deleted_count
    
    def get_notification_history(self, phone: str, days: int = 7) -> List[Dict[str, Any]]:
        """Get notification history for a phone number"""
        cache_key = self._get_cache_key("history", f"{phone}_{days}")
        
        cached_data = self._cache_get(cache_key)
        if cached_data:
            return cached_data
        
        since_date = datetime.now() - timedelta(days=days)
        
        notifications = self.db.query(Notification).join(
            Notification.subscription
        ).filter(
            and_(
                Notification.subscription.has(phone=phone),
                Notification.created_at >= since_date
            )
        ).options(
            joinedload(Notification.subscription).joinedload('stop').joinedload('route')
        ).order_by(desc(Notification.created_at)).all()
        
        result = []
        for notification in notifications:
            notif_data = {
                'id': notification.id,
                'message': notification.message,
                'channel': notification.channel,
                'status': notification.status.value,
                'created_at': notification.created_at.isoformat(),
                'sent_at': notification.sent_at.isoformat() if notification.sent_at else None,
                'delivered_at': notification.delivered_at.isoformat() if notification.delivered_at else None,
                'error_message': notification.error_message
            }
            
            if notification.subscription and notification.subscription.stop:
                stop = notification.subscription.stop
                notif_data['stop'] = {
                    'name': stop.name,
                    'name_kannada': stop.name_kannada
                }
                
                if stop.route:
                    notif_data['route'] = {
                        'name': stop.route.name,
                        'route_number': stop.route.route_number
                    }
            
            result.append(notif_data)
        
        if result:
            self._cache_set(cache_key, result, ttl=600)  # 10 minutes TTL
        
        return result