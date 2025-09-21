from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from ..models.emergency import EmergencyType, EmergencyStatus

class EmergencyReportCreate(BaseModel):
    type: EmergencyType
    description: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    phone_number: Optional[str] = None
    user_agent: Optional[str] = None

    @validator('latitude')
    def validate_latitude(cls, v):
        if v is not None and not (-90 <= v <= 90):
            raise ValueError('Latitude must be between -90 and 90')
        return v

    @validator('longitude')
    def validate_longitude(cls, v):
        if v is not None and not (-180 <= v <= 180):
            raise ValueError('Longitude must be between -180 and 180')
        return v

class EmergencyIncidentResponse(BaseModel):
    id: int
    type: EmergencyType
    description: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    status: EmergencyStatus
    user_id: Optional[int]
    phone_number: Optional[str]
    reported_at: datetime
    acknowledged_at: Optional[datetime]
    resolved_at: Optional[datetime]
    assigned_admin_id: Optional[int]
    admin_notes: Optional[str]
    emergency_call_made: bool
    emergency_call_time: Optional[datetime]

    class Config:
        from_attributes = True

class EmergencyIncidentUpdate(BaseModel):
    status: Optional[EmergencyStatus] = None
    admin_notes: Optional[str] = None
    assigned_admin_id: Optional[int] = None

class EmergencyBroadcastCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1)
    route_id: Optional[int] = None
    stop_id: Optional[int] = None
    send_sms: bool = True
    send_push: bool = True
    send_whatsapp: bool = False

    @validator('route_id', 'stop_id')
    def validate_targeting(cls, v, values):
        # Can't target both route and stop
        if 'route_id' in values and values['route_id'] and v:
            raise ValueError('Cannot target both route and stop')
        return v

class EmergencyBroadcastResponse(BaseModel):
    id: int
    title: str
    message: str
    route_id: Optional[int]
    stop_id: Optional[int]
    sent_by_admin_id: int
    sent_at: datetime
    total_recipients: int
    successful_deliveries: int
    failed_deliveries: int
    send_sms: bool
    send_push: bool
    send_whatsapp: bool

    class Config:
        from_attributes = True

class EmergencyContactResponse(BaseModel):
    id: int
    name: str
    phone_number: str
    type: str
    is_active: bool
    priority: int

    class Config:
        from_attributes = True

class EmergencyContactCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    phone_number: str = Field(..., pattern=r'^\+?[1-9]\d{1,14}$')
    type: str = Field(..., min_length=1, max_length=50)
    is_active: bool = True
    priority: int = Field(default=1, ge=1, le=10)

class EmergencyStatsResponse(BaseModel):
    total_incidents: int
    incidents_by_type: dict
    incidents_by_status: dict
    recent_incidents: List[EmergencyIncidentResponse]
    active_incidents: int
    resolved_today: int

class EmergencyDashboardResponse(BaseModel):
    stats: EmergencyStatsResponse
    recent_broadcasts: List[EmergencyBroadcastResponse]
    emergency_contacts: List[EmergencyContactResponse]