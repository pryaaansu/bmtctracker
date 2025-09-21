from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Enum, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum as PyEnum
from ..core.database import Base

class EmergencyType(PyEnum):
    MEDICAL = "medical"
    SAFETY = "safety"
    HARASSMENT = "harassment"
    ACCIDENT = "accident"
    OTHER = "other"

class EmergencyStatus(PyEnum):
    REPORTED = "reported"
    ACKNOWLEDGED = "acknowledged"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"

class EmergencyIncident(Base):
    __tablename__ = "emergency_incidents"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(Enum(EmergencyType), nullable=False)
    description = Column(Text)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    status = Column(Enum(EmergencyStatus), default=EmergencyStatus.REPORTED)
    
    # User information (if authenticated)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    phone_number = Column(String(15), nullable=True)
    
    # System information
    user_agent = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    
    # Timestamps
    reported_at = Column(DateTime(timezone=True), server_default=func.now())
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Admin handling
    assigned_admin_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    admin_notes = Column(Text, nullable=True)
    
    # Emergency response
    emergency_call_made = Column(Boolean, default=False)
    emergency_call_time = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="emergency_incidents")
    assigned_admin = relationship("User", foreign_keys=[assigned_admin_id])

class EmergencyBroadcast(Base):
    __tablename__ = "emergency_broadcasts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    
    # Targeting
    route_id = Column(Integer, ForeignKey("routes.id"), nullable=True)  # None for all users
    stop_id = Column(Integer, ForeignKey("stops.id"), nullable=True)   # None for all users
    
    # Broadcast details
    sent_by_admin_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Delivery tracking
    total_recipients = Column(Integer, default=0)
    successful_deliveries = Column(Integer, default=0)
    failed_deliveries = Column(Integer, default=0)
    
    # Channels
    send_sms = Column(Boolean, default=True)
    send_push = Column(Boolean, default=True)
    send_whatsapp = Column(Boolean, default=False)
    
    # Relationships
    route = relationship("Route", back_populates="emergency_broadcasts")
    stop = relationship("Stop", back_populates="emergency_broadcasts")
    sent_by = relationship("User", back_populates="emergency_broadcasts_sent")

class EmergencyContact(Base):
    __tablename__ = "emergency_contacts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    phone_number = Column(String(15), nullable=False)
    type = Column(String(50), nullable=False)  # police, ambulance, fire, helpline
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=1)  # 1 = highest priority
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())