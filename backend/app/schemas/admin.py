from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, EmailStr
from ..models.user import UserRole

class AdminUserCreate(BaseModel):
    """Schema for creating users by admin"""
    email: EmailStr
    phone: Optional[str] = Field(None, pattern=r'^\+?[1-9]\d{1,14}$')
    full_name: Optional[str] = Field(None, max_length=100)
    password: str = Field(..., min_length=8)
    role: UserRole = UserRole.PASSENGER
    is_active: bool = True
    is_verified: bool = False

class AdminUserUpdate(BaseModel):
    """Schema for updating users by admin"""
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, pattern=r'^\+?[1-9]\d{1,14}$')
    full_name: Optional[str] = Field(None, max_length=100)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None

class AdminUserResponse(BaseModel):
    """Enhanced user response for admin views"""
    id: int
    email: str
    phone: Optional[str]
    full_name: Optional[str]
    role: UserRole
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class UserListResponse(BaseModel):
    """Response for user list with pagination"""
    users: List[AdminUserResponse]
    total: int
    page: int
    per_page: int
    total_pages: int

class RoleChangeRequest(BaseModel):
    """Schema for changing user role"""
    user_id: int
    new_role: UserRole
    reason: Optional[str] = Field(None, max_length=500)

class BulkUserAction(BaseModel):
    """Schema for bulk user actions"""
    user_ids: List[int]
    action: str = Field(..., pattern=r'^(activate|deactivate|delete|verify)$')
    reason: Optional[str] = Field(None, max_length=500)

class AdminDashboardStats(BaseModel):
    """Admin dashboard statistics"""
    total_users: int
    active_users: int
    total_drivers: int
    active_drivers: int
    total_admins: int
    new_users_today: int
    new_users_this_week: int
    user_growth_percentage: float

class SystemHealth(BaseModel):
    """System health metrics"""
    database_status: str
    redis_status: str
    websocket_connections: int
    active_buses: int
    api_response_time: float
    error_rate: float
    uptime: str

class AuditLogEntry(BaseModel):
    """Audit log entry"""
    id: int
    admin_id: int
    admin_email: str
    action: str
    resource_type: str
    resource_id: Optional[int]
    details: Dict[str, Any]
    ip_address: Optional[str]
    user_agent: Optional[str]
    timestamp: datetime
    
    class Config:
        from_attributes = True

class AuditLogResponse(BaseModel):
    """Response for audit log with pagination"""
    logs: List[AuditLogEntry]
    total: int
    page: int
    per_page: int
    total_pages: int

class AdminPermission(BaseModel):
    """Admin permission definition"""
    name: str
    description: str
    category: str

class AdminRole(BaseModel):
    """Admin role with permissions"""
    id: int
    name: str
    description: str
    permissions: List[AdminPermission]
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class AdminRoleCreate(BaseModel):
    """Schema for creating admin roles"""
    name: str = Field(..., max_length=50)
    description: str = Field(..., max_length=200)
    permissions: List[str]

class AdminRoleUpdate(BaseModel):
    """Schema for updating admin roles"""
    name: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = Field(None, max_length=200)
    permissions: Optional[List[str]] = None
    is_active: Optional[bool] = None

# Route Management Schemas
class RouteStopCreate(BaseModel):
    """Schema for creating a stop within a route"""
    name: str = Field(..., max_length=100)
    name_kannada: Optional[str] = Field(None, max_length=100)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    stop_order: int = Field(..., ge=0)

class RouteStopUpdate(BaseModel):
    """Schema for updating a stop within a route"""
    name: Optional[str] = Field(None, max_length=100)
    name_kannada: Optional[str] = Field(None, max_length=100)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    stop_order: Optional[int] = Field(None, ge=0)

class RouteCreateRequest(BaseModel):
    """Schema for creating a new route with stops"""
    name: str = Field(..., max_length=100)
    route_number: str = Field(..., max_length=20)
    geojson: str
    polyline: str
    stops: List[RouteStopCreate] = []
    is_active: bool = True

class RouteUpdateRequest(BaseModel):
    """Schema for updating an existing route"""
    name: Optional[str] = Field(None, max_length=100)
    route_number: Optional[str] = Field(None, max_length=20)
    geojson: Optional[str] = None
    polyline: Optional[str] = None
    is_active: Optional[bool] = None

class RouteStopReorderRequest(BaseModel):
    """Schema for reordering stops in a route"""
    stop_orders: List[Dict[str, int]] = Field(..., description="List of {stop_id: new_order}")

class RouteValidationResult(BaseModel):
    """Schema for route validation results"""
    is_valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    conflicts: List[Dict[str, Any]] = []

class BulkRouteImport(BaseModel):
    """Schema for bulk route import"""
    format: str = Field(..., pattern=r'^(csv|geojson)$')
    data: str
    validate_only: bool = False
    overwrite_existing: bool = False

class BulkRouteExport(BaseModel):
    """Schema for bulk route export"""
    format: str = Field(..., pattern=r'^(csv|geojson|json)$')
    route_ids: Optional[List[int]] = None
    include_stops: bool = True
    include_inactive: bool = False