from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from ..models.subscription import NotificationChannel

class SubscriptionBase(BaseModel):
    phone: str
    stop_id: int
    channel: NotificationChannel
    eta_threshold: int = 5

class SubscriptionCreate(SubscriptionBase):
    pass

class SubscriptionUpdate(BaseModel):
    phone: Optional[str] = None
    stop_id: Optional[int] = None
    channel: Optional[NotificationChannel] = None
    eta_threshold: Optional[int] = None
    is_active: Optional[bool] = None

class SubscriptionResponse(SubscriptionBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True