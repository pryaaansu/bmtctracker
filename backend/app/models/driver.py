from sqlalchemy import Column, Integer, String, Enum, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from ..core.database import Base
import enum

class DriverStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ON_BREAK = "on_break"

class Driver(Base):
    __tablename__ = "drivers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    phone = Column(String(15), unique=True, nullable=False, index=True)
    license_number = Column(String(50), unique=True, nullable=False)
    assigned_vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=True)
    status = Column(Enum(DriverStatus), default=DriverStatus.ACTIVE)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    assigned_vehicle = relationship("Vehicle", back_populates="assigned_driver")
    trips = relationship("Trip", back_populates="driver")