from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base

class AuditLog(Base):
    """Audit log for tracking admin actions"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String(100), nullable=False)  # e.g., "create_user", "update_route", "delete_bus"
    resource_type = Column(String(50), nullable=False)  # e.g., "user", "route", "bus"
    resource_id = Column(Integer, nullable=True)  # ID of the affected resource
    details = Column(JSON, nullable=True)  # Additional details about the action
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6
    user_agent = Column(Text, nullable=True)
    timestamp = Column(DateTime, server_default=func.now(), nullable=False)
    
    # Relationships
    admin = relationship("User", foreign_keys=[admin_id])
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, admin_id={self.admin_id}, action='{self.action}', resource='{self.resource_type}:{self.resource_id}')>"

class AdminRole(Base):
    """Admin roles with different permission levels"""
    __tablename__ = "admin_roles"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(200), nullable=True)
    permissions = Column(JSON, nullable=False)  # List of permission strings
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<AdminRole(id={self.id}, name='{self.name}')>"

class AdminRoleAssignment(Base):
    """Assignment of roles to admin users"""
    __tablename__ = "admin_role_assignments"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role_id = Column(Integer, ForeignKey("admin_roles.id"), nullable=False)
    assigned_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    assigned_at = Column(DateTime, server_default=func.now(), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    role = relationship("AdminRole", foreign_keys=[role_id])
    assigned_by_user = relationship("User", foreign_keys=[assigned_by])
    
    def __repr__(self):
        return f"<AdminRoleAssignment(user_id={self.user_id}, role_id={self.role_id})>"