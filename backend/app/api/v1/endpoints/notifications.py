"""
Notification API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional

from ....core.database import get_db
from ....core.dependencies import get_current_user
from ....repositories.notification import NotificationRepository
from ....schemas.notification import (
    NotificationResponse,
    NotificationHistoryResponse,
    NotificationStatsResponse,
    NotificationSendRequest,
    NotificationSendResponse,
    BulkNotificationRequest,
    BulkNotificationResponse,
    NotificationEngineStatsResponse
)
from ....services.notification_engine import notification_engine
from ....models.user import User
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/send", response_model=NotificationSendResponse)
async def send_notification(
    request: NotificationSendRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Send a single notification"""
    try:
        notification_id = await notification_engine.send_notification(
            phone=request.phone,
            message=request.message,
            channel=request.channel,
            subscription_id=request.subscription_id,
            priority=request.priority,
            max_retries=request.max_retries
        )
        
        return NotificationSendResponse(
            notification_id=notification_id,
            status="queued",
            message="Notification queued successfully"
        )
        
    except Exception as e:
        logger.error(f"Failed to send notification: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/send/bulk", response_model=BulkNotificationResponse)
async def send_bulk_notifications(
    request: BulkNotificationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Send multiple notifications in bulk"""
    try:
        notification_ids = []
        errors = []
        failed_count = 0
        
        for notification_request in request.notifications:
            try:
                notification_id = await notification_engine.send_notification(
                    phone=notification_request.phone,
                    message=notification_request.message,
                    channel=notification_request.channel,
                    subscription_id=notification_request.subscription_id,
                    priority=notification_request.priority,
                    max_retries=notification_request.max_retries
                )
                notification_ids.append(notification_id)
                
            except Exception as e:
                failed_count += 1
                errors.append(f"Failed to queue notification for {notification_request.phone}: {str(e)}")
        
        return BulkNotificationResponse(
            total_queued=len(notification_ids),
            failed_count=failed_count,
            notification_ids=notification_ids,
            errors=errors
        )
        
    except Exception as e:
        logger.error(f"Failed to send bulk notifications: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history/{phone}", response_model=List[NotificationHistoryResponse])
async def get_notification_history(
    phone: str,
    days: int = 7,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get notification history for a phone number"""
    try:
        notification_repo = NotificationRepository(db)
        history = notification_repo.get_notification_history(phone, days)
        
        return [NotificationHistoryResponse(**item) for item in history]
        
    except Exception as e:
        logger.error(f"Failed to get notification history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats", response_model=NotificationStatsResponse)
async def get_notification_stats(
    hours: int = 24,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get notification delivery statistics"""
    try:
        notification_repo = NotificationRepository(db)
        stats = notification_repo.get_delivery_stats(hours)
        
        return NotificationStatsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Failed to get notification stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/engine/stats", response_model=NotificationEngineStatsResponse)
async def get_engine_stats(
    current_user: User = Depends(get_current_user)
):
    """Get notification engine statistics"""
    try:
        stats = await notification_engine.get_stats()
        return NotificationEngineStatsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Failed to get engine stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{notification_id}", response_model=NotificationResponse)
async def get_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get notification by ID"""
    try:
        notification_repo = NotificationRepository(db)
        notification = notification_repo.get(notification_id)
        
        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        return NotificationResponse.from_orm(notification)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get notification: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[NotificationResponse])
async def get_notifications(
    skip: int = 0,
    limit: int = 50,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get notifications with optional filtering"""
    try:
        notification_repo = NotificationRepository(db)
        
        if status:
            from ....models.notification import NotificationStatus
            try:
                status_enum = NotificationStatus(status)
                notifications = notification_repo.get_by_status(status_enum, limit)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        else:
            notifications = notification_repo.get_all(skip=skip, limit=limit)
        
        return [NotificationResponse.from_orm(notif) for notif in notifications]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get notifications: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cleanup")
async def cleanup_old_notifications(
    days: int = 30,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Clean up old notification records"""
    def cleanup_task():
        try:
            notification_repo = NotificationRepository(db)
            deleted_count = notification_repo.cleanup_old_notifications(days)
            logger.info(f"Cleaned up {deleted_count} old notifications")
        except Exception as e:
            logger.error(f"Failed to cleanup notifications: {str(e)}")
    
    background_tasks.add_task(cleanup_task)
    
    return {"message": f"Cleanup task scheduled for notifications older than {days} days"}