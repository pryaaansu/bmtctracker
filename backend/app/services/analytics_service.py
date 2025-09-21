from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc, asc
from datetime import datetime, timedelta, date
from typing import List, Dict, Any, Optional, Tuple
import math
import json

from ..models.analytics import (
    TripAnalytics, RoutePerformance, SystemMetrics, PredictiveAnalytics
)
from ..models.trip import Trip, TripStatus
from ..models.vehicle import Vehicle
from ..models.route import Route
from ..models.occupancy import OccupancyReport
from ..models.location import VehicleLocation


class AnalyticsService:
    """Service for analytics calculations and reporting"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # Trip History and Performance Analytics
    
    def calculate_trip_analytics(self, trip_id: int) -> Optional[TripAnalytics]:
        """Calculate analytics for a completed trip"""
        trip = self.db.query(Trip).filter(Trip.id == trip_id).first()
        if not trip or trip.status != TripStatus.COMPLETED:
            return None
        
        # Get trip locations for distance calculation
        locations = self.db.query(VehicleLocation).filter(
            VehicleLocation.vehicle_id == trip.vehicle_id,
            VehicleLocation.recorded_at >= trip.start_time,
            VehicleLocation.recorded_at <= trip.end_time
        ).order_by(VehicleLocation.recorded_at).all()
        
        # Calculate basic metrics
        actual_duration = (trip.end_time - trip.start_time).total_seconds() / 60
        scheduled_duration = self._estimate_scheduled_duration(trip.route_id)
        delay_minutes = max(0, actual_duration - scheduled_duration)
        on_time_percentage = max(0, (scheduled_duration - delay_minutes) / scheduled_duration * 100) if scheduled_duration > 0 else 0
        
        # Calculate distance
        total_distance = self._calculate_trip_distance(locations)
        average_speed = (total_distance / (actual_duration / 60)) if actual_duration > 0 else 0
        
        # Get occupancy data
        occupancy_data = self._get_trip_occupancy_data(trip_id)
        
        # Calculate environmental impact
        co2_saved = self._calculate_co2_saved(occupancy_data['total_passengers'], total_distance)
        
        # Create or update analytics record
        analytics = self.db.query(TripAnalytics).filter(TripAnalytics.trip_id == trip_id).first()
        if not analytics:
            analytics = TripAnalytics(trip_id=trip_id)
            self.db.add(analytics)
        
        analytics.scheduled_duration_minutes = scheduled_duration
        analytics.actual_duration_minutes = actual_duration
        analytics.delay_minutes = delay_minutes
        analytics.on_time_percentage = on_time_percentage
        analytics.total_distance_km = total_distance
        analytics.average_speed_kmh = average_speed
        analytics.fuel_efficiency_estimate = self._estimate_fuel_efficiency(total_distance, actual_duration)
        analytics.total_passengers = occupancy_data['total_passengers']
        analytics.peak_occupancy_percentage = occupancy_data['peak_occupancy']
        analytics.average_occupancy_percentage = occupancy_data['average_occupancy']
        analytics.co2_saved_kg = co2_saved
        analytics.stops_completed = self._count_stops_completed(trip_id)
        analytics.stops_skipped = self._count_stops_skipped(trip_id)
        
        self.db.commit()
        self.db.refresh(analytics)
        return analytics
    
    def get_trip_history(
        self, 
        route_id: Optional[int] = None,
        vehicle_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get trip history with analytics data"""
        query = self.db.query(TripAnalytics, Trip, Route, Vehicle).join(
            Trip, TripAnalytics.trip_id == Trip.id
        ).join(
            Route, Trip.route_id == Route.id
        ).join(
            Vehicle, Trip.vehicle_id == Vehicle.id
        ).filter(Trip.status == TripStatus.COMPLETED)
        
        if route_id:
            query = query.filter(Trip.route_id == route_id)
        if vehicle_id:
            query = query.filter(Trip.vehicle_id == vehicle_id)
        if start_date:
            query = query.filter(func.date(Trip.start_time) >= start_date)
        if end_date:
            query = query.filter(func.date(Trip.start_time) <= end_date)
        
        results = query.order_by(desc(Trip.start_time)).limit(limit).all()
        
        return [
            {
                'trip_id': trip.id,
                'route_number': route.route_number,
                'route_name': route.name,
                'vehicle_number': vehicle.vehicle_number,
                'start_time': trip.start_time,
                'end_time': trip.end_time,
                'duration_minutes': analytics.actual_duration_minutes,
                'delay_minutes': analytics.delay_minutes,
                'on_time_percentage': analytics.on_time_percentage,
                'distance_km': analytics.total_distance_km,
                'average_speed_kmh': analytics.average_speed_kmh,
                'total_passengers': analytics.total_passengers,
                'peak_occupancy': analytics.peak_occupancy_percentage,
                'co2_saved_kg': analytics.co2_saved_kg,
                'stops_completed': analytics.stops_completed,
                'stops_skipped': analytics.stops_skipped
            }
            for analytics, trip, route, vehicle in results
        ]
    
    def get_performance_metrics(
        self,
        route_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Calculate performance metrics for trips"""
        query = self.db.query(TripAnalytics).join(Trip)
        
        if route_id:
            query = query.filter(Trip.route_id == route_id)
        if start_date:
            query = query.filter(func.date(Trip.start_time) >= start_date)
        if end_date:
            query = query.filter(func.date(Trip.start_time) <= end_date)
        
        analytics = query.all()
        
        if not analytics:
            return {
                'total_trips': 0,
                'on_time_percentage': 0,
                'average_delay_minutes': 0,
                'reliability_score': 0,
                'total_passengers': 0,
                'average_occupancy': 0,
                'total_co2_saved_kg': 0
            }
        
        total_trips = len(analytics)
        on_time_trips = len([a for a in analytics if a.delay_minutes <= 5])  # 5 min tolerance
        on_time_percentage = (on_time_trips / total_trips * 100) if total_trips > 0 else 0
        average_delay = sum(a.delay_minutes for a in analytics) / total_trips if total_trips > 0 else 0
        total_passengers = sum(a.total_passengers for a in analytics)
        average_occupancy = sum(a.average_occupancy_percentage for a in analytics) / total_trips if total_trips > 0 else 0
        total_co2_saved = sum(a.co2_saved_kg for a in analytics)
        
        # Calculate reliability score (0-100)
        reliability_factors = [
            on_time_percentage / 100,  # On-time performance
            max(0, 1 - (average_delay / 30)),  # Delay factor (30 min max)
            min(1, total_trips / 10)  # Trip frequency factor
        ]
        reliability_score = sum(reliability_factors) / len(reliability_factors) * 100
        
        return {
            'total_trips': total_trips,
            'on_time_percentage': round(on_time_percentage, 2),
            'average_delay_minutes': round(average_delay, 2),
            'reliability_score': round(reliability_score, 2),
            'total_passengers': total_passengers,
            'average_occupancy': round(average_occupancy, 2),
            'total_co2_saved_kg': round(total_co2_saved, 2)
        }
    
    def get_ridership_estimation(
        self,
        route_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Estimate ridership patterns and trends"""
        query = self.db.query(TripAnalytics).join(Trip)
        
        if route_id:
            query = query.filter(Trip.route_id == route_id)
        if start_date:
            query = query.filter(func.date(Trip.start_time) >= start_date)
        if end_date:
            query = query.filter(func.date(Trip.start_time) <= end_date)
        
        analytics = query.all()
        
        if not analytics:
            return {
                'total_passengers': 0,
                'average_daily_passengers': 0,
                'peak_hour_occupancy': 0,
                'growth_trend': 0,
                'seasonal_patterns': {}
            }
        
        # Calculate daily patterns
        daily_passengers = {}
        hourly_occupancy = {}
        
        for analytics_record in analytics:
            trip = self.db.query(Trip).filter(Trip.id == analytics_record.trip_id).first()
            if trip and trip.start_time:
                day_key = trip.start_time.date()
                hour = trip.start_time.hour
                
                daily_passengers[day_key] = daily_passengers.get(day_key, 0) + analytics_record.total_passengers
                hourly_occupancy[hour] = hourly_occupancy.get(hour, [])
                hourly_occupancy[hour].append(analytics_record.peak_occupancy_percentage)
        
        total_passengers = sum(daily_passengers.values())
        average_daily = total_passengers / len(daily_passengers) if daily_passengers else 0
        
        # Calculate peak hour occupancy
        peak_hour_occupancy = 0
        for hour, occupancies in hourly_occupancy.items():
            if occupancies:
                avg_occupancy = sum(occupancies) / len(occupancies)
                peak_hour_occupancy = max(peak_hour_occupancy, avg_occupancy)
        
        # Calculate growth trend (simplified)
        if len(daily_passengers) > 7:
            recent_days = sorted(daily_passengers.keys())[-7:]
            older_days = sorted(daily_passengers.keys())[:-7]
            
            recent_avg = sum(daily_passengers[d] for d in recent_days) / len(recent_days)
            older_avg = sum(daily_passengers[d] for d in older_days) / len(older_days) if older_days else recent_avg
            
            growth_trend = ((recent_avg - older_avg) / older_avg * 100) if older_avg > 0 else 0
        else:
            growth_trend = 0
        
        return {
            'total_passengers': total_passengers,
            'average_daily_passengers': round(average_daily, 2),
            'peak_hour_occupancy': round(peak_hour_occupancy, 2),
            'growth_trend': round(growth_trend, 2),
            'daily_patterns': daily_passengers,
            'hourly_occupancy': {str(k): round(sum(v)/len(v), 2) for k, v in hourly_occupancy.items() if v}
        }
    
    def calculate_carbon_footprint(
        self,
        route_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Calculate environmental impact and carbon footprint"""
        query = self.db.query(TripAnalytics).join(Trip)
        
        if route_id:
            query = query.filter(Trip.route_id == route_id)
        if start_date:
            query = query.filter(func.date(Trip.start_time) >= start_date)
        if end_date:
            query = query.filter(func.date(Trip.start_time) <= end_date)
        
        analytics = query.all()
        
        total_co2_saved = sum(a.co2_saved_kg for a in analytics)
        total_distance = sum(a.total_distance_km for a in analytics)
        total_passengers = sum(a.total_passengers for a in analytics)
        
        # Calculate equivalent cars off road
        # Average car emits ~120g CO2 per km, bus emits ~89g CO2 per km per passenger
        avg_car_emissions_per_km = 0.120  # kg CO2 per km
        avg_bus_emissions_per_km_per_passenger = 0.089  # kg CO2 per km per passenger
        
        if total_distance > 0 and total_passengers > 0:
            car_emissions = total_distance * avg_car_emissions_per_km * total_passengers
            bus_emissions = total_distance * avg_bus_emissions_per_km_per_passenger * total_passengers
            net_co2_saved = car_emissions - bus_emissions
            
            # Convert to equivalent cars (assuming 10,000 km per year per car)
            equivalent_cars = net_co2_saved / (avg_car_emissions_per_km * 10000)
        else:
            equivalent_cars = 0
        
        return {
            'total_co2_saved_kg': round(total_co2_saved, 2),
            'total_distance_km': round(total_distance, 2),
            'total_passengers': total_passengers,
            'equivalent_cars_off_road': round(equivalent_cars, 2),
            'co2_saved_per_passenger_kg': round(total_co2_saved / total_passengers, 2) if total_passengers > 0 else 0,
            'co2_saved_per_km_kg': round(total_co2_saved / total_distance, 2) if total_distance > 0 else 0
        }
    
    # Predictive Analytics
    
    def generate_demand_prediction(
        self,
        route_id: int,
        prediction_date: date,
        days_ahead: int = 7
    ) -> Dict[str, Any]:
        """Generate demand prediction for a route"""
        # Get historical data for the same day of week
        historical_data = self._get_historical_demand_data(route_id, prediction_date, days_ahead)
        
        if not historical_data:
            return {
                'route_id': route_id,
                'prediction_date': prediction_date,
                'predicted_demand': 0,
                'confidence_score': 0,
                'factors': ['insufficient_data']
            }
        
        # Simple prediction based on historical average and trend
        avg_demand = sum(historical_data) / len(historical_data)
        trend = self._calculate_demand_trend(historical_data)
        
        # Apply trend and seasonal factors
        predicted_demand = avg_demand * (1 + trend)
        
        # Calculate confidence based on data quality
        confidence = min(1.0, len(historical_data) / 30)  # More data = higher confidence
        
        # Store prediction
        prediction = PredictiveAnalytics(
            route_id=route_id,
            prediction_type='demand',
            prediction_date=datetime.combine(prediction_date, datetime.min.time()),
            predicted_value=predicted_demand,
            confidence_score=confidence,
            model_version='v1.0',
            features_used=['historical_average', 'trend', 'day_of_week']
        )
        self.db.add(prediction)
        self.db.commit()
        
        return {
            'route_id': route_id,
            'prediction_date': prediction_date,
            'predicted_demand': round(predicted_demand, 2),
            'confidence_score': round(confidence, 2),
            'historical_average': round(avg_demand, 2),
            'trend_percentage': round(trend * 100, 2),
            'factors': ['historical_average', 'trend', 'day_of_week']
        }
    
    def generate_delay_prediction(
        self,
        route_id: int,
        prediction_date: date,
        time_of_day: str = 'morning'
    ) -> Dict[str, Any]:
        """Generate delay prediction for a route"""
        # Get historical delay data
        historical_delays = self._get_historical_delay_data(route_id, prediction_date, time_of_day)
        
        if not historical_delays:
            return {
                'route_id': route_id,
                'prediction_date': prediction_date,
                'time_of_day': time_of_day,
                'predicted_delay_minutes': 0,
                'confidence_score': 0,
                'factors': ['insufficient_data']
            }
        
        # Calculate prediction
        avg_delay = sum(historical_delays) / len(historical_delays)
        delay_variance = sum((d - avg_delay) ** 2 for d in historical_delays) / len(historical_delays)
        delay_std = math.sqrt(delay_variance)
        
        # Confidence interval (±1 standard deviation)
        confidence_lower = max(0, avg_delay - delay_std)
        confidence_upper = avg_delay + delay_std
        
        confidence_score = min(1.0, len(historical_delays) / 20)
        
        # Store prediction
        prediction = PredictiveAnalytics(
            route_id=route_id,
            prediction_type='delay',
            prediction_date=datetime.combine(prediction_date, datetime.min.time()),
            predicted_value=avg_delay,
            confidence_interval_lower=confidence_lower,
            confidence_interval_upper=confidence_upper,
            confidence_score=confidence_score,
            model_version='v1.0',
            features_used=['historical_delays', 'time_of_day', 'day_of_week']
        )
        self.db.add(prediction)
        self.db.commit()
        
        return {
            'route_id': route_id,
            'prediction_date': prediction_date,
            'time_of_day': time_of_day,
            'predicted_delay_minutes': round(avg_delay, 2),
            'confidence_interval_lower': round(confidence_lower, 2),
            'confidence_interval_upper': round(confidence_upper, 2),
            'confidence_score': round(confidence_score, 2),
            'factors': ['historical_delays', 'time_of_day', 'day_of_week']
        }
    
    # Helper methods
    
    def _estimate_scheduled_duration(self, route_id: int) -> float:
        """Estimate scheduled trip duration based on route characteristics"""
        # This would typically come from route schedule data
        # For now, return a default based on route complexity
        route = self.db.query(Route).filter(Route.id == route_id).first()
        if route and route.geojson:
            # Estimate based on route length (simplified)
            return 45.0  # Default 45 minutes
        return 30.0  # Default 30 minutes
    
    def _calculate_trip_distance(self, locations: List[VehicleLocation]) -> float:
        """Calculate total distance traveled using Haversine formula"""
        if len(locations) < 2:
            return 0.0
        
        total_distance = 0.0
        for i in range(1, len(locations)):
            lat1, lon1 = locations[i-1].latitude, locations[i-1].longitude
            lat2, lon2 = locations[i].latitude, locations[i].longitude
            total_distance += self._haversine_distance(lat1, lon1, lat2, lon2)
        
        return total_distance
    
    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points using Haversine formula"""
        R = 6371  # Earth's radius in kilometers
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2)
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c
    
    def _get_trip_occupancy_data(self, trip_id: int) -> Dict[str, Any]:
        """Get occupancy data for a trip"""
        trip = self.db.query(Trip).filter(Trip.id == trip_id).first()
        if not trip:
            return {'total_passengers': 0, 'peak_occupancy': 0, 'average_occupancy': 0}
        
        occupancy_reports = self.db.query(OccupancyReport).filter(
            OccupancyReport.vehicle_id == trip.vehicle_id,
            OccupancyReport.timestamp >= trip.start_time,
            OccupancyReport.timestamp <= trip.end_time
        ).all()
        
        if not occupancy_reports:
            return {'total_passengers': 0, 'peak_occupancy': 0, 'average_occupancy': 0}
        
        total_passengers = sum(r.passenger_count for r in occupancy_reports)
        peak_occupancy = max(r.occupancy_level for r in occupancy_reports) if occupancy_reports else 0
        average_occupancy = sum(r.occupancy_level for r in occupancy_reports) / len(occupancy_reports)
        
        return {
            'total_passengers': total_passengers,
            'peak_occupancy': peak_occupancy,
            'average_occupancy': average_occupancy
        }
    
    def _calculate_co2_saved(self, passengers: int, distance_km: float) -> float:
        """Calculate CO2 saved compared to private vehicles"""
        # Average car emissions: 120g CO2 per km
        # Average bus emissions: 89g CO2 per km per passenger
        car_emissions_per_km = 0.120  # kg CO2 per km
        bus_emissions_per_km_per_passenger = 0.089  # kg CO2 per km per passenger
        
        if passengers == 0 or distance_km == 0:
            return 0.0
        
        car_emissions = distance_km * car_emissions_per_km * passengers
        bus_emissions = distance_km * bus_emissions_per_km_per_passenger * passengers
        
        return max(0, car_emissions - bus_emissions)
    
    def _estimate_fuel_efficiency(self, distance_km: float, duration_minutes: float) -> float:
        """Estimate fuel efficiency in km per liter"""
        # Typical bus fuel efficiency: 3-5 km per liter
        # Adjust based on speed and distance
        base_efficiency = 4.0  # km per liter
        speed_factor = min(1.2, max(0.8, (distance_km / (duration_minutes / 60)) / 30))  # Speed factor
        return base_efficiency * speed_factor
    
    def _count_stops_completed(self, trip_id: int) -> int:
        """Count stops completed during trip"""
        # This would typically be tracked during the trip
        # For now, return a default value
        return 10  # Default number of stops
    
    def _count_stops_skipped(self, trip_id: int) -> int:
        """Count stops skipped during trip"""
        # This would typically be tracked during the trip
        # For now, return a default value
        return 0  # Default no skipped stops
    
    def _get_historical_demand_data(self, route_id: int, prediction_date: date, days: int) -> List[float]:
        """Get historical demand data for prediction"""
        end_date = prediction_date - timedelta(days=1)
        start_date = end_date - timedelta(days=days * 4)  # Look back 4x the prediction period
        
        query = self.db.query(TripAnalytics).join(Trip).filter(
            Trip.route_id == route_id,
            func.date(Trip.start_time) >= start_date,
            func.date(Trip.start_time) <= end_date
        )
        
        analytics = query.all()
        return [a.total_passengers for a in analytics]
    
    def _calculate_demand_trend(self, data: List[float]) -> float:
        """Calculate trend in demand data"""
        if len(data) < 2:
            return 0.0
        
        # Simple linear trend calculation
        n = len(data)
        x = list(range(n))
        y = data
        
        x_mean = sum(x) / n
        y_mean = sum(y) / n
        
        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return 0.0
        
        slope = numerator / denominator
        return slope / y_mean if y_mean > 0 else 0.0
    
    def _get_historical_delay_data(self, route_id: int, prediction_date: date, time_of_day: str) -> List[float]:
        """Get historical delay data for prediction"""
        end_date = prediction_date - timedelta(days=1)
        start_date = end_date - timedelta(days=30)  # Look back 30 days
        
        # Filter by time of day
        if time_of_day == 'morning':
            hour_start, hour_end = 6, 12
        elif time_of_day == 'afternoon':
            hour_start, hour_end = 12, 18
        elif time_of_day == 'evening':
            hour_start, hour_end = 18, 22
        else:
            hour_start, hour_end = 0, 23
        
        query = self.db.query(TripAnalytics).join(Trip).filter(
            Trip.route_id == route_id,
            func.date(Trip.start_time) >= start_date,
            func.date(Trip.start_time) <= end_date,
            func.hour(Trip.start_time) >= hour_start,
            func.hour(Trip.start_time) <= hour_end
        )
        
        analytics = query.all()
        return [a.delay_minutes for a in analytics if a.delay_minutes is not None]
