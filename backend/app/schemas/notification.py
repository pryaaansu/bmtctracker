"""
Notification schemas for API serialization
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

from ..models.notification import NotificationStatus
from ..models.subscription import NotificationChannel

class NotificationBase(BaseModel):
    """Base notification schema"""
    message: str = Field(..., description="Notification message content")
    channel: str = Field(..., description="Notification channel (sms, voice, whatsapp, push)")

class NotificationCreate(NotificationBase):
    """Schema for creating notifications"""
    subscription_id: Optional[int] = Field(None, description="Associated subscription ID")

class NotificationUpdate(BaseModel):
    """Schema for updating notifications"""
    status: Optional[NotificationStatus] = Field(None, description="Notification status")
    error_message: Optional[str] = Field(None, description="Error message if failed")

class NotificationResponse(NotificationBase):
    """Schema for notification responses"""
    id: int = Field(..., description="Notification ID")
    subscription_id: Optional[int] = Field(None, description="Associated subscription ID")
    status: NotificationStatus = Field(..., description="Current notification status")
    sent_at: Optional[datetime] = Field(None, description="Time when notification was sent")
    delivered_at: Optional[datetime] = Field(None, description="Time when notification was delivered")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    created_at: datetime = Field(..., description="Creation timestamp")
    
    class Config:
        from_attributes = True

class NotificationHistoryResponse(BaseModel):
    """Schema for notification history with additional context"""
    id: int = Field(..., description="Notification ID")
    message: str = Field(..., description="Notification message")
    channel: str = Field(..., description="Notification channel")
    status: str = Field(..., description="Notification status")
    created_at: str = Field(..., description="Creation timestamp (ISO format)")
    sent_at: Optional[str] = Field(None, description="Sent timestamp (ISO format)")
    delivered_at: Optional[str] = Field(None, description="Delivered timestamp (ISO format)")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    stop: Optional[Dict[str, str]] = Field(None, description="Associated stop information")
    route: Optional[Dict[str, str]] = Field(None, description="Associated route information")

class NotificationStatsResponse(BaseModel):
    """Schema for notification statistics"""
    total_notifications: int = Field(..., description="Total number of notifications")
    success_rate: float = Field(..., description="Success rate percentage")
    status_breakdown: Dict[str, int] = Field(..., description="Count by status")
    channel_breakdown: Dict[str, int] = Field(..., description="Count by channel")
    period_hours: int = Field(..., description="Statistics period in hours")

class NotificationSendRequest(BaseModel):
    """Schema for sending notifications"""
    phone: str = Field(..., description="Phone number to send notification to")
    message: str = Field(..., description="Message content")
    channel: NotificationChannel = Field(..., description="Notification channel")
    subscription_id: Optional[int] = Field(None, description="Associated subscription ID")
    priority: int = Field(0, description="Notification priority (0=normal, 1=high)")
    max_retries: int = Field(3, description="Maximum retry attempts")

class NotificationSendResponse(BaseModel):
    """Schema for notification send response"""
    notification_id: str = Field(..., description="Unique notification ID")
    status: str = Field(..., description="Initial status")
    message: str = Field(..., description="Response message")

class BulkNotificationRequest(BaseModel):
    """Schema for bulk notification sending"""
    notifications: list[NotificationSendRequest] = Field(..., description="List of notifications to send")
    batch_size: int = Field(10, description="Batch processing size")

class BulkNotificationResponse(BaseModel):
    """Schema for bulk notification response"""
    total_queued: int = Field(..., description="Total notifications queued")
    failed_count: int = Field(..., description="Number of failed notifications")
    notification_ids: list[str] = Field(..., description="List of notification IDs")
    errors: list[str] = Field(default_factory=list, description="List of errors if any")

class NotificationEngineStatsResponse(BaseModel):
    """Schema for notification engine statistics"""
    queue_stats: Dict[str, int] = Field(..., description="Queue statistics")
    adapters: list[str] = Field(..., description="Available adapters")
    workers_running: int = Field(..., description="Number of active workers")
    demo_mode: bool = Field(..., description="Whether running in demo mode")

class NotificationTemplateRequest(BaseModel):
    """Schema for notification templates"""
    template_name: str = Field(..., description="Template name")
    message_en: str = Field(..., description="Message template in English")
    message_kn: str = Field(..., description="Message template in Kannada")
    variables: list[str] = Field(default_factory=list, description="Template variables")

class NotificationTemplateResponse(NotificationTemplateRequest):
    """Schema for notification template response"""
    id: int = Field(..., description="Template ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        from_attributes = True