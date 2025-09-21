from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from ....core.database import get_db
from ....core.dependencies import get_admin_user
from ....repositories.audit_log import (
    AuditLogRepository, AdminRoleRepository, 
    AdminRoleAssignmentRepository, AdminUserRepository
)
from ....repositories.factory import get_repositories
from ....schemas.admin import (
    AdminUserCreate, AdminUserUpdate, AdminUserResponse,
    UserListResponse, RoleChangeRequest, BulkUserAction,
    AdminDashboardStats, SystemHealth, AuditLogResponse,
    AdminRole, AdminRoleCreate, AdminRoleUpdate,
    RouteCreateRequest, RouteUpdateRequest, RouteStopCreate,
    RouteStopUpdate, RouteStopReorderRequest, RouteValidationResult,
    BulkRouteImport, BulkRouteExport
)
from ....schemas.auth import UserResponse
from ....models.user import User, UserRole
from ....models.route import Route
from ....models.stop import Stop
from ....core.auth import get_password_hash
import redis
import time
import psutil
from datetime import datetime, timedelta

router = APIRouter()

def log_admin_action(
    request: Request,
    admin: User,
    action: str,
    resource_type: str,
    resource_id: Optional[int] = None,
    details: Optional[dict] = None,
    db: Session = None
):
    """Helper function to log admin actions"""
    if db:
        audit_repo = AuditLogRepository(db)
        audit_repo.log_action(
            admin_id=admin.id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )

# Dashboard and Statistics
@router.get("/dashboard/stats", response_model=AdminDashboardStats)
def get_dashboard_stats(
    current_admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get admin dashboard statistics"""
    admin_user_repo = AdminUserRepository(db)
    stats = admin_user_repo.get_dashboard_stats()
    return AdminDashboardStats(**stats)

@router.get("/system/health", response_model=SystemHealth)
def get_system_health(
    current_admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get system health metrics"""
    try:
        # Test database connection
        db.execute("SELECT 1")
        db_status = "healthy"
    except Exception:
        db_status = "unhealthy"
    
    try:
        # Test Redis connection (if available)
        # This is a simplified check - in production you'd use actual Redis client
        redis_status = "healthy"  # Placeholder
    except Exception:
        redis_status = "unhealthy"
    
    # Get system metrics
    process = psutil.Process()
    uptime_seconds = time.time() - process.create_time()
    uptime_str = str(timedelta(seconds=int(uptime_seconds)))
    
    return SystemHealth(
        database_status=db_status,
        redis_status=redis_status,
        websocket_connections=0,  # Placeholder - would get from WebSocket manager
        active_buses=0,  # Placeholder - would get from vehicle repository
        api_response_time=0.05,  # Placeholder - would get from monitoring
        error_rate=0.01,  # Placeholder - would get from monitoring
        uptime=uptime_str
    )

# User Management
@router.get("/users", response_model=UserListResponse)
def list_users(
    request: Request,
    page: int = 1,
    per_page: int = 20,
    role: Optional[UserRole] = None,
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
) -> Any:
    """List users with pagination and filtering"""
    admin_user_repo = AdminUserRepository(db)
    result = admin_user_repo.get_users_with_pagination(
        page=page,
        per_page=per_page,
        role=role,
        search=search,
        is_active=is_active
    )
    
    log_admin_action(
        request, current_admin, "list_users", "user",
        details={"filters": {"role": role, "search": search, "is_active": is_active}},
        db=db
    )
    
    return UserListResponse(**result)

@router.post("/users", response_model=AdminUserResponse)
def create_user(
    request: Request,
    user_data: AdminUserCreate,
    current_admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
) -> Any:
    """Create a new user (admin only)"""
    repos = get_repositories(db)
    
    # Check if user already exists
    if repos.user.get_by_email(user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    if user_data.phone and repos.user.get_by_phone(user_data.phone):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number already registered"
        )
    
    # Create user
    hashed_password = get_password_hash(user_data.password)
    user = User(
        email=user_data.email,
        phone=user_data.phone,
        full_name=user_data.full_name,
        hashed_password=hashed_password,
        role=user_data.role,
        is_active=user_data.is_active,
        is_verified=user_data.is_verified
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    log_admin_action(
        request, current_admin, "create_user", "user", user.id,
        details={"email": user.email, "role": user.role.value},
        db=db
    )
    
    return user

@router.get("/users/{user_id}", response_model=AdminUserResponse)
def get_user(
    user_id: int,
    current_admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get user by ID"""
    repos = get_repositories(db)
    user = repos.user.get(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user

@router.put("/users/{user_id}", response_model=AdminUserResponse)
def update_user(
    request: Request,
    user_id: int,
    user_update: AdminUserUpdate,
    current_admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
) -> Any:
    """Update user by ID"""
    repos = get_repositories(db)
    user = repos.user.get(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check for email conflicts
    if user_update.email and user_update.email != user.email:
        existing_user = repos.user.get_by_email(user_update.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use"
            )
    
    # Check for phone conflicts
    if user_update.phone and user_update.phone != user.phone:
        existing_user = repos.user.get_by_phone(user_update.phone)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone number already in use"
            )
    
    # Update user fields
    update_data = user_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    
    log_admin_action(
        request, current_admin, "update_user", "user", user.id,
        details={"updated_fields": list(update_data.keys())},
        db=db
    )
    
    return user

@router.delete("/users/{user_id}")
def delete_user(
    request: Request,
    user_id: int,
    current_admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
) -> Any:
    """Delete user by ID"""
    repos = get_repositories(db)
    user = repos.user.get(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Don't allow deleting yourself
    if user.id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    # Don't allow deleting other admins (optional business rule)
    if user.role == UserRole.ADMIN and user.id != current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete other admin accounts"
        )
    
    db.delete(user)
    db.commit()
    
    log_admin_action(
        request, current_admin, "delete_user", "user", user_id,
        details={"email": user.email, "role": user.role.value},
        db=db
    )
    
    return {"message": "User deleted successfully"}

@router.post("/users/bulk-action")
def bulk_user_action(
    request: Request,
    action_data: BulkUserAction,
    current_admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
) -> Any:
    """Perform bulk actions on users"""
    admin_user_repo = AdminUserRepository(db)
    result = admin_user_repo.bulk_update_users(
        user_ids=action_data.user_ids,
        action=action_data.action,
        admin_id=current_admin.id
    )
    
    log_admin_action(
        request, current_admin, f"bulk_{action_data.action}", "user",
        details={
            "user_ids": action_data.user_ids,
            "action": action_data.action,
            "reason": action_data.reason
        },
        db=db
    )
    
    return result

@router.post("/users/{user_id}/change-role")
def change_user_role(
    request: Request,
    user_id: int,
    role_change: RoleChangeRequest,
    current_admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
) -> Any:
    """Change user role"""
    repos = get_repositories(db)
    user = repos.user.get(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Don't allow changing your own role
    if user.id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change your own role"
        )
    
    old_role = user.role
    user.role = role_change.new_role
    db.commit()
    db.refresh(user)
    
    log_admin_action(
        request, current_admin, "change_user_role", "user", user.id,
        details={
            "old_role": old_role.value,
            "new_role": role_change.new_role.value,
            "reason": role_change.reason
        },
        db=db
    )
    
    return {"message": f"User role changed from {old_role.value} to {role_change.new_role.value}"}

# Audit Logs
@router.get("/audit-logs", response_model=AuditLogResponse)
def get_audit_logs(
    page: int = 1,
    per_page: int = 50,
    admin_id: Optional[int] = None,
    action: Optional[str] = None,
    hours: int = 24,
    current_admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get audit logs with pagination"""
    audit_repo = AuditLogRepository(db)
    
    if admin_id:
        logs = audit_repo.get_logs_by_admin(admin_id, per_page, (page - 1) * per_page)
        total = len(logs)  # Simplified - in production you'd get actual count
    else:
        logs = audit_repo.get_recent_logs(per_page, (page - 1) * per_page, hours)
        total = len(logs)  # Simplified - in production you'd get actual count
    
    total_pages = (total + per_page - 1) // per_page
    
    return AuditLogResponse(
        logs=logs,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages
    )

# Live Operations Dashboard
@router.get("/dashboard/live-buses")
def get_live_buses(
    current_admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get live bus tracking data for admin dashboard"""
    repos = get_repositories(db)
    
    # Get all active vehicles with their latest locations
    vehicles = repos.vehicle.get_active_vehicles()
    
    live_buses = []
    for vehicle in vehicles:
        # Get latest location
        latest_location = repos.location.get_latest_location(vehicle.id)
        
        # Get current trip if any
        # This would be implemented in a trip repository
        current_trip = None  # Placeholder
        
        # Calculate status based on location updates
        status = "active"
        if latest_location:
            # If location is older than 5 minutes, mark as stale
            from datetime import datetime, timedelta
            if latest_location.recorded_at < datetime.utcnow() - timedelta(minutes=5):
                status = "stale"
        else:
            status = "offline"
        
        bus_data = {
            "vehicle_id": vehicle.id,
            "vehicle_number": vehicle.vehicle_number,
            "status": status,
            "location": {
                "latitude": latest_location.latitude if latest_location else None,
                "longitude": latest_location.longitude if latest_location else None,
                "speed": latest_location.speed if latest_location else 0,
                "bearing": latest_location.bearing if latest_location else 0,
                "last_update": latest_location.recorded_at.isoformat() if latest_location else None
            },
            "route": {
                "id": current_trip.route_id if current_trip else None,
                "name": "Route Name"  # Would get from route repository
            },
            "occupancy": "medium",  # Placeholder - would get from occupancy reports
            "alerts": []  # Placeholder - would get from alerts system
        }
        live_buses.append(bus_data)
    
    return {
        "buses": live_buses,
        "total_buses": len(vehicles),
        "active_buses": len([b for b in live_buses if b["status"] == "active"]),
        "offline_buses": len([b for b in live_buses if b["status"] == "offline"]),
        "last_updated": datetime.utcnow().isoformat()
    }

@router.get("/dashboard/metrics")
def get_live_metrics(
    current_admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get live operational metrics"""
    repos = get_repositories(db)
    
    # Get basic counts
    total_vehicles = repos.vehicle.count()
    total_routes = repos.route.count()
    total_stops = repos.stop.count()
    
    # Get active counts (simplified - in production would use proper queries)
    active_vehicles = len(repos.vehicle.get_active_vehicles())
    
    # Calculate performance metrics (simplified)
    on_time_percentage = 85.5  # Placeholder
    average_delay = 3.2  # minutes
    
    # Get recent activity counts
    from datetime import datetime, timedelta
    today = datetime.utcnow().date()
    
    # These would be calculated from actual trip and incident data
    trips_today = 245  # Placeholder
    incidents_today = 3  # Placeholder
    
    return {
        "fleet_status": {
            "total_vehicles": total_vehicles,
            "active_vehicles": active_vehicles,
            "maintenance_vehicles": total_vehicles - active_vehicles,
            "utilization_rate": round((active_vehicles / total_vehicles * 100), 1) if total_vehicles > 0 else 0
        },
        "network_status": {
            "total_routes": total_routes,
            "total_stops": total_stops,
            "active_routes": total_routes,  # Simplified
            "coverage_percentage": 92.3  # Placeholder
        },
        "performance_metrics": {
            "on_time_percentage": on_time_percentage,
            "average_delay_minutes": average_delay,
            "trips_completed_today": trips_today,
            "passenger_satisfaction": 4.2  # Placeholder rating
        },
        "alerts_and_incidents": {
            "active_alerts": 2,  # Placeholder
            "incidents_today": incidents_today,
            "emergency_calls": 0,  # Placeholder
            "maintenance_due": 5  # Placeholder
        },
        "real_time_stats": {
            "passengers_in_transit": 1250,  # Placeholder
            "average_occupancy": 68.5,  # Percentage
            "fuel_efficiency": 12.3,  # km/l average
            "carbon_saved_today": 145.7  # kg CO2
        }
    }

@router.get("/dashboard/alerts")
def get_system_alerts(
    current_admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get system alerts and notifications"""
    # This would integrate with various monitoring systems
    alerts = [
        {
            "id": 1,
            "type": "delay",
            "severity": "medium",
            "title": "Route 335E experiencing delays",
            "description": "Average delay of 8 minutes due to traffic congestion",
            "vehicle_id": "KA01AB1234",
            "route_id": 335,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "active"
        },
        {
            "id": 2,
            "type": "maintenance",
            "severity": "low",
            "title": "Vehicle maintenance due",
            "description": "5 vehicles are due for scheduled maintenance",
            "timestamp": datetime.utcnow().isoformat(),
            "status": "pending"
        }
    ]
    
    return {
        "alerts": alerts,
        "total_alerts": len(alerts),
        "critical_alerts": len([a for a in alerts if a["severity"] == "critical"]),
        "active_alerts": len([a for a in alerts if a["status"] == "active"])
    }

@router.get("/dashboard/route-performance")
def get_route_performance(
    current_admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get route performance analytics"""
    repos = get_repositories(db)
    
    routes = repos.route.get_all()
    
    route_performance = []
    for route in routes[:10]:  # Limit to top 10 for demo
        # These metrics would be calculated from actual trip data
        performance = {
            "route_id": route.id,
            "route_number": route.route_number,
            "route_name": route.name,
            "on_time_percentage": round(75 + (route.id % 20), 1),  # Mock data
            "average_delay": round(2 + (route.id % 8), 1),  # Mock data
            "trips_today": 15 + (route.id % 10),  # Mock data
            "passenger_load": round(60 + (route.id % 30), 1),  # Mock data
            "fuel_efficiency": round(10 + (route.id % 5), 1),  # Mock data
            "incidents_count": route.id % 3,  # Mock data
            "status": "active" if route.id % 4 != 0 else "delayed"
        }
        route_performance.append(performance)
    
    return {
        "routes": route_performance,
        "summary": {
            "total_routes": len(routes),
            "routes_on_time": len([r for r in route_performance if r["on_time_percentage"] > 80]),
            "routes_delayed": len([r for r in route_performance if r["status"] == "delayed"]),
            "average_performance": round(sum(r["on_time_percentage"] for r in route_performance) / len(route_performance), 1)
        }
    }

# Admin Roles (for future multi-level admin permissions)
@router.get("/roles", response_model=List[AdminRole])
def list_admin_roles(
    current_admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
) -> Any:
    """List all admin roles"""
    role_repo = AdminRoleRepository(db)
    return role_repo.get_active_roles()

@router.post("/roles", response_model=AdminRole)
def create_admin_role(
    request: Request,
    role_data: AdminRoleCreate,
    current_admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
) -> Any:
    """Create a new admin role"""
    role_repo = AdminRoleRepository(db)
    
    # Check if role name already exists
    existing_role = role_repo.get_by_name(role_data.name)
    if existing_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role name already exists"
        )
    
    role = role_repo.create_role(
        name=role_data.name,
        description=role_data.description,
        permissions=role_data.permissions
    )
    
    log_admin_action(
        request, current_admin, "create_admin_role", "admin_role", role.id,
        details={"name": role.name, "permissions": role.permissions},
        db=db
    )
    
    return role

# Route Management Endpoints
@router.post("/routes", response_model=dict)
def create_route(
    request: Request,
    route_data: RouteCreateRequest,
    current_admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
) -> Any:
    """Create a new route with stops"""
    from ....schemas.admin import RouteCreateRequest
    from ....models.route import Route
    from ....models.stop import Stop
    
    # Check if route number already exists
    existing_route = db.query(Route).filter(Route.route_number == route_data.route_number).first()
    if existing_route:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Route number already exists"
        )
    
    # Validate route data
    validation_result = validate_route_data(route_data, db)
    if not validation_result["is_valid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Route validation failed: {', '.join(validation_result['errors'])}"
        )
    
    # Create route
    route = Route(
        name=route_data.name,
        route_number=route_data.route_number,
        geojson=route_data.geojson,
        polyline=route_data.polyline,
        is_active=route_data.is_active
    )
    
    db.add(route)
    db.flush()  # Get the route ID
    
    # Create stops
    stops_created = []
    for stop_data in route_data.stops:
        stop = Stop(
            route_id=route.id,
            name=stop_data.name,
            name_kannada=stop_data.name_kannada,
            latitude=stop_data.latitude,
            longitude=stop_data.longitude,
            stop_order=stop_data.stop_order
        )
        db.add(stop)
        stops_created.append(stop)
    
    db.commit()
    db.refresh(route)
    
    log_admin_action(
        request, current_admin, "create_route", "route", route.id,
        details={
            "route_number": route.route_number,
            "name": route.name,
            "stops_count": len(stops_created)
        },
        db=db
    )
    
    return {
        "message": "Route created successfully",
        "route": {
            "id": route.id,
            "name": route.name,
            "route_number": route.route_number,
            "stops_count": len(stops_created)
        }
    }

@router.put("/routes/{route_id}", response_model=dict)
def update_route(
    request: Request,
    route_id: int,
    route_data: RouteUpdateRequest,
    current_admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
) -> Any:
    """Update an existing route"""
    from ....schemas.admin import RouteUpdateRequest
    from ....models.route import Route
    
    route = db.query(Route).filter(Route.id == route_id).first()
    if not route:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Route not found"
        )
    
    # Check for route number conflicts
    if route_data.route_number and route_data.route_number != route.route_number:
        existing_route = db.query(Route).filter(
            Route.route_number == route_data.route_number,
            Route.id != route_id
        ).first()
        if existing_route:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Route number already exists"
            )
    
    # Update route fields
    update_data = route_data.dict(exclude_unset=True)
    updated_fields = []
    
    for field, value in update_data.items():
        if hasattr(route, field):
            setattr(route, field, value)
            updated_fields.append(field)
    
    db.commit()
    db.refresh(route)
    
    log_admin_action(
        request, current_admin, "update_route", "route", route.id,
        details={
            "route_number": route.route_number,
            "updated_fields": updated_fields
        },
        db=db
    )
    
    return {
        "message": "Route updated successfully",
        "route": {
            "id": route.id,
            "name": route.name,
            "route_number": route.route_number,
            "updated_fields": updated_fields
        }
    }

@router.delete("/routes/{route_id}")
def delete_route(
    request: Request,
    route_id: int,
    current_admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
) -> Any:
    """Delete a route and all its stops"""
    from ....models.route import Route
    
    route = db.query(Route).filter(Route.id == route_id).first()
    if not route:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Route not found"
        )
    
    # Check if route has active trips (optional business rule)
    # This would prevent deletion of routes with ongoing operations
    
    route_info = {
        "id": route.id,
        "name": route.name,
        "route_number": route.route_number
    }
    
    db.delete(route)
    db.commit()
    
    log_admin_action(
        request, current_admin, "delete_route", "route", route_id,
        details=route_info,
        db=db
    )
    
    return {"message": "Route deleted successfully"}

@router.post("/routes/{route_id}/stops", response_model=dict)
def add_stop_to_route(
    request: Request,
    route_id: int,
    stop_data: RouteStopCreate,
    current_admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
) -> Any:
    """Add a new stop to an existing route"""
    from ....schemas.admin import RouteStopCreate
    from ....models.route import Route
    from ....models.stop import Stop
    
    route = db.query(Route).filter(Route.id == route_id).first()
    if not route:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Route not found"
        )
    
    # Check if stop order conflicts with existing stops
    existing_stop = db.query(Stop).filter(
        Stop.route_id == route_id,
        Stop.stop_order == stop_data.stop_order
    ).first()
    
    if existing_stop:
        # Auto-increment stop orders for existing stops
        db.query(Stop).filter(
            Stop.route_id == route_id,
            Stop.stop_order >= stop_data.stop_order
        ).update({Stop.stop_order: Stop.stop_order + 1})
    
    stop = Stop(
        route_id=route_id,
        name=stop_data.name,
        name_kannada=stop_data.name_kannada,
        latitude=stop_data.latitude,
        longitude=stop_data.longitude,
        stop_order=stop_data.stop_order
    )
    
    db.add(stop)
    db.commit()
    db.refresh(stop)
    
    log_admin_action(
        request, current_admin, "add_stop_to_route", "stop", stop.id,
        details={
            "route_id": route_id,
            "stop_name": stop.name,
            "stop_order": stop.stop_order
        },
        db=db
    )
    
    return {
        "message": "Stop added successfully",
        "stop": {
            "id": stop.id,
            "name": stop.name,
            "stop_order": stop.stop_order
        }
    }

@router.put("/routes/{route_id}/stops/{stop_id}", response_model=dict)
def update_route_stop(
    request: Request,
    route_id: int,
    stop_id: int,
    stop_data: RouteStopUpdate,
    current_admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
) -> Any:
    """Update a stop in a route"""
    from ....schemas.admin import RouteStopUpdate
    from ....models.stop import Stop
    
    stop = db.query(Stop).filter(
        Stop.id == stop_id,
        Stop.route_id == route_id
    ).first()
    
    if not stop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stop not found in this route"
        )
    
    # Handle stop order changes
    if stop_data.stop_order is not None and stop_data.stop_order != stop.stop_order:
        # Check for conflicts and reorder if necessary
        existing_stop = db.query(Stop).filter(
            Stop.route_id == route_id,
            Stop.stop_order == stop_data.stop_order,
            Stop.id != stop_id
        ).first()
        
        if existing_stop:
            # Swap orders
            existing_stop.stop_order = stop.stop_order
    
    # Update stop fields
    update_data = stop_data.dict(exclude_unset=True)
    updated_fields = []
    
    for field, value in update_data.items():
        if hasattr(stop, field):
            setattr(stop, field, value)
            updated_fields.append(field)
    
    db.commit()
    db.refresh(stop)
    
    log_admin_action(
        request, current_admin, "update_route_stop", "stop", stop.id,
        details={
            "route_id": route_id,
            "updated_fields": updated_fields
        },
        db=db
    )
    
    return {
        "message": "Stop updated successfully",
        "stop": {
            "id": stop.id,
            "name": stop.name,
            "stop_order": stop.stop_order,
            "updated_fields": updated_fields
        }
    }

@router.delete("/routes/{route_id}/stops/{stop_id}")
def delete_route_stop(
    request: Request,
    route_id: int,
    stop_id: int,
    current_admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
) -> Any:
    """Delete a stop from a route"""
    from ....models.stop import Stop
    
    stop = db.query(Stop).filter(
        Stop.id == stop_id,
        Stop.route_id == route_id
    ).first()
    
    if not stop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stop not found in this route"
        )
    
    stop_info = {
        "id": stop.id,
        "name": stop.name,
        "stop_order": stop.stop_order
    }
    
    # Reorder remaining stops
    db.query(Stop).filter(
        Stop.route_id == route_id,
        Stop.stop_order > stop.stop_order
    ).update({Stop.stop_order: Stop.stop_order - 1})
    
    db.delete(stop)
    db.commit()
    
    log_admin_action(
        request, current_admin, "delete_route_stop", "stop", stop_id,
        details={**stop_info, "route_id": route_id},
        db=db
    )
    
    return {"message": "Stop deleted successfully"}

@router.post("/routes/{route_id}/reorder-stops", response_model=dict)
def reorder_route_stops(
    request: Request,
    route_id: int,
    reorder_data: RouteStopReorderRequest,
    current_admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
) -> Any:
    """Reorder stops in a route"""
    from ....schemas.admin import RouteStopReorderRequest
    from ....models.route import Route
    from ....models.stop import Stop
    
    route = db.query(Route).filter(Route.id == route_id).first()
    if not route:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Route not found"
        )
    
    # Validate all stop IDs belong to this route
    stop_ids = [item["stop_id"] for item in reorder_data.stop_orders]
    existing_stops = db.query(Stop).filter(
        Stop.route_id == route_id,
        Stop.id.in_(stop_ids)
    ).all()
    
    if len(existing_stops) != len(stop_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Some stop IDs do not belong to this route"
        )
    
    # Update stop orders
    for item in reorder_data.stop_orders:
        db.query(Stop).filter(
            Stop.id == item["stop_id"],
            Stop.route_id == route_id
        ).update({Stop.stop_order: item["new_order"]})
    
    db.commit()
    
    log_admin_action(
        request, current_admin, "reorder_route_stops", "route", route_id,
        details={
            "stop_orders": reorder_data.stop_orders,
            "stops_count": len(stop_ids)
        },
        db=db
    )
    
    return {
        "message": "Stops reordered successfully",
        "updated_stops": len(stop_ids)
    }

@router.post("/routes/validate", response_model=RouteValidationResult)
def validate_route(
    route_data: RouteCreateRequest,
    current_admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
) -> Any:
    """Validate route data without creating it"""
    from ....schemas.admin import RouteCreateRequest, RouteValidationResult
    
    validation_result = validate_route_data(route_data, db)
    return RouteValidationResult(**validation_result)

def validate_route_data(route_data: RouteCreateRequest, db: Session) -> dict:
    """Helper function to validate route data"""
    errors = []
    warnings = []
    conflicts = []
    
    # Check route number uniqueness
    existing_route = db.query(Route).filter(Route.route_number == route_data.route_number).first()
    if existing_route:
        errors.append(f"Route number '{route_data.route_number}' already exists")
    
    # Validate GeoJSON format
    try:
        import json
        geojson_data = json.loads(route_data.geojson)
        if geojson_data.get("type") not in ["LineString", "MultiLineString"]:
            warnings.append("GeoJSON should be LineString or MultiLineString for routes")
    except json.JSONDecodeError:
        errors.append("Invalid GeoJSON format")
    
    # Validate stops
    if route_data.stops:
        stop_orders = [stop.stop_order for stop in route_data.stops]
        if len(stop_orders) != len(set(stop_orders)):
            errors.append("Duplicate stop orders found")
        
        # Check for stops too close to each other
        for i, stop1 in enumerate(route_data.stops):
            for j, stop2 in enumerate(route_data.stops[i+1:], i+1):
                distance = calculate_distance(
                    stop1.latitude, stop1.longitude,
                    stop2.latitude, stop2.longitude
                )
                if distance < 0.1:  # Less than 100 meters
                    warnings.append(f"Stops '{stop1.name}' and '{stop2.name}' are very close ({distance:.0f}m)")
    
    # Check for route conflicts (overlapping routes)
    # This would involve more complex geospatial analysis
    
    return {
        "is_valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "conflicts": conflicts
    }

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points in kilometers using Haversine formula"""
    import math
    
    R = 6371  # Earth's radius in kilometers
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = (math.sin(delta_lat / 2) ** 2 +
         math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c * 1000  # Convert to meters

# Bulk Operations Endpoints
@router.post("/routes/bulk-import", response_model=dict)
def bulk_import_routes(
    request: Request,
    import_data: BulkRouteImport,
    current_admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
) -> Any:
    """Bulk import routes from CSV or GeoJSON"""
    from ....schemas.admin import BulkRouteImport
    import csv
    import json
    from io import StringIO
    
    try:
        imported_count = 0
        errors = []
        warnings = []
        
        if import_data.format == 'csv':
            # Parse CSV data
            csv_reader = csv.DictReader(StringIO(import_data.data))
            routes_to_import = []
            
            for row_num, row in enumerate(csv_reader, 1):
                try:
                    # Validate required fields
                    required_fields = ['name', 'route_number', 'geojson', 'polyline']
                    missing_fields = [field for field in required_fields if not row.get(field)]
                    
                    if missing_fields:
                        errors.append(f"Row {row_num}: Missing fields: {', '.join(missing_fields)}")
                        continue
                    
                    # Check if route already exists
                    existing_route = db.query(Route).filter(Route.route_number == row['route_number']).first()
                    if existing_route and not import_data.overwrite_existing:
                        warnings.append(f"Row {row_num}: Route {row['route_number']} already exists, skipping")
                        continue
                    
                    route_data = {
                        'name': row['name'],
                        'route_number': row['route_number'],
                        'geojson': row['geojson'],
                        'polyline': row['polyline'],
                        'is_active': row.get('is_active', 'true').lower() == 'true'
                    }
                    
                    routes_to_import.append((route_data, existing_route))
                    
                except Exception as e:
                    errors.append(f"Row {row_num}: {str(e)}")
        
        elif import_data.format == 'geojson':
            # Parse GeoJSON data
            try:
                geojson_data = json.loads(import_data.data)
                
                if geojson_data.get('type') == 'FeatureCollection':
                    features = geojson_data.get('features', [])
                elif geojson_data.get('type') == 'Feature':
                    features = [geojson_data]
                else:
                    errors.append("Invalid GeoJSON format: must be Feature or FeatureCollection")
                    features = []
                
                routes_to_import = []
                for i, feature in enumerate(features):
                    try:
                        properties = feature.get('properties', {})
                        geometry = feature.get('geometry', {})
                        
                        # Extract route information from properties
                        name = properties.get('name') or properties.get('route_name')
                        route_number = properties.get('route_number') or properties.get('number')
                        
                        if not name or not route_number:
                            errors.append(f"Feature {i+1}: Missing name or route_number in properties")
                            continue
                        
                        # Check if route already exists
                        existing_route = db.query(Route).filter(Route.route_number == route_number).first()
                        if existing_route and not import_data.overwrite_existing:
                            warnings.append(f"Feature {i+1}: Route {route_number} already exists, skipping")
                            continue
                        
                        # Generate polyline from geometry (simplified)
                        polyline = json.dumps(geometry)
                        
                        route_data = {
                            'name': name,
                            'route_number': route_number,
                            'geojson': json.dumps(geometry),
                            'polyline': polyline,
                            'is_active': properties.get('is_active', True)
                        }
                        
                        routes_to_import.append((route_data, existing_route))
                        
                    except Exception as e:
                        errors.append(f"Feature {i+1}: {str(e)}")
                        
            except json.JSONDecodeError as e:
                errors.append(f"Invalid JSON format: {str(e)}")
                routes_to_import = []
        
        # If validation only, return results without importing
        if import_data.validate_only:
            return {
                "success": len(errors) == 0,
                "imported_count": len(routes_to_import),
                "errors": errors,
                "warnings": warnings
            }
        
        # Import routes if no critical errors
        if len(errors) == 0:
            for route_data, existing_route in routes_to_import:
                try:
                    if existing_route and import_data.overwrite_existing:
                        # Update existing route
                        for field, value in route_data.items():
                            setattr(existing_route, field, value)
                        db.commit()
                    else:
                        # Create new route
                        route = Route(**route_data)
                        db.add(route)
                        db.flush()
                    
                    imported_count += 1
                    
                except Exception as e:
                    errors.append(f"Failed to import route {route_data['route_number']}: {str(e)}")
            
            if imported_count > 0:
                db.commit()
        
        log_admin_action(
            request, current_admin, "bulk_import_routes", "route",
            details={
                "format": import_data.format,
                "imported_count": imported_count,
                "errors_count": len(errors),
                "warnings_count": len(warnings)
            },
            db=db
        )
        
        return {
            "success": len(errors) == 0,
            "imported_count": imported_count,
            "errors": errors,
            "warnings": warnings
        }
        
    except Exception as e:
        return {
            "success": False,
            "imported_count": 0,
            "errors": [f"Import failed: {str(e)}"],
            "warnings": []
        }

@router.post("/routes/bulk-export")
def bulk_export_routes(
    request: Request,
    export_data: BulkRouteExport,
    current_admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
) -> Any:
    """Bulk export routes to CSV, GeoJSON, or JSON"""
    from ....schemas.admin import BulkRouteExport
    from fastapi.responses import StreamingResponse
    import csv
    import json
    from io import StringIO
    
    try:
        # Build query
        query = db.query(Route)
        
        if export_data.route_ids:
            query = query.filter(Route.id.in_(export_data.route_ids))
        
        if not export_data.include_inactive:
            query = query.filter(Route.is_active == True)
        
        routes = query.all()
        
        if export_data.format == 'csv':
            # Generate CSV
            output = StringIO()
            fieldnames = ['id', 'name', 'route_number', 'geojson', 'polyline', 'is_active', 'created_at']
            
            if export_data.include_stops:
                fieldnames.extend(['stops_count', 'stops_data'])
            
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            
            for route in routes:
                row_data = {
                    'id': route.id,
                    'name': route.name,
                    'route_number': route.route_number,
                    'geojson': route.geojson,
                    'polyline': route.polyline,
                    'is_active': route.is_active,
                    'created_at': route.created_at.isoformat()
                }
                
                if export_data.include_stops:
                    stops = db.query(Stop).filter(Stop.route_id == route.id).order_by(Stop.stop_order).all()
                    row_data['stops_count'] = len(stops)
                    row_data['stops_data'] = json.dumps([{
                        'name': stop.name,
                        'name_kannada': stop.name_kannada,
                        'latitude': float(stop.latitude),
                        'longitude': float(stop.longitude),
                        'stop_order': stop.stop_order
                    } for stop in stops])
                
                writer.writerow(row_data)
            
            content = output.getvalue()
            media_type = 'text/csv'
            
        elif export_data.format == 'geojson':
            # Generate GeoJSON
            features = []
            
            for route in routes:
                try:
                    geometry = json.loads(route.geojson)
                except json.JSONDecodeError:
                    # Fallback to simple geometry
                    geometry = {"type": "LineString", "coordinates": []}
                
                properties = {
                    'id': route.id,
                    'name': route.name,
                    'route_number': route.route_number,
                    'is_active': route.is_active,
                    'created_at': route.created_at.isoformat()
                }
                
                if export_data.include_stops:
                    stops = db.query(Stop).filter(Stop.route_id == route.id).order_by(Stop.stop_order).all()
                    properties['stops'] = [{
                        'name': stop.name,
                        'name_kannada': stop.name_kannada,
                        'latitude': float(stop.latitude),
                        'longitude': float(stop.longitude),
                        'stop_order': stop.stop_order
                    } for stop in stops]
                
                feature = {
                    'type': 'Feature',
                    'geometry': geometry,
                    'properties': properties
                }
                features.append(feature)
            
            geojson_data = {
                'type': 'FeatureCollection',
                'features': features
            }
            
            content = json.dumps(geojson_data, indent=2)
            media_type = 'application/geo+json'
            
        else:  # JSON format
            # Generate JSON
            routes_data = []
            
            for route in routes:
                route_data = {
                    'id': route.id,
                    'name': route.name,
                    'route_number': route.route_number,
                    'geojson': route.geojson,
                    'polyline': route.polyline,
                    'is_active': route.is_active,
                    'created_at': route.created_at.isoformat()
                }
                
                if export_data.include_stops:
                    stops = db.query(Stop).filter(Stop.route_id == route.id).order_by(Stop.stop_order).all()
                    route_data['stops'] = [{
                        'id': stop.id,
                        'name': stop.name,
                        'name_kannada': stop.name_kannada,
                        'latitude': float(stop.latitude),
                        'longitude': float(stop.longitude),
                        'stop_order': stop.stop_order
                    } for stop in stops]
                
                routes_data.append(route_data)
            
            content = json.dumps({
                'routes': routes_data,
                'exported_at': datetime.utcnow().isoformat(),
                'total_routes': len(routes_data)
            }, indent=2)
            media_type = 'application/json'
        
        log_admin_action(
            request, current_admin, "bulk_export_routes", "route",
            details={
                "format": export_data.format,
                "routes_count": len(routes),
                "include_stops": export_data.include_stops
            },
            db=db
        )
        
        # Return file as download
        return StreamingResponse(
            StringIO(content),
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename=routes_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.{export_data.format}"
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export failed: {str(e)}"
        )