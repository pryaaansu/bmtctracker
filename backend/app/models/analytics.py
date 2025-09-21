from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, func, Text, JSON
from sqlalchemy.orm import relationship
from ..core.database import Base
from datetime import datetime
from typing import Dict, Any

class TripAnalytics(Base):
    """Analytics data for completed trips"""
    __tablename__ = "trip_analytics"

    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id"), nullable=False, unique=True)
    
    # Performance metrics
    scheduled_duration_minutes = Column(Float, nullable=True)  # Expected trip duration
    actual_duration_minutes = Column(Float, nullable=True)     # Actual trip duration
    delay_minutes = Column(Float, default=0.0)                # Delay in minutes
    on_time_percentage = Column(Float, nullable=True)          # On-time performance
    
    # Distance and efficiency
    total_distance_km = Column(Float, nullable=True)
    average_speed_kmh = Column(Float, nullable=True)
    fuel_efficiency_estimate = Column(Float, nullable=True)    # km per liter estimate
    
    # Ridership data
    total_passengers = Column(Integer, default=0)
    peak_occupancy_percentage = Column(Float, default=0.0)
    average_occupancy_percentage = Column(Float, default=0.0)
    
    # Environmental impact
    co2_saved_kg = Column(Float, default=0.0)                 # CO2 saved vs private vehicles
    
    # Route performance
    stops_completed = Column(Integer, default=0)
    stops_skipped = Column(Integer, default=0)
    
    # Additional metadata
    weather_conditions = Column(String(50), nullable=True)
    traffic_conditions = Column(String(50), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    trip = relationship("Trip")

class RoutePerformance(Base):
    """Aggregated performance metrics for routes"""
    __tablename__ = "route_performance"

    id = Column(Integer, primary_key=True, index=True)
    route_id = Column(Integer, ForeignKey("routes.id"), nullable=False)
    date = Column(DateTime(timezone=True), nullable=False)
    
    # Daily aggregated metrics
    total_trips = Column(Integer, default=0)
    completed_trips = Column(Integer, default=0)
    cancelled_trips = Column(Integer, default=0)
    
    # Performance metrics
    average_delay_minutes = Column(Float, default=0.0)
    on_time_percentage = Column(Float, default=0.0)
    reliability_score = Column(Float, default=0.0)           # Overall reliability (0-100)
    
    # Ridership metrics
    total_passengers = Column(Integer, default=0)
    average_occupancy = Column(Float, default=0.0)
    peak_hour_occupancy = Column(Float, default=0.0)
    
    # Environmental impact
    total_co2_saved_kg = Column(Float, default=0.0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    route = relationship("Route")

class SystemMetrics(Base):
    """System-wide performance metrics"""
    __tablename__ = "system_metrics"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime(timezone=True), nullable=False)
    
    # Fleet metrics
    total_vehicles = Column(Integer, default=0)
    active_vehicles = Column(Integer, default=0)
    vehicles_in_maintenance = Column(Integer, default=0)
    
    # Service metrics
    total_routes = Column(Integer, default=0)
    active_routes = Column(Integer, default=0)
    total_trips_scheduled = Column(Integer, default=0)
    total_trips_completed = Column(Integer, default=0)
    
    # Performance metrics
    system_on_time_percentage = Column(Float, default=0.0)
    average_delay_minutes = Column(Float, default=0.0)
    service_reliability = Column(Float, default=0.0)
    
    # Ridership metrics
    total_passengers = Column(Integer, default=0)
    average_system_occupancy = Column(Float, default=0.0)
    
    # Environmental impact
    total_co2_saved_kg = Column(Float, default=0.0)
    equivalent_cars_off_road = Column(Integer, default=0)
    
    # Additional metrics
    fuel_consumption_estimate = Column(Float, default=0.0)
    cost_per_passenger = Column(Float, default=0.0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class PredictiveAnalytics(Base):
    """Predictive analytics and forecasting data"""
    __tablename__ = "predictive_analytics"

    id = Column(Integer, primary_key=True, index=True)
    route_id = Column(Integer, ForeignKey("routes.id"), nullable=True)
    prediction_type = Column(String(50), nullable=False)  # 'demand', 'delay', 'occupancy'
    prediction_date = Column(DateTime(timezone=True), nullable=False)
    
    # Prediction data
    predicted_value = Column(Float, nullable=False)
    confidence_interval_lower = Column(Float, nullable=True)
    confidence_interval_upper = Column(Float, nullable=True)
    confidence_score = Column(Float, default=0.0)  # 0-1 confidence score
    
    # Model metadata
    model_version = Column(String(50), nullable=True)
    features_used = Column(JSON, nullable=True)  # JSON array of feature names
    
    # Actual vs predicted (for model evaluation)
    actual_value = Column(Float, nullable=True)
    prediction_error = Column(Float, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    route = relationship("Route")