"""
Repository factory for dependency injection
"""
from sqlalchemy.orm import Session

from .vehicle import VehicleRepository
from .route import RouteRepository
from .stop import StopRepository
from .subscription import SubscriptionRepository
from .location import VehicleLocationRepository
from .user import UserRepository
from .audit_log import AuditLogRepository, AdminRoleRepository, AdminRoleAssignmentRepository, AdminUserRepository

class RepositoryFactory:
    """Factory class to create repository instances"""
    
    def __init__(self, db: Session):
        self.db = db
        self._vehicle_repo = None
        self._route_repo = None
        self._stop_repo = None
        self._subscription_repo = None
        self._location_repo = None
        self._user_repo = None
        self._audit_log_repo = None
        self._admin_role_repo = None
        self._admin_role_assignment_repo = None
        self._admin_user_repo = None
    
    @property
    def vehicle(self) -> VehicleRepository:
        """Get vehicle repository instance"""
        if self._vehicle_repo is None:
            self._vehicle_repo = VehicleRepository(self.db)
        return self._vehicle_repo
    
    @property
    def route(self) -> RouteRepository:
        """Get route repository instance"""
        if self._route_repo is None:
            self._route_repo = RouteRepository(self.db)
        return self._route_repo
    
    @property
    def stop(self) -> StopRepository:
        """Get stop repository instance"""
        if self._stop_repo is None:
            self._stop_repo = StopRepository(self.db)
        return self._stop_repo
    
    @property
    def subscription(self) -> SubscriptionRepository:
        """Get subscription repository instance"""
        if self._subscription_repo is None:
            self._subscription_repo = SubscriptionRepository(self.db)
        return self._subscription_repo
    
    @property
    def location(self) -> VehicleLocationRepository:
        """Get location repository instance"""
        if self._location_repo is None:
            self._location_repo = VehicleLocationRepository(self.db)
        return self._location_repo
    
    @property
    def user(self) -> UserRepository:
        """Get user repository instance"""
        if self._user_repo is None:
            self._user_repo = UserRepository(self.db)
        return self._user_repo
    
    @property
    def audit_log(self) -> AuditLogRepository:
        """Get audit log repository instance"""
        if self._audit_log_repo is None:
            self._audit_log_repo = AuditLogRepository(self.db)
        return self._audit_log_repo
    
    @property
    def admin_role(self) -> AdminRoleRepository:
        """Get admin role repository instance"""
        if self._admin_role_repo is None:
            self._admin_role_repo = AdminRoleRepository(self.db)
        return self._admin_role_repo
    
    @property
    def admin_role_assignment(self) -> AdminRoleAssignmentRepository:
        """Get admin role assignment repository instance"""
        if self._admin_role_assignment_repo is None:
            self._admin_role_assignment_repo = AdminRoleAssignmentRepository(self.db)
        return self._admin_role_assignment_repo
    
    @property
    def admin_user(self) -> AdminUserRepository:
        """Get admin user repository instance"""
        if self._admin_user_repo is None:
            self._admin_user_repo = AdminUserRepository(self.db)
        return self._admin_user_repo

# Dependency function for FastAPI
def get_repositories(db: Session) -> RepositoryFactory:
    """Get repository factory instance"""
    return RepositoryFactory(db)