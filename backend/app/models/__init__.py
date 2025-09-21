from .vehicle import Vehicle
from .driver import Driver
from .route import Route
from .stop import Stop
from .trip import Trip
from .location import VehicleLocation
from .subscription import Subscription
from .notification import Notification
from .user import User, UserRole
from .emergency import EmergencyIncident, EmergencyBroadcast, EmergencyContact, EmergencyType, EmergencyStatus
from .occupancy import OccupancyReport, OccupancyLevel
from .issue import Issue, IssueCategory, IssuePriority, IssueStatus
from .shift_schedule import ShiftSchedule, ShiftStatus
from .audit_log import AuditLog, AdminRole, AdminRoleAssignment
from ..core.database import Base

# Import all models to ensure they are registered with SQLAlchemy
__all__ = [
    "Base",
    "Vehicle",
    "Driver", 
    "Route",
    "Stop",
    "Trip",
    "VehicleLocation",
    "Subscription",
    "Notification",
    "User",
    "UserRole",
    "EmergencyIncident",
    "EmergencyBroadcast", 
    "EmergencyContact",
    "EmergencyType",
    "EmergencyStatus",
    "OccupancyReport",
    "OccupancyLevel",
    "Issue",
    "IssueCategory",
    "IssuePriority", 
    "IssueStatus",
    "ShiftSchedule",
    "ShiftStatus",
    "AuditLog",
    "AdminRole",
    "AdminRoleAssignment"
]