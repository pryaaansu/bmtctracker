from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, func
from sqlalchemy.orm import relationship
from ..core.database import Base

class Route(Base):
    __tablename__ = "routes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    route_number = Column(String(20), unique=True, nullable=False, index=True)
    geojson = Column(Text, nullable=False)  # GeoJSON representation
    polyline = Column(Text, nullable=False)  # Encoded polyline for maps
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    stops = relationship("Stop", back_populates="route", cascade="all, delete-orphan")
    trips = relationship("Trip", back_populates="route")
    emergency_broadcasts = relationship("EmergencyBroadcast", back_populates="route")