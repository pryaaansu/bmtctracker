from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, func, Enum
from sqlalchemy.orm import relationship
from ..core.database import Base
import enum

class OccupancyLevel(str, enum.Enum):
    EMPTY = "empty"          # 0-10%
    LOW = "low"              # 11-30%
    MEDIUM = "medium"        # 31-60%
    HIGH = "high"            # 61-85%
    FULL = "full"            # 86-100%

class OccupancyReport(Base):
    __tablename__ = "occupancy_reports"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False)
    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=False)
    occupancy_level = Column(Enum(OccupancyLevel), nullable=False)
    passenger_count = Column(Integer, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    vehicle = relationship("Vehicle")
    driver = relationship("Driver")