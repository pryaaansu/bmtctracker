from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, func
from .base import BaseRepository
from ..models.audit_log import AuditLog, AdminRole, AdminRoleAssignment
from ..models.user import User, UserRole

class AuditLogRepository(BaseRepository[AuditLog]):
    """Repository for audit log operations"""
    
    def __init__(self, db: Session):
        super().__init__(AuditLog, db)
    
    def log_action(
        self,
        admin_id: int,
        action: str,
        resource_type: str,
        resource_id: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        """Log an admin action"""
        log_entry = AuditLog(
            admin_id=admin_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent
        )
        self.db.add(log_entry)
        self.db.commit()
        self.db.refresh(log_entry)
        return log_entry
    
    def get_logs_by_admin(
        self,
        admin_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> List[AuditLog]:
        """Get audit logs for a specific admin"""
        return (
            self.db.query(AuditLog)
            .filter(AuditLog.admin_id == admin_id)
            .order_by(desc(AuditLog.timestamp))
            .offset(offset)
            .limit(limit)
            .all()
        )
    
    def get_logs_by_resource(
        self,
        resource_type: str,
        resource_id: int,
        limit: int = 50
    ) -> List[AuditLog]:
        """Get audit logs for a specific resource"""
        return (
            self.db.query(AuditLog)
            .filter(
                and_(
                    AuditLog.resource_type == resource_type,
                    AuditLog.resource_id == resource_id
                )
            )
            .order_by(desc(AuditLog.timestamp))
            .limit(limit)
            .all()
        )
    
    def get_recent_logs(
        self,
        limit: int = 100,
        offset: int = 0,
        hours: int = 24
    ) -> List[AuditLog]:
        """Get recent audit logs"""
        since = datetime.utcnow() - timedelta(hours=hours)
        return (
            self.db.query(AuditLog)
            .filter(AuditLog.timestamp >= since)
            .order_by(desc(AuditLog.timestamp))
            .offset(offset)
            .limit(limit)
            .all()
        )
    
    def get_action_count(
        self,
        action: str,
        hours: int = 24
    ) -> int:
        """Get count of specific actions in the last N hours"""
        since = datetime.utcnow() - timedelta(hours=hours)
        return (
            self.db.query(AuditLog)
            .filter(
                and_(
                    AuditLog.action == action,
                    AuditLog.timestamp >= since
                )
            )
            .count()
        )

class AdminRoleRepository(BaseRepository[AdminRole]):
    """Repository for admin role operations"""
    
    def __init__(self, db: Session):
        super().__init__(AdminRole, db)
    
    def create_role(
        self,
        name: str,
        description: str,
        permissions: List[str]
    ) -> AdminRole:
        """Create a new admin role"""
        role = AdminRole(
            name=name,
            description=description,
            permissions=permissions
        )
        self.db.add(role)
        self.db.commit()
        self.db.refresh(role)
        return role
    
    def get_by_name(self, name: str) -> Optional[AdminRole]:
        """Get role by name"""
        return self.db.query(AdminRole).filter(AdminRole.name == name).first()
    
    def get_active_roles(self) -> List[AdminRole]:
        """Get all active roles"""
        return (
            self.db.query(AdminRole)
            .filter(AdminRole.is_active == True)
            .order_by(AdminRole.name)
            .all()
        )
    
    def update_permissions(
        self,
        role_id: int,
        permissions: List[str]
    ) -> Optional[AdminRole]:
        """Update role permissions"""
        role = self.get(role_id)
        if role:
            role.permissions = permissions
            self.db.commit()
            self.db.refresh(role)
        return role

class AdminRoleAssignmentRepository(BaseRepository[AdminRoleAssignment]):
    """Repository for admin role assignment operations"""
    
    def __init__(self, db: Session):
        super().__init__(AdminRoleAssignment, db)
    
    def assign_role(
        self,
        user_id: int,
        role_id: int,
        assigned_by: int
    ) -> AdminRoleAssignment:
        """Assign a role to a user"""
        # Deactivate existing assignments for this user
        existing = (
            self.db.query(AdminRoleAssignment)
            .filter(
                and_(
                    AdminRoleAssignment.user_id == user_id,
                    AdminRoleAssignment.is_active == True
                )
            )
            .all()
        )
        
        for assignment in existing:
            assignment.is_active = False
        
        # Create new assignment
        assignment = AdminRoleAssignment(
            user_id=user_id,
            role_id=role_id,
            assigned_by=assigned_by
        )
        self.db.add(assignment)
        self.db.commit()
        self.db.refresh(assignment)
        return assignment
    
    def get_user_roles(self, user_id: int) -> List[AdminRole]:
        """Get active roles for a user"""
        return (
            self.db.query(AdminRole)
            .join(AdminRoleAssignment)
            .filter(
                and_(
                    AdminRoleAssignment.user_id == user_id,
                    AdminRoleAssignment.is_active == True,
                    AdminRole.is_active == True
                )
            )
            .all()
        )
    
    def get_user_permissions(self, user_id: int) -> List[str]:
        """Get all permissions for a user"""
        roles = self.get_user_roles(user_id)
        permissions = set()
        for role in roles:
            permissions.update(role.permissions)
        return list(permissions)
    
    def revoke_role(self, user_id: int, role_id: int) -> bool:
        """Revoke a specific role from a user"""
        assignment = (
            self.db.query(AdminRoleAssignment)
            .filter(
                and_(
                    AdminRoleAssignment.user_id == user_id,
                    AdminRoleAssignment.role_id == role_id,
                    AdminRoleAssignment.is_active == True
                )
            )
            .first()
        )
        
        if assignment:
            assignment.is_active = False
            self.db.commit()
            return True
        return False

class AdminUserRepository:
    """Repository for admin user management operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Get dashboard statistics"""
        total_users = self.db.query(User).count()
        active_users = self.db.query(User).filter(User.is_active == True).count()
        total_drivers = self.db.query(User).filter(User.role == UserRole.DRIVER).count()
        active_drivers = (
            self.db.query(User)
            .filter(
                and_(
                    User.role == UserRole.DRIVER,
                    User.is_active == True
                )
            )
            .count()
        )
        total_admins = self.db.query(User).filter(User.role == UserRole.ADMIN).count()
        
        # Users created today
        today = datetime.utcnow().date()
        new_users_today = (
            self.db.query(User)
            .filter(func.date(User.created_at) == today)
            .count()
        )
        
        # Users created this week
        week_ago = datetime.utcnow() - timedelta(days=7)
        new_users_this_week = (
            self.db.query(User)
            .filter(User.created_at >= week_ago)
            .count()
        )
        
        # Calculate growth percentage (simplified)
        prev_week_start = week_ago - timedelta(days=7)
        prev_week_users = (
            self.db.query(User)
            .filter(
                and_(
                    User.created_at >= prev_week_start,
                    User.created_at < week_ago
                )
            )
            .count()
        )
        
        growth_percentage = 0.0
        if prev_week_users > 0:
            growth_percentage = ((new_users_this_week - prev_week_users) / prev_week_users) * 100
        
        return {
            "total_users": total_users,
            "active_users": active_users,
            "total_drivers": total_drivers,
            "active_drivers": active_drivers,
            "total_admins": total_admins,
            "new_users_today": new_users_today,
            "new_users_this_week": new_users_this_week,
            "user_growth_percentage": round(growth_percentage, 2)
        }
    
    def get_users_with_pagination(
        self,
        page: int = 1,
        per_page: int = 20,
        role: Optional[UserRole] = None,
        search: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> Dict[str, Any]:
        """Get users with pagination and filtering"""
        query = self.db.query(User)
        
        # Apply filters
        if role:
            query = query.filter(User.role == role)
        
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                User.email.ilike(search_term) |
                User.full_name.ilike(search_term) |
                User.phone.ilike(search_term)
            )
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * per_page
        users = query.order_by(desc(User.created_at)).offset(offset).limit(per_page).all()
        
        total_pages = (total + per_page - 1) // per_page
        
        return {
            "users": users,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages
        }
    
    def bulk_update_users(
        self,
        user_ids: List[int],
        action: str,
        admin_id: int
    ) -> Dict[str, Any]:
        """Perform bulk actions on users"""
        users = self.db.query(User).filter(User.id.in_(user_ids)).all()
        
        if not users:
            return {"success": False, "message": "No users found"}
        
        updated_count = 0
        
        for user in users:
            if action == "activate":
                user.is_active = True
                updated_count += 1
            elif action == "deactivate":
                # Don't allow deactivating the current admin
                if user.id != admin_id:
                    user.is_active = False
                    updated_count += 1
            elif action == "verify":
                user.is_verified = True
                updated_count += 1
        
        self.db.commit()
        
        return {
            "success": True,
            "message": f"Updated {updated_count} users",
            "updated_count": updated_count
        }