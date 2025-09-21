from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...core.dependencies import get_current_user, get_current_admin_user
from ...models.user import User
from ...models.emergency import EmergencyStatus
from ...schemas.emergency import (
    EmergencyReportCreate,
    EmergencyIncidentResponse,
    EmergencyIncidentUpdate,
    EmergencyBroadcastCreate,
    EmergencyBroadcastResponse,
    EmergencyContactCreate,
    EmergencyContactResponse,
    EmergencyStatsResponse,
    EmergencyDashboardResponse
)
from ...repositories.emergency import (
    EmergencyRepository,
    EmergencyBroadcastRepository,
    EmergencyContactRepository
)
from ...services.notification_engine import NotificationEngine
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/report", response_model=EmergencyIncidentResponse)
async def report_emergency(
    incident_data: EmergencyReportCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Report an emergency incident"""
    try:
        emergency_repo = EmergencyRepository(db)
        
        # Get client IP address
        client_ip = request.client.host
        
        # Create the incident
        incident = emergency_repo.create_incident(
            incident_data=incident_data,
            user_id=current_user.id if current_user else None,
            ip_address=client_ip
        )
        
        # Log the emergency report
        logger.warning(f"Emergency reported: {incident.type} at {incident.latitude}, {incident.longitude}")
        
        # TODO: Trigger immediate notifications to admin dashboard
        # This would be handled by WebSocket or push notifications
        
        # Simulate emergency call if enabled
        if incident.type in ['medical', 'accident']:
            # In a real system, this would trigger actual emergency services
            logger.info(f"Emergency call simulation for incident {incident.id}")
            incident.emergency_call_made = True
            incident.emergency_call_time = incident.reported_at
            db.commit()
        
        return incident
        
    except Exception as e:
        logger.error(f"Error reporting emergency: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to report emergency"
        )

@router.get("/incidents", response_model=List[EmergencyIncidentResponse])
async def get_incidents(
    status_filter: Optional[EmergencyStatus] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get emergency incidents (admin only)"""
    emergency_repo = EmergencyRepository(db)
    
    if status_filter:
        incidents = emergency_repo.get_incidents_by_status(status_filter)
    else:
        incidents = emergency_repo.get_recent_incidents(limit)
    
    return incidents

@router.get("/incidents/{incident_id}", response_model=EmergencyIncidentResponse)
async def get_incident(
    incident_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get a specific emergency incident (admin only)"""
    emergency_repo = EmergencyRepository(db)
    incident = emergency_repo.get_by_id(incident_id)
    
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Emergency incident not found"
        )
    
    return incident

@router.put("/incidents/{incident_id}", response_model=EmergencyIncidentResponse)
async def update_incident(
    incident_id: int,
    update_data: EmergencyIncidentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Update an emergency incident (admin only)"""
    emergency_repo = EmergencyRepository(db)
    
    # Set the admin who is updating the incident
    if update_data.assigned_admin_id is None:
        update_data.assigned_admin_id = current_user.id
    
    incident = emergency_repo.update_incident(incident_id, update_data)
    
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Emergency incident not found"
        )
    
    logger.info(f"Emergency incident {incident_id} updated by admin {current_user.id}")
    return incident

@router.post("/broadcast", response_model=EmergencyBroadcastResponse)
async def create_emergency_broadcast(
    broadcast_data: EmergencyBroadcastCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Create an emergency broadcast (admin only)"""
    try:
        broadcast_repo = EmergencyBroadcastRepository(db)
        
        # Create the broadcast
        broadcast = broadcast_repo.create_broadcast(
            broadcast_data=broadcast_data,
            admin_id=current_user.id
        )
        
        # TODO: Trigger actual broadcast delivery
        # This would integrate with the notification engine
        logger.info(f"Emergency broadcast created by admin {current_user.id}: {broadcast.title}")
        
        # Simulate delivery stats for demo
        broadcast_repo.update_delivery_stats(
            broadcast_id=broadcast.id,
            total_recipients=100,  # Mock data
            successful_deliveries=95,
            failed_deliveries=5
        )
        
        return broadcast
        
    except Exception as e:
        logger.error(f"Error creating emergency broadcast: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create emergency broadcast"
        )

@router.get("/broadcasts", response_model=List[EmergencyBroadcastResponse])
async def get_broadcasts(
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get emergency broadcasts (admin only)"""
    broadcast_repo = EmergencyBroadcastRepository(db)
    broadcasts = broadcast_repo.get_recent_broadcasts(limit)
    return broadcasts

@router.post("/contacts", response_model=EmergencyContactResponse)
async def create_emergency_contact(
    contact_data: EmergencyContactCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Create an emergency contact (admin only)"""
    contact_repo = EmergencyContactRepository(db)
    contact = contact_repo.create_contact(contact_data)
    return contact

@router.get("/contacts", response_model=List[EmergencyContactResponse])
async def get_emergency_contacts(
    db: Session = Depends(get_db)
):
    """Get emergency contacts (public endpoint)"""
    contact_repo = EmergencyContactRepository(db)
    contacts = contact_repo.get_active_contacts()
    return contacts

@router.get("/stats", response_model=EmergencyStatsResponse)
async def get_emergency_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get emergency statistics (admin only)"""
    emergency_repo = EmergencyRepository(db)
    
    stats = emergency_repo.get_incident_stats()
    recent_incidents = emergency_repo.get_recent_incidents(5)
    
    return EmergencyStatsResponse(
        **stats,
        recent_incidents=recent_incidents
    )

@router.get("/dashboard", response_model=EmergencyDashboardResponse)
async def get_emergency_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get emergency dashboard data (admin only)"""
    emergency_repo = EmergencyRepository(db)
    broadcast_repo = EmergencyBroadcastRepository(db)
    contact_repo = EmergencyContactRepository(db)
    
    # Get stats
    stats = emergency_repo.get_incident_stats()
    recent_incidents = emergency_repo.get_recent_incidents(5)
    
    # Get recent broadcasts
    recent_broadcasts = broadcast_repo.get_recent_broadcasts(5)
    
    # Get emergency contacts
    emergency_contacts = contact_repo.get_active_contacts()
    
    return EmergencyDashboardResponse(
        stats=EmergencyStatsResponse(
            **stats,
            recent_incidents=recent_incidents
        ),
        recent_broadcasts=recent_broadcasts,
        emergency_contacts=emergency_contacts
    )