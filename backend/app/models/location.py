from sqlalchemy import Column, Integer, ForeignKey, Numeric, DateTime, func, Index
from sqlalchemy.orm import relationship
from ..core.database import Base

class VehicleLocation(Base):
    __tablename__ = "vehicle_locations"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False)
    latitude = Column(Numeric(10, 8), nullable=False)
    longitude = Column(Numeric(11, 8), nullable=False)
    speed = Column(Numeric(5, 2), default=0)  # km/h
    bearing = Column(Integer, default=0)  # degrees
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    vehicle = relationship("Vehicle", back_populates="locations")

    # Indexes for efficient queries
    __table_args__ = (
        Index('idx_vehicle_time', 'vehicle_id', 'recorded_at'),
        Index('idx_location', 'latitude', 'longitude'),
    )