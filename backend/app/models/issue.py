from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, func, Enum, Text
from sqlalchemy.orm import relationship
from ..core.database import Base
import enum

class IssueCategory(str, enum.Enum):
    MECHANICAL = "mechanical"
    TRAFFIC = "traffic"
    PASSENGER = "passenger"
    ROUTE = "route"
    EMERGENCY = "emergency"
    OTHER = "other"

class IssuePriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class IssueStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"

class Issue(Base):
    __tablename__ = "issues"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(Enum(IssueCategory), nullable=False)
    priority = Column(Enum(IssuePriority), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    location_lat = Column(Float, nullable=True)
    location_lng = Column(Float, nullable=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=True)
    route_id = Column(Integer, ForeignKey("routes.id"), nullable=True)
    reported_by = Column(Integer, ForeignKey("drivers.id"), nullable=False)
    status = Column(Enum(IssueStatus), default=IssueStatus.OPEN)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(Integer, ForeignKey("drivers.id"), nullable=True)

    # Relationships
    vehicle = relationship("Vehicle")
    route = relationship("Route")
    reporter = relationship("Driver", foreign_keys=[reported_by])
    resolver = relationship("Driver", foreign_keys=[resolved_by])