from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, DateTime, func, Index
from sqlalchemy.orm import relationship
from ..core.database import Base

class Stop(Base):
    __tablename__ = "stops"

    id = Column(Integer, primary_key=True, index=True)
    route_id = Column(Integer, ForeignKey("routes.id"), nullable=False)
    name = Column(String(100), nullable=False)
    name_kannada = Column(String(100), nullable=True)
    latitude = Column(Numeric(10, 8), nullable=False)
    longitude = Column(Numeric(11, 8), nullable=False)
    stop_order = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    route = relationship("Route", back_populates="stops")
    subscriptions = relationship("Subscription", back_populates="stop")
    emergency_broadcasts = relationship("EmergencyBroadcast", back_populates="stop")

    # Indexes for geospatial queries
    __table_args__ = (
        Index('idx_location', 'latitude', 'longitude'),
        Index('idx_route_order', 'route_id', 'stop_order'),
    )