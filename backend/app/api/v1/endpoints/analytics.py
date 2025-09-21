from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import date, datetime, timedelta
from pydantic import BaseModel

from ....core.database import get_db
from ....core.auth import get_current_user
from ....models.user import User
from ....services.analytics_service import AnalyticsService

router = APIRouter()

# Pydantic models for request/response
class TripHistoryResponse(BaseModel):
    trip_id: int
    route_number: str
    route_name: str
    vehicle_number: str
    start_time: datetime
    end_time: datetime
    duration_minutes: float
    delay_minutes: float
    on_time_percentage: float
    distance_km: float
    average_speed_kmh: float
    total_passengers: int
    peak_occupancy: float
    co2_saved_kg: float
    stops_completed: int
    stops_skipped: int

class PerformanceMetricsResponse(BaseModel):
    total_trips: int
    on_time_percentage: float
    average_delay_minutes: float
    reliability_score: float
    total_passengers: int
    average_occupancy: float
    total_co2_saved_kg: float

class RidershipEstimationResponse(BaseModel):
    total_passengers: int
    average_daily_passengers: float
    peak_hour_occupancy: float
    growth_trend: float
    daily_patterns: Dict[str, int]
    hourly_occupancy: Dict[str, float]

class CarbonFootprintResponse(BaseModel):
    total_co2_saved_kg: float
    total_distance_km: float
    total_passengers: int
    equivalent_cars_off_road: float
    co2_saved_per_passenger_kg: float
    co2_saved_per_km_kg: float

class DemandPredictionResponse(BaseModel):
    route_id: int
    prediction_date: date
    predicted_demand: float
    confidence_score: float
    historical_average: float
    trend_percentage: float
    factors: List[str]

class DelayPredictionResponse(BaseModel):
    route_id: int
    prediction_date: date
    time_of_day: str
    predicted_delay_minutes: float
    confidence_interval_lower: float
    confidence_interval_upper: float
    confidence_score: float
    factors: List[str]

@router.get("/trip-history", response_model=List[TripHistoryResponse])
def get_trip_history(
    route_id: Optional[int] = Query(None, description="Filter by route ID"),
    vehicle_id: Optional[int] = Query(None, description="Filter by vehicle ID"),
    start_date: Optional[date] = Query(None, description="Start date for filtering"),
    end_date: Optional[date] = Query(None, description="End date for filtering"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get trip history with performance analytics
    
    Returns detailed trip history including performance metrics, ridership data,
    and environmental impact for completed trips.
    """
    analytics_service = AnalyticsService(db)
    
    try:
        trip_history = analytics_service.get_trip_history(
            route_id=route_id,
            vehicle_id=vehicle_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
        
        return trip_history
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving trip history: {str(e)}")

@router.get("/performance-metrics", response_model=PerformanceMetricsResponse)
def get_performance_metrics(
    route_id: Optional[int] = Query(None, description="Filter by route ID"),
    start_date: Optional[date] = Query(None, description="Start date for filtering"),
    end_date: Optional[date] = Query(None, description="End date for filtering"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get performance metrics for trips
    
    Returns aggregated performance metrics including on-time percentage,
    average delays, reliability scores, and ridership data.
    """
    analytics_service = AnalyticsService(db)
    
    try:
        metrics = analytics_service.get_performance_metrics(
            route_id=route_id,
            start_date=start_date,
            end_date=end_date
        )
        
        return PerformanceMetricsResponse(**metrics)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating performance metrics: {str(e)}")

@router.get("/ridership-estimation", response_model=RidershipEstimationResponse)
def get_ridership_estimation(
    route_id: Optional[int] = Query(None, description="Filter by route ID"),
    start_date: Optional[date] = Query(None, description="Start date for filtering"),
    end_date: Optional[date] = Query(None, description="End date for filtering"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get ridership estimation and patterns
    
    Returns ridership patterns, trends, and passenger flow analysis
    for better service planning and optimization.
    """
    analytics_service = AnalyticsService(db)
    
    try:
        ridership_data = analytics_service.get_ridership_estimation(
            route_id=route_id,
            start_date=start_date,
            end_date=end_date
        )
        
        return RidershipEstimationResponse(**ridership_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating ridership estimation: {str(e)}")

@router.get("/carbon-footprint", response_model=CarbonFootprintResponse)
def get_carbon_footprint(
    route_id: Optional[int] = Query(None, description="Filter by route ID"),
    start_date: Optional[date] = Query(None, description="Start date for filtering"),
    end_date: Optional[date] = Query(None, description="End date for filtering"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get carbon footprint and environmental impact analysis
    
    Returns environmental impact metrics including CO2 savings,
    equivalent cars off road, and sustainability indicators.
    """
    analytics_service = AnalyticsService(db)
    
    try:
        carbon_data = analytics_service.calculate_carbon_footprint(
            route_id=route_id,
            start_date=start_date,
            end_date=end_date
        )
        
        return CarbonFootprintResponse(**carbon_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating carbon footprint: {str(e)}")

@router.post("/demand-prediction", response_model=DemandPredictionResponse)
def generate_demand_prediction(
    route_id: int = Query(..., description="Route ID for prediction"),
    prediction_date: date = Query(..., description="Date for prediction"),
    days_ahead: int = Query(7, ge=1, le=30, description="Days ahead to look for historical data"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate demand prediction for a route
    
    Uses historical data and machine learning to predict passenger demand
    for better resource allocation and service planning.
    """
    analytics_service = AnalyticsService(db)
    
    try:
        prediction = analytics_service.generate_demand_prediction(
            route_id=route_id,
            prediction_date=prediction_date,
            days_ahead=days_ahead
        )
        
        return DemandPredictionResponse(**prediction)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating demand prediction: {str(e)}")

@router.post("/delay-prediction", response_model=DelayPredictionResponse)
def generate_delay_prediction(
    route_id: int = Query(..., description="Route ID for prediction"),
    prediction_date: date = Query(..., description="Date for prediction"),
    time_of_day: str = Query("morning", description="Time of day: morning, afternoon, evening"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate delay prediction for a route
    
    Predicts potential delays based on historical patterns, traffic conditions,
    and other factors to help with service reliability planning.
    """
    if time_of_day not in ["morning", "afternoon", "evening"]:
        raise HTTPException(status_code=400, detail="time_of_day must be one of: morning, afternoon, evening")
    
    analytics_service = AnalyticsService(db)
    
    try:
        prediction = analytics_service.generate_delay_prediction(
            route_id=route_id,
            prediction_date=prediction_date,
            time_of_day=time_of_day
        )
        
        return DelayPredictionResponse(**prediction)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating delay prediction: {str(e)}")

@router.get("/dashboard-summary")
def get_dashboard_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive dashboard summary
    
    Returns a complete overview of system performance, ridership,
    environmental impact, and key metrics for the analytics dashboard.
    """
    analytics_service = AnalyticsService(db)
    
    try:
        # Get system-wide metrics for the last 30 days
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
        
        performance_metrics = analytics_service.get_performance_metrics(
            start_date=start_date,
            end_date=end_date
        )
        
        ridership_data = analytics_service.get_ridership_estimation(
            start_date=start_date,
            end_date=end_date
        )
        
        carbon_data = analytics_service.calculate_carbon_footprint(
            start_date=start_date,
            end_date=end_date
        )
        
        # Get recent trip history for trends
        recent_trips = analytics_service.get_trip_history(
            start_date=start_date,
            end_date=end_date,
            limit=50
        )
        
        # Calculate trends
        if len(recent_trips) > 1:
            recent_week = [t for t in recent_trips if (end_date - t['start_time'].date()).days <= 7]
            previous_week = [t for t in recent_trips if 7 < (end_date - t['start_time'].date()).days <= 14]
            
            if recent_week and previous_week:
                recent_avg_delay = sum(t['delay_minutes'] for t in recent_week) / len(recent_week)
                previous_avg_delay = sum(t['delay_minutes'] for t in previous_week) / len(previous_week)
                delay_trend = ((recent_avg_delay - previous_avg_delay) / previous_avg_delay * 100) if previous_avg_delay > 0 else 0
            else:
                delay_trend = 0
        else:
            delay_trend = 0
        
        return {
            "performance": performance_metrics,
            "ridership": ridership_data,
            "environmental": carbon_data,
            "trends": {
                "delay_trend_percentage": round(delay_trend, 2),
                "recent_trips_count": len(recent_trips),
                "data_period_days": 30
            },
            "last_updated": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating dashboard summary: {str(e)}")

@router.post("/calculate-trip-analytics/{trip_id}")
def calculate_trip_analytics(
    trip_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Calculate analytics for a specific completed trip
    
    Manually trigger analytics calculation for a trip that has been completed.
    This is useful for ensuring all trip data is properly analyzed.
    """
    analytics_service = AnalyticsService(db)
    
    try:
        analytics = analytics_service.calculate_trip_analytics(trip_id)
        
        if not analytics:
            raise HTTPException(status_code=404, detail="Trip not found or not completed")
        
        return {
            "trip_id": trip_id,
            "analytics_calculated": True,
            "delay_minutes": analytics.delay_minutes,
            "on_time_percentage": analytics.on_time_percentage,
            "total_passengers": analytics.total_passengers,
            "co2_saved_kg": analytics.co2_saved_kg,
            "message": "Trip analytics calculated successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating trip analytics: {str(e)}")

