from sqlalchemy import Column, Integer, String, Enum, DateTime, func
from sqlalchemy.orm import relationship
from ..core.database import Base
import enum

class VehicleStatus(str, enum.Enum):
    ACTIVE = "active"
    MAINTENANCE = "maintenance"
    OFFLINE = "offline"

class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_number = Column(String(20), unique=True, nullable=False, index=True)
    capacity = Column(Integer, nullable=False)
    status = Column(Enum(VehicleStatus), default=VehicleStatus.ACTIVE)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    trips = relationship("Trip", back_populates="vehicle")
    locations = relationship("VehicleLocation", back_populates="vehicle")
    assigned_driver = relationship("Driver", back_populates="assigned_vehicle")