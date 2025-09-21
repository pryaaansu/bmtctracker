from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
from datetime import datetime, timedelta
from ..models.emergency import EmergencyIncident, EmergencyBroadcast, EmergencyContact, EmergencyType, EmergencyStatus
from ..schemas.emergency import EmergencyReportCreate, EmergencyIncidentUpdate, EmergencyBroadcastCreate, EmergencyContactCreate
from .base import BaseRepository

class EmergencyRepository(BaseRepository[EmergencyIncident]):
    def __init__(self, db: Session):
        super().__init__(EmergencyIncident, db)

    def create_incident(
        self, 
        incident_data: EmergencyReportCreate, 
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None
    ) -> EmergencyIncident:
        """Create a new emergency incident"""
        incident = EmergencyIncident(
            type=incident_data.type,
            description=incident_data.description,
            latitude=incident_data.latitude,
            longitude=incident_data.longitude,
            user_id=user_id,
            phone_number=incident_data.phone_number,
            user_agent=incident_data.user_agent,
            ip_address=ip_address,
            status=EmergencyStatus.REPORTED
        )
        
        self.db.add(incident)
        self.db.commit()
        self.db.refresh(incident)
        return incident

    def update_incident(self, incident_id: int, update_data: EmergencyIncidentUpdate) -> Optional[EmergencyIncident]:
        """Update an emergency incident"""
        incident = self.get_by_id(incident_id)
        if not incident:
            return None

        update_dict = update_data.dict(exclude_unset=True)
        
        # Set timestamps based on status changes
        if 'status' in update_dict:
            if update_dict['status'] == EmergencyStatus.ACKNOWLEDGED and not incident.acknowledged_at:
                update_dict['acknowledged_at'] = datetime.utcnow()
            elif update_dict['status'] in [EmergencyStatus.RESOLVED, EmergencyStatus.CLOSED] and not incident.resolved_at:
                update_dict['resolved_at'] = datetime.utcnow()

        for field, value in update_dict.items():
            setattr(incident, field, value)

        self.db.commit()
        self.db.refresh(incident)
        return incident

    def get_incidents_by_status(self, status: EmergencyStatus) -> List[EmergencyIncident]:
        """Get incidents by status"""
        return self.db.query(EmergencyIncident).filter(
            EmergencyIncident.status == status
        ).order_by(desc(EmergencyIncident.reported_at)).all()

    def get_recent_incidents(self, limit: int = 10) -> List[EmergencyIncident]:
        """Get recent incidents"""
        return self.db.query(EmergencyIncident).order_by(
            desc(EmergencyIncident.reported_at)
        ).limit(limit).all()

    def get_incidents_by_location(
        self, 
        latitude: float, 
        longitude: float, 
        radius_km: float = 5.0
    ) -> List[EmergencyIncident]:
        """Get incidents within a radius of a location"""
        # Simple bounding box calculation (for more accuracy, use PostGIS)
        lat_delta = radius_km / 111.0  # Approximate km per degree latitude
        lng_delta = radius_km / (111.0 * abs(latitude))  # Adjust for latitude
        
        return self.db.query(EmergencyIncident).filter(
            and_(
                EmergencyIncident.latitude.between(latitude - lat_delta, latitude + lat_delta),
                EmergencyIncident.longitude.between(longitude - lng_delta, longitude + lng_delta)
            )
        ).order_by(desc(EmergencyIncident.reported_at)).all()

    def get_incident_stats(self) -> Dict[str, Any]:
        """Get emergency incident statistics"""
        total_incidents = self.db.query(EmergencyIncident).count()
        
        # Incidents by type
        type_stats = self.db.query(
            EmergencyIncident.type,
            func.count(EmergencyIncident.id).label('count')
        ).group_by(EmergencyIncident.type).all()
        
        incidents_by_type = {str(stat.type): stat.count for stat in type_stats}
        
        # Incidents by status
        status_stats = self.db.query(
            EmergencyIncident.status,
            func.count(EmergencyIncident.id).label('count')
        ).group_by(EmergencyIncident.status).all()
        
        incidents_by_status = {str(stat.status): stat.count for stat in status_stats}
        
        # Active incidents
        active_incidents = self.db.query(EmergencyIncident).filter(
            EmergencyIncident.status.in_([
                EmergencyStatus.REPORTED,
                EmergencyStatus.ACKNOWLEDGED,
                EmergencyStatus.IN_PROGRESS
            ])
        ).count()
        
        # Resolved today
        today = datetime.utcnow().date()
        resolved_today = self.db.query(EmergencyIncident).filter(
            and_(
                EmergencyIncident.status.in_([EmergencyStatus.RESOLVED, EmergencyStatus.CLOSED]),
                func.date(EmergencyIncident.resolved_at) == today
            )
        ).count()
        
        return {
            'total_incidents': total_incidents,
            'incidents_by_type': incidents_by_type,
            'incidents_by_status': incidents_by_status,
            'active_incidents': active_incidents,
            'resolved_today': resolved_today
        }

class EmergencyBroadcastRepository(BaseRepository[EmergencyBroadcast]):
    def __init__(self, db: Session):
        super().__init__(EmergencyBroadcast, db)

    def create_broadcast(
        self, 
        broadcast_data: EmergencyBroadcastCreate, 
        admin_id: int
    ) -> EmergencyBroadcast:
        """Create a new emergency broadcast"""
        broadcast = EmergencyBroadcast(
            title=broadcast_data.title,
            message=broadcast_data.message,
            route_id=broadcast_data.route_id,
            stop_id=broadcast_data.stop_id,
            sent_by_admin_id=admin_id,
            send_sms=broadcast_data.send_sms,
            send_push=broadcast_data.send_push,
            send_whatsapp=broadcast_data.send_whatsapp
        )
        
        self.db.add(broadcast)
        self.db.commit()
        self.db.refresh(broadcast)
        return broadcast

    def update_delivery_stats(
        self, 
        broadcast_id: int, 
        total_recipients: int,
        successful_deliveries: int,
        failed_deliveries: int
    ) -> Optional[EmergencyBroadcast]:
        """Update broadcast delivery statistics"""
        broadcast = self.get_by_id(broadcast_id)
        if not broadcast:
            return None

        broadcast.total_recipients = total_recipients
        broadcast.successful_deliveries = successful_deliveries
        broadcast.failed_deliveries = failed_deliveries

        self.db.commit()
        self.db.refresh(broadcast)
        return broadcast

    def get_recent_broadcasts(self, limit: int = 10) -> List[EmergencyBroadcast]:
        """Get recent broadcasts"""
        return self.db.query(EmergencyBroadcast).order_by(
            desc(EmergencyBroadcast.sent_at)
        ).limit(limit).all()

class EmergencyContactRepository(BaseRepository[EmergencyContact]):
    def __init__(self, db: Session):
        super().__init__(EmergencyContact, db)

    def create_contact(self, contact_data: EmergencyContactCreate) -> EmergencyContact:
        """Create a new emergency contact"""
        contact = EmergencyContact(**contact_data.dict())
        
        self.db.add(contact)
        self.db.commit()
        self.db.refresh(contact)
        return contact

    def get_active_contacts(self) -> List[EmergencyContact]:
        """Get all active emergency contacts ordered by priority"""
        return self.db.query(EmergencyContact).filter(
            EmergencyContact.is_active == True
        ).order_by(EmergencyContact.priority, EmergencyContact.name).all()

    def get_contacts_by_type(self, contact_type: str) -> List[EmergencyContact]:
        """Get contacts by type"""
        return self.db.query(EmergencyContact).filter(
            and_(
                EmergencyContact.type == contact_type,
                EmergencyContact.is_active == True
            )
        ).order_by(EmergencyContact.priority).all()