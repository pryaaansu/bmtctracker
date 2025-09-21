from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class DriverStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ON_BREAK = "on_break"

class TripStatus(str, Enum):
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class IssueCategory(str, Enum):
    MECHANICAL = "mechanical"
    TRAFFIC = "traffic"
    PASSENGER = "passenger"
    ROUTE = "route"
    EMERGENCY = "emergency"
    OTHER = "other"

class IssuePriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

# Driver authentication schemas
class DriverLogin(BaseModel):
    phone: str = Field(..., description="Driver phone number")
    password: str = Field(..., description="Driver password")

class DriverLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    driver: "DriverProfile"

# Driver profile schemas
class DriverProfile(BaseModel):
    id: int
    name: str
    phone: str
    license_number: str
    status: DriverStatus
    assigned_vehicle_id: Optional[int] = None
    assigned_vehicle_number: Optional[str] = None
    current_route_id: Optional[int] = None
    current_route_name: Optional[str] = None

    class Config:
        from_attributes = True

# Trip management schemas
class TripBase(BaseModel):
    vehicle_id: int
    route_id: int
    driver_id: int

class TripCreate(TripBase):
    pass

class TripUpdate(BaseModel):
    status: Optional[TripStatus] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

class TripResponse(BaseModel):
    id: int
    vehicle_id: int
    route_id: int
    driver_id: int
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: TripStatus
    created_at: datetime
    
    # Related data
    vehicle_number: Optional[str] = None
    route_name: Optional[str] = None
    route_number: Optional[str] = None

    class Config:
        from_attributes = True

# Occupancy reporting schemas
class OccupancyLevel(str, Enum):
    EMPTY = "empty"          # 0-10%
    LOW = "low"              # 11-30%
    MEDIUM = "medium"        # 31-60%
    HIGH = "high"            # 61-85%
    FULL = "full"            # 86-100%

class OccupancyReport(BaseModel):
    vehicle_id: int
    occupancy_level: OccupancyLevel
    passenger_count: Optional[int] = None
    timestamp: Optional[datetime] = None

class OccupancyResponse(BaseModel):
    id: int
    vehicle_id: int
    occupancy_level: OccupancyLevel
    passenger_count: Optional[int] = None
    timestamp: datetime
    reported_by: int  # driver_id

    class Config:
        from_attributes = True

# Issue reporting schemas
class IssueReport(BaseModel):
    category: IssueCategory
    priority: IssuePriority
    title: str = Field(..., max_length=200)
    description: str = Field(..., max_length=1000)
    location_lat: Optional[float] = None
    location_lng: Optional[float] = None
    vehicle_id: Optional[int] = None
    route_id: Optional[int] = None

class IssueResponse(BaseModel):
    id: int
    category: IssueCategory
    priority: IssuePriority
    title: str
    description: str
    location_lat: Optional[float] = None
    location_lng: Optional[float] = None
    vehicle_id: Optional[int] = None
    route_id: Optional[int] = None
    reported_by: int  # driver_id
    status: str = "open"
    created_at: datetime
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Shift schedule schemas
class ShiftSchedule(BaseModel):
    id: int
    driver_id: int
    start_time: datetime
    end_time: datetime
    route_id: int
    vehicle_id: int
    status: str = "scheduled"
    
    # Related data
    route_name: Optional[str] = None
    route_number: Optional[str] = None
    vehicle_number: Optional[str] = None

    class Config:
        from_attributes = True

# Location ping schemas
class LocationPing(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    speed: Optional[float] = Field(None, ge=0)
    bearing: Optional[int] = Field(None, ge=0, le=360)
    accuracy: Optional[float] = None
    timestamp: Optional[datetime] = None

class LocationPingResponse(BaseModel):
    success: bool
    message: str
    recorded_at: datetime

# Dashboard data schemas
class DriverDashboard(BaseModel):
    driver: DriverProfile
    current_trip: Optional[TripResponse] = None
    upcoming_shifts: List[ShiftSchedule] = []
    recent_issues: List[IssueResponse] = []
    today_stats: dict = {}

# Communication schemas
class DispatchMessage(BaseModel):
    message: str = Field(..., max_length=500)
    priority: IssuePriority = IssuePriority.MEDIUM
    recipient_type: str = "dispatch"  # "dispatch" or "admin"

class MessageResponse(BaseModel):
    id: int
    message: str
    priority: IssuePriority
    sender_id: int
    sender_name: str
    recipient_type: str
    created_at: datetime
    read_at: Optional[datetime] = None

    class Config:
        from_attributes = True