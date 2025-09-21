from sqlalchemy import Column, Integer, String, ForeignKey, Enum, Boolean, DateTime, func, Index
from sqlalchemy.orm import relationship
from ..core.database import Base
import enum

class NotificationChannel(str, enum.Enum):
    SMS = "sms"
    VOICE = "voice"
    WHATSAPP = "whatsapp"
    PUSH = "push"

class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String(15), nullable=False)
    stop_id = Column(Integer, ForeignKey("stops.id"), nullable=False)
    channel = Column(Enum(NotificationChannel), nullable=False)
    eta_threshold = Column(Integer, default=5)  # minutes
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    stop = relationship("Stop", back_populates="subscriptions")
    notifications = relationship("Notification", back_populates="subscription")

    # Indexes for efficient queries
    __table_args__ = (
        Index('idx_phone', 'phone'),
        Index('idx_stop', 'stop_id'),
        Index('idx_active', 'is_active'),
    )