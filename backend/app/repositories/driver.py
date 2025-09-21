from typing import Optional, List
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc
from datetime import datetime, timedelta

from .base import BaseRepository
from ..models.driver import Driver, DriverStatus
from ..models.trip import Trip, TripStatus
from ..models.occupancy import OccupancyReport
from ..models.issue import Issue
from ..models.shift_schedule import ShiftSchedule
from ..schemas.driver import DriverProfile, TripResponse, OccupancyReport as OccupancySchema

class DriverRepository(BaseRepository[Driver]):
    def __init__(self, db: Session):
        super().__init__(Driver, db)

    def get_by_phone(self, phone: str) -> Optional[Driver]:
        """Get driver by phone number"""
        return self.db.query(Driver).filter(Driver.phone == phone).first()

    def get_driver_profile(self, driver_id: int) -> Optional[DriverProfile]:
        """Get complete driver profile with vehicle and route info"""
        driver = self.db.query(Driver).options(
            joinedload(Driver.assigned_vehicle)
        ).filter(Driver.id == driver_id).first()
        
        if not driver:
            return None

        # Get current active trip
        current_trip = self.db.query(Trip).filter(
            and_(
                Trip.driver_id == driver_id,
                Trip.status == TripStatus.ACTIVE
            )
        ).first()

        return DriverProfile(
            id=driver.id,
            name=driver.name,
            phone=driver.phone,
            license_number=driver.license_number,
            status=driver.status,
            assigned_vehicle_id=driver.assigned_vehicle_id,
            assigned_vehicle_number=driver.assigned_vehicle.vehicle_number if driver.assigned_vehicle else None,
            current_route_id=current_trip.route_id if current_trip else None,
            current_route_name=current_trip.route.name if current_trip and current_trip.route else None
        )

    def get_current_trip(self, driver_id: int) -> Optional[Trip]:
        """Get driver's current active trip"""
        return self.db.query(Trip).options(
            joinedload(Trip.vehicle),
            joinedload(Trip.route)
        ).filter(
            and_(
                Trip.driver_id == driver_id,
                Trip.status == TripStatus.ACTIVE
            )
        ).first()

    def get_upcoming_shifts(self, driver_id: int, days: int = 7) -> List[ShiftSchedule]:
        """Get driver's upcoming shifts"""
        end_date = datetime.utcnow() + timedelta(days=days)
        return self.db.query(ShiftSchedule).options(
            joinedload(ShiftSchedule.route),
            joinedload(ShiftSchedule.vehicle)
        ).filter(
            and_(
                ShiftSchedule.driver_id == driver_id,
                ShiftSchedule.start_time >= datetime.utcnow(),
                ShiftSchedule.start_time <= end_date
            )
        ).order_by(ShiftSchedule.start_time).all()

    def get_recent_issues(self, driver_id: int, limit: int = 10) -> List[Issue]:
        """Get driver's recent issues"""
        return self.db.query(Issue).filter(
            Issue.reported_by == driver_id
        ).order_by(desc(Issue.created_at)).limit(limit).all()

    def start_trip(self, trip_id: int, driver_id: int) -> Optional[Trip]:
        """Start a trip"""
        trip = self.db.query(Trip).filter(
            and_(
                Trip.id == trip_id,
                Trip.driver_id == driver_id,
                Trip.status == TripStatus.SCHEDULED
            )
        ).first()
        
        if trip:
            trip.status = TripStatus.ACTIVE
            trip.start_time = datetime.utcnow()
            self.db.commit()
            self.db.refresh(trip)
        
        return trip

    def end_trip(self, trip_id: int, driver_id: int) -> Optional[Trip]:
        """End a trip"""
        trip = self.db.query(Trip).filter(
            and_(
                Trip.id == trip_id,
                Trip.driver_id == driver_id,
                Trip.status == TripStatus.ACTIVE
            )
        ).first()
        
        if trip:
            trip.status = TripStatus.COMPLETED
            trip.end_time = datetime.utcnow()
            self.db.commit()
            self.db.refresh(trip)
        
        return trip

    def report_occupancy(self, occupancy_data: OccupancySchema, driver_id: int) -> OccupancyReport:
        """Report vehicle occupancy"""
        occupancy = OccupancyReport(
            vehicle_id=occupancy_data.vehicle_id,
            driver_id=driver_id,
            occupancy_level=occupancy_data.occupancy_level,
            passenger_count=occupancy_data.passenger_count,
            timestamp=occupancy_data.timestamp or datetime.utcnow()
        )
        self.db.add(occupancy)
        self.db.commit()
        self.db.refresh(occupancy)
        return occupancy

    def get_today_stats(self, driver_id: int) -> dict:
        """Get driver's today statistics"""
        today = datetime.utcnow().date()
        
        # Count today's trips
        trips_today = self.db.query(Trip).filter(
            and_(
                Trip.driver_id == driver_id,
                Trip.start_time >= today,
                Trip.status.in_([TripStatus.ACTIVE, TripStatus.COMPLETED])
            )
        ).count()

        # Count today's issues
        issues_today = self.db.query(Issue).filter(
            and_(
                Issue.reported_by == driver_id,
                Issue.created_at >= today
            )
        ).count()

        # Get shift hours today
        shifts_today = self.db.query(ShiftSchedule).filter(
            and_(
                ShiftSchedule.driver_id == driver_id,
                ShiftSchedule.start_time >= today
            )
        ).all()

        total_hours = sum([
            (shift.end_time - shift.start_time).total_seconds() / 3600
            for shift in shifts_today
        ])

        return {
            "trips_completed": trips_today,
            "issues_reported": issues_today,
            "hours_scheduled": round(total_hours, 1),
            "status": "active"  # This could be calculated based on current time and shifts
        }