from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from ...core.database import get_db
from ...core.auth import get_current_user, create_access_token
from ...core.dependencies import get_current_driver
from ...repositories.driver import DriverRepository
from ...repositories.issue import IssueRepository
from ...repositories.vehicle import VehicleRepository
from ...models.user import User
from ...models.driver import Driver
from ...schemas.driver import (
    DriverLogin, DriverLoginResponse, DriverProfile, DriverDashboard,
    TripResponse, TripUpdate, OccupancyReport, OccupancyResponse,
    IssueReport, IssueResponse, LocationPing, LocationPingResponse,
    DispatchMessage, MessageResponse, ShiftSchedule
)

router = APIRouter()

@router.post("/login", response_model=DriverLoginResponse)
async def driver_login(
    login_data: DriverLogin,
    db: Session = Depends(get_db)
):
    """Driver authentication endpoint"""
    driver_repo = DriverRepository(db)
    driver = driver_repo.get_by_phone(login_data.phone)
    
    if not driver:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid phone number or password"
        )
    
    # In a real implementation, you would verify the password hash
    # For demo purposes, we'll use a simple check
    if login_data.password != "driver123":  # Demo password
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid phone number or password"
        )
    
    # Create access token
    access_token = create_access_token(data={"sub": str(driver.id), "type": "driver"})
    
    # Get driver profile
    profile = driver_repo.get_driver_profile(driver.id)
    
    return DriverLoginResponse(
        access_token=access_token,
        driver=profile
    )

@router.get("/dashboard", response_model=DriverDashboard)
async def get_driver_dashboard(
    current_driver: Driver = Depends(get_current_driver),
    db: Session = Depends(get_db)
):
    """Get driver dashboard data"""
    driver_repo = DriverRepository(db)
    
    # Get driver profile
    profile = driver_repo.get_driver_profile(current_driver.id)
    
    # Get current trip
    current_trip = driver_repo.get_current_trip(current_driver.id)
    current_trip_data = None
    if current_trip:
        current_trip_data = TripResponse(
            id=current_trip.id,
            vehicle_id=current_trip.vehicle_id,
            route_id=current_trip.route_id,
            driver_id=current_trip.driver_id,
            start_time=current_trip.start_time,
            end_time=current_trip.end_time,
            status=current_trip.status,
            created_at=current_trip.created_at,
            vehicle_number=current_trip.vehicle.vehicle_number if current_trip.vehicle else None,
            route_name=current_trip.route.name if current_trip.route else None,
            route_number=current_trip.route.route_number if current_trip.route else None
        )
    
    # Get upcoming shifts
    upcoming_shifts = driver_repo.get_upcoming_shifts(current_driver.id)
    shifts_data = [
        ShiftSchedule(
            id=shift.id,
            driver_id=shift.driver_id,
            start_time=shift.start_time,
            end_time=shift.end_time,
            route_id=shift.route_id,
            vehicle_id=shift.vehicle_id,
            status=shift.status.value,
            route_name=shift.route.name if shift.route else None,
            route_number=shift.route.route_number if shift.route else None,
            vehicle_number=shift.vehicle.vehicle_number if shift.vehicle else None
        )
        for shift in upcoming_shifts
    ]
    
    # Get recent issues
    recent_issues = driver_repo.get_recent_issues(current_driver.id, limit=5)
    issues_data = [
        IssueResponse(
            id=issue.id,
            category=issue.category,
            priority=issue.priority,
            title=issue.title,
            description=issue.description,
            location_lat=issue.location_lat,
            location_lng=issue.location_lng,
            vehicle_id=issue.vehicle_id,
            route_id=issue.route_id,
            reported_by=issue.reported_by,
            status=issue.status.value,
            created_at=issue.created_at,
            resolved_at=issue.resolved_at
        )
        for issue in recent_issues
    ]
    
    # Get today's stats
    today_stats = driver_repo.get_today_stats(current_driver.id)
    
    return DriverDashboard(
        driver=profile,
        current_trip=current_trip_data,
        upcoming_shifts=shifts_data,
        recent_issues=issues_data,
        today_stats=today_stats
    )

@router.post("/trips/{trip_id}/start", response_model=TripResponse)
async def start_trip(
    trip_id: int,
    current_driver: Driver = Depends(get_current_driver),
    db: Session = Depends(get_db)
):
    """Start a trip"""
    driver_repo = DriverRepository(db)
    trip = driver_repo.start_trip(trip_id, current_driver.id)
    
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found or cannot be started"
        )
    
    return TripResponse(
        id=trip.id,
        vehicle_id=trip.vehicle_id,
        route_id=trip.route_id,
        driver_id=trip.driver_id,
        start_time=trip.start_time,
        end_time=trip.end_time,
        status=trip.status,
        created_at=trip.created_at,
        vehicle_number=trip.vehicle.vehicle_number if trip.vehicle else None,
        route_name=trip.route.name if trip.route else None,
        route_number=trip.route.route_number if trip.route else None
    )

@router.post("/trips/{trip_id}/end", response_model=TripResponse)
async def end_trip(
    trip_id: int,
    current_driver: Driver = Depends(get_current_driver),
    db: Session = Depends(get_db)
):
    """End a trip"""
    driver_repo = DriverRepository(db)
    trip = driver_repo.end_trip(trip_id, current_driver.id)
    
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found or cannot be ended"
        )
    
    return TripResponse(
        id=trip.id,
        vehicle_id=trip.vehicle_id,
        route_id=trip.route_id,
        driver_id=trip.driver_id,
        start_time=trip.start_time,
        end_time=trip.end_time,
        status=trip.status,
        created_at=trip.created_at,
        vehicle_number=trip.vehicle.vehicle_number if trip.vehicle else None,
        route_name=trip.route.name if trip.route else None,
        route_number=trip.route.route_number if trip.route else None
    )

@router.post("/occupancy", response_model=OccupancyResponse)
async def report_occupancy(
    occupancy_data: OccupancyReport,
    current_driver: Driver = Depends(get_current_driver),
    db: Session = Depends(get_db)
):
    """Report vehicle occupancy"""
    driver_repo = DriverRepository(db)
    
    # Verify driver has access to this vehicle
    current_trip = driver_repo.get_current_trip(current_driver.id)
    if not current_trip or current_trip.vehicle_id != occupancy_data.vehicle_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only report occupancy for your assigned vehicle"
        )
    
    occupancy = driver_repo.report_occupancy(occupancy_data, current_driver.id)
    
    return OccupancyResponse(
        id=occupancy.id,
        vehicle_id=occupancy.vehicle_id,
        occupancy_level=occupancy.occupancy_level,
        passenger_count=occupancy.passenger_count,
        timestamp=occupancy.timestamp,
        reported_by=occupancy.driver_id
    )

@router.post("/issues", response_model=IssueResponse)
async def report_issue(
    issue_data: IssueReport,
    current_driver: Driver = Depends(get_current_driver),
    db: Session = Depends(get_db)
):
    """Report an issue"""
    issue_repo = IssueRepository(db)
    issue = issue_repo.create_issue(issue_data, current_driver.id)
    
    return IssueResponse(
        id=issue.id,
        category=issue.category,
        priority=issue.priority,
        title=issue.title,
        description=issue.description,
        location_lat=issue.location_lat,
        location_lng=issue.location_lng,
        vehicle_id=issue.vehicle_id,
        route_id=issue.route_id,
        reported_by=issue.reported_by,
        status=issue.status.value,
        created_at=issue.created_at,
        resolved_at=issue.resolved_at
    )

@router.get("/issues", response_model=List[IssueResponse])
async def get_driver_issues(
    current_driver: Driver = Depends(get_current_driver),
    db: Session = Depends(get_db)
):
    """Get driver's issues"""
    issue_repo = IssueRepository(db)
    issues = issue_repo.get_driver_issues(current_driver.id)
    
    return [
        IssueResponse(
            id=issue.id,
            category=issue.category,
            priority=issue.priority,
            title=issue.title,
            description=issue.description,
            location_lat=issue.location_lat,
            location_lng=issue.location_lng,
            vehicle_id=issue.vehicle_id,
            route_id=issue.route_id,
            reported_by=issue.reported_by,
            status=issue.status.value,
            created_at=issue.created_at,
            resolved_at=issue.resolved_at
        )
        for issue in issues
    ]

@router.post("/location", response_model=LocationPingResponse)
async def ping_location(
    location_data: LocationPing,
    current_driver: Driver = Depends(get_current_driver),
    db: Session = Depends(get_db)
):
    """Update driver location"""
    # Get current trip to get vehicle ID
    driver_repo = DriverRepository(db)
    current_trip = driver_repo.get_current_trip(current_driver.id)
    
    if not current_trip:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active trip found. Start a trip to track location."
        )
    
    # Store location in vehicle_locations table
    from ...repositories.location import LocationRepository
    location_repo = LocationRepository(db)
    
    location_repo.create_location(
        vehicle_id=current_trip.vehicle_id,
        latitude=location_data.latitude,
        longitude=location_data.longitude,
        speed=location_data.speed or 0,
        bearing=location_data.bearing or 0
    )
    
    return LocationPingResponse(
        success=True,
        message="Location updated successfully",
        recorded_at=datetime.utcnow()
    )

@router.get("/shifts", response_model=List[ShiftSchedule])
async def get_driver_shifts(
    days: int = 7,
    current_driver: Driver = Depends(get_current_driver),
    db: Session = Depends(get_db)
):
    """Get driver's upcoming shifts"""
    driver_repo = DriverRepository(db)
    shifts = driver_repo.get_upcoming_shifts(current_driver.id, days)
    
    return [
        ShiftSchedule(
            id=shift.id,
            driver_id=shift.driver_id,
            start_time=shift.start_time,
            end_time=shift.end_time,
            route_id=shift.route_id,
            vehicle_id=shift.vehicle_id,
            status=shift.status.value,
            route_name=shift.route.name if shift.route else None,
            route_number=shift.route.route_number if shift.route else None,
            vehicle_number=shift.vehicle.vehicle_number if shift.vehicle else None
        )
        for shift in shifts
    ]

@router.post("/messages", response_model=MessageResponse)
async def send_message_to_dispatch(
    message_data: DispatchMessage,
    current_driver: Driver = Depends(get_current_driver),
    db: Session = Depends(get_db)
):
    """Send message to dispatch"""
    # In a real implementation, this would store the message and notify dispatch
    # For demo purposes, we'll return a mock response
    return MessageResponse(
        id=1,
        message=message_data.message,
        priority=message_data.priority,
        sender_id=current_driver.id,
        sender_name=current_driver.name,
        recipient_type=message_data.recipient_type,
        created_at=datetime.utcnow()
    )