"""
Subscription repository with notification management
"""
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_

from .base import BaseRepository
from ..models.subscription import Subscription, NotificationChannel
from ..schemas.subscription import SubscriptionCreate, SubscriptionUpdate

class SubscriptionRepository(BaseRepository[Subscription, SubscriptionCreate, SubscriptionUpdate]):
    """Repository for Subscription model with notification logic"""
    
    def __init__(self, db: Session):
        super().__init__(Subscription, db)
    
    def get_by_phone(self, phone: str) -> List[Subscription]:
        """Get all subscriptions for a phone number"""
        cache_key = self._get_cache_key("phone", phone)
        
        cached_data = self._cache_get(cache_key)
        if cached_data:
            return cached_data
        
        subscriptions = self.db.query(Subscription).filter(
            Subscription.phone == phone
        ).all()
        
        if subscriptions:
            data = [self._model_to_dict(sub) for sub in subscriptions]
            self._cache_set(cache_key, data, ttl=300)  # 5 minutes TTL
        return subscriptions
    
    def get_active_by_phone(self, phone: str) -> List[Subscription]:
        """Get active subscriptions for a phone number"""
        cache_key = self._get_cache_key("active_phone", phone)
        
        cached_data = self._cache_get(cache_key)
        if cached_data:
            return cached_data
        
        subscriptions = self.db.query(Subscription).filter(
            and_(
                Subscription.phone == phone,
                Subscription.is_active == True
            )
        ).all()
        
        if subscriptions:
            data = [self._model_to_dict(sub) for sub in subscriptions]
            self._cache_set(cache_key, data, ttl=180)  # 3 minutes TTL
        return subscriptions
    
    def get_by_stop(self, stop_id: int) -> List[Subscription]:
        """Get all active subscriptions for a stop"""
        cache_key = self._get_cache_key("stop", stop_id)
        
        cached_data = self._cache_get(cache_key)
        if cached_data:
            return cached_data
        
        subscriptions = self.db.query(Subscription).filter(
            and_(
                Subscription.stop_id == stop_id,
                Subscription.is_active == True
            )
        ).all()
        
        if subscriptions:
            data = [self._model_to_dict(sub) for sub in subscriptions]
            self._cache_set(cache_key, data, ttl=60)  # 1 minute TTL for real-time notifications
        return subscriptions
    
    def get_by_channel(self, channel: NotificationChannel) -> List[Subscription]:
        """Get active subscriptions by notification channel"""
        cache_key = self._get_cache_key("channel", channel.value)
        
        cached_data = self._cache_get(cache_key)
        if cached_data:
            return cached_data
        
        subscriptions = self.db.query(Subscription).filter(
            and_(
                Subscription.channel == channel,
                Subscription.is_active == True
            )
        ).all()
        
        if subscriptions:
            data = [self._model_to_dict(sub) for sub in subscriptions]
            self._cache_set(cache_key, data, ttl=120)  # 2 minutes TTL
        return subscriptions
    
    def get_with_stop_info(self, subscription_id: int) -> Optional[dict]:
        """Get subscription with stop and route information"""
        cache_key = self._get_cache_key("with_stop", subscription_id)
        
        cached_data = self._cache_get(cache_key)
        if cached_data:
            return cached_data
        
        subscription = self.db.query(Subscription).options(
            joinedload(Subscription.stop).joinedload('route')
        ).filter(Subscription.id == subscription_id).first()
        
        if subscription:
            sub_data = self._model_to_dict(subscription)
            if subscription.stop:
                sub_data['stop'] = {
                    'id': subscription.stop.id,
                    'name': subscription.stop.name,
                    'name_kannada': subscription.stop.name_kannada,
                    'latitude': float(subscription.stop.latitude),
                    'longitude': float(subscription.stop.longitude),
                    'stop_order': subscription.stop.stop_order
                }
                if subscription.stop.route:
                    sub_data['route'] = {
                        'id': subscription.stop.route.id,
                        'name': subscription.stop.route.name,
                        'route_number': subscription.stop.route.route_number
                    }
            
            self._cache_set(cache_key, sub_data, ttl=300)  # 5 minutes TTL
            return sub_data
        
        return None
    
    def create_or_update_subscription(self, phone: str, stop_id: int, 
                                    channel: NotificationChannel, 
                                    eta_threshold: int = 5) -> Subscription:
        """Create new subscription or update existing one"""
        # Check if subscription already exists
        existing = self.db.query(Subscription).filter(
            and_(
                Subscription.phone == phone,
                Subscription.stop_id == stop_id,
                Subscription.channel == channel
            )
        ).first()
        
        if existing:
            # Update existing subscription
            existing.eta_threshold = eta_threshold
            existing.is_active = True
            self.db.commit()
            self.db.refresh(existing)
            subscription = existing
        else:
            # Create new subscription
            subscription_data = {
                'phone': phone,
                'stop_id': stop_id,
                'channel': channel,
                'eta_threshold': eta_threshold,
                'is_active': True
            }
            subscription = Subscription(**subscription_data)
            self.db.add(subscription)
            self.db.commit()
            self.db.refresh(subscription)
        
        # Invalidate related cache
        self._cache_delete_pattern(f"{self.model.__tablename__}:*")
        
        return subscription
    
    def deactivate_subscription(self, subscription_id: int) -> Optional[Subscription]:
        """Deactivate a subscription"""
        subscription = self.get(subscription_id, use_cache=False)
        if subscription:
            subscription.is_active = False
            self.db.commit()
            self.db.refresh(subscription)
            
            # Invalidate related cache
            self._cache_delete_pattern(f"{self.model.__tablename__}:*")
        
        return subscription
    
    def get_subscriptions_for_notification(self, stop_id: int, eta_minutes: int) -> List[Subscription]:
        """Get subscriptions that should be notified based on ETA threshold"""
        subscriptions = self.get_by_stop(stop_id)
        
        # Filter by ETA threshold
        return [
            sub for sub in subscriptions 
            if sub.eta_threshold >= eta_minutes and sub.is_active
        ]