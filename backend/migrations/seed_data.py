"""
Seed data generator for BMTC Transport Tracker
Uses the MockDataGenerator for realistic route and bus data
"""
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models import (
    Vehicle, Driver, Route, Stop, Trip, VehicleLocation, 
    Subscription, VehicleStatus, DriverStatus, TripStatus, NotificationChannel
)
from app.services.data_seeding_service import DataSeedingService
from datetime import datetime, timedelta
import logging
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_sample_routes(db: Session):
    """Create sample BMTC routes"""
    routes_data = [
        {
            "name": "Majestic - Electronic City",
            "route_number": "335E",
            "geojson": '{"type":"LineString","coordinates":[[77.5946,12.9716],[77.6648,12.8456]]}',
            "polyline": "encoded_polyline_data_1"
        },
        {
            "name": "Majestic - Whitefield", 
            "route_number": "500D",
            "geojson": '{"type":"LineString","coordinates":[[77.5946,12.9716],[77.7499,12.9698]]}',
            "polyline": "encoded_polyline_data_2"
        },
        {
            "name": "Banashankari - Hebbal",
            "route_number": "201",
            "geojson": '{"type":"LineString","coordinates":[[77.5568,12.9249],[77.5946,13.0358]]}',
            "polyline": "encoded_polyline_data_3"
        },
        {
            "name": "KR Puram - Mysore Road",
            "route_number": "365",
            "geojson": '{"type":"LineString","coordinates":[[77.7499,12.9698],[77.5568,12.9249]]}',
            "polyline": "encoded_polyline_data_4"
        },
        {
            "name": "Yeshwantpur - Koramangala",
            "route_number": "201A",
            "geojson": '{"type":"LineString","coordinates":[[77.5385,13.0280],[77.6279,12.9279]]}',
            "polyline": "encoded_polyline_data_5"
        }
    ]
    
    routes = []
    for route_data in routes_data:
        route = Route(**route_data)
        db.add(route)
        routes.append(route)
    
    db.commit()
    logger.info(f"Created {len(routes)} sample routes")
    return routes

def create_sample_vehicles(db: Session):
    """Create sample vehicles"""
    vehicles_data = [
        {"vehicle_number": "KA01-1234", "capacity": 40, "status": VehicleStatus.ACTIVE},
        {"vehicle_number": "KA01-5678", "capacity": 40, "status": VehicleStatus.ACTIVE},
        {"vehicle_number": "KA01-9012", "capacity": 35, "status": VehicleStatus.ACTIVE},
        {"vehicle_number": "KA01-3456", "capacity": 40, "status": VehicleStatus.MAINTENANCE},
        {"vehicle_number": "KA01-7890", "capacity": 35, "status": VehicleStatus.ACTIVE},
        {"vehicle_number": "KA02-1111", "capacity": 45, "status": VehicleStatus.ACTIVE},
        {"vehicle_number": "KA02-2222", "capacity": 40, "status": VehicleStatus.ACTIVE},
        {"vehicle_number": "KA02-3333", "capacity": 35, "status": VehicleStatus.OFFLINE},
    ]
    
    vehicles = []
    for vehicle_data in vehicles_data:
        vehicle = Vehicle(**vehicle_data)
        db.add(vehicle)
        vehicles.append(vehicle)
    
    db.commit()
    logger.info(f"Created {len(vehicles)} sample vehicles")
    return vehicles

def create_sample_drivers(db: Session, vehicles):
    """Create sample drivers"""
    drivers_data = [
        {"name": "Rajesh Kumar", "phone": "+919876543210", "license_number": "KA0120230001", "status": DriverStatus.ACTIVE},
        {"name": "Suresh Babu", "phone": "+919876543211", "license_number": "KA0120230002", "status": DriverStatus.ACTIVE},
        {"name": "Mahesh Gowda", "phone": "+919876543212", "license_number": "KA0120230003", "status": DriverStatus.ACTIVE},
        {"name": "Ramesh Reddy", "phone": "+919876543213", "license_number": "KA0120230004", "status": DriverStatus.INACTIVE},
        {"name": "Ganesh Rao", "phone": "+919876543214", "license_number": "KA0120230005", "status": DriverStatus.ACTIVE},
        {"name": "Prakash Shetty", "phone": "+919876543215", "license_number": "KA0120230006", "status": DriverStatus.ACTIVE},
        {"name": "Venkatesh Naik", "phone": "+919876543216", "license_number": "KA0120230007", "status": DriverStatus.ON_BREAK},
    ]
    
    drivers = []
    active_vehicles = [v for v in vehicles if v.status == VehicleStatus.ACTIVE]
    
    for i, driver_data in enumerate(drivers_data):
        # Assign vehicles to active drivers
        if i < len(active_vehicles) and driver_data["status"] == DriverStatus.ACTIVE:
            driver_data["assigned_vehicle_id"] = active_vehicles[i].id
        
        driver = Driver(**driver_data)
        db.add(driver)
        drivers.append(driver)
    
    db.commit()
    logger.info(f"Created {len(drivers)} sample drivers")
    return drivers

def create_sample_stops(db: Session, routes):
    """Create sample bus stops for routes"""
    stops_data = {
        1: [  # Majestic - Electronic City
            {"name": "Majestic Bus Station", "name_kannada": "ಮೆಜೆಸ್ಟಿಕ್ ಬಸ್ ನಿಲ್ದಾಣ", "latitude": 12.9716, "longitude": 77.5946, "stop_order": 1},
            {"name": "Town Hall", "name_kannada": "ಟೌನ್ ಹಾಲ್", "latitude": 12.9667, "longitude": 77.5964, "stop_order": 2},
            {"name": "Corporation Circle", "name_kannada": "ಕಾರ್ಪೊರೇಷನ್ ಸರ್ಕಲ್", "latitude": 12.9611, "longitude": 77.6017, "stop_order": 3},
            {"name": "Lalbagh West Gate", "name_kannada": "ಲಾಲ್ಬಾಗ್ ಪಶ್ಚಿಮ ಗೇಟ್", "latitude": 12.9507, "longitude": 77.5848, "stop_order": 4},
            {"name": "Jayanagar 4th Block", "name_kannada": "ಜಯನಗರ 4ನೇ ಬ್ಲಾಕ್", "latitude": 12.9279, "longitude": 77.5937, "stop_order": 5},
            {"name": "BTM Layout", "name_kannada": "ಬಿಟಿಎಂ ಲೇಔಟ್", "latitude": 12.9165, "longitude": 77.6101, "stop_order": 6},
            {"name": "Silk Board", "name_kannada": "ಸಿಲ್ಕ್ ಬೋರ್ಡ್", "latitude": 12.9077, "longitude": 77.6226, "stop_order": 7},
            {"name": "Electronic City", "name_kannada": "ಎಲೆಕ್ಟ್ರಾನಿಕ್ ಸಿಟಿ", "latitude": 12.8456, "longitude": 77.6648, "stop_order": 8},
        ],
        2: [  # Majestic - Whitefield
            {"name": "Majestic Bus Station", "name_kannada": "ಮೆಜೆಸ್ಟಿಕ್ ಬಸ್ ನಿಲ್ದಾಣ", "latitude": 12.9716, "longitude": 77.5946, "stop_order": 1},
            {"name": "Shivaji Nagar", "name_kannada": "ಶಿವಾಜಿ ನಗರ", "latitude": 12.9895, "longitude": 77.6006, "stop_order": 2},
            {"name": "Cantonment Railway Station", "name_kannada": "ಕ್ಯಾಂಟೋನ್ಮೆಂಟ್ ರೈಲ್ವೇ ನಿಲ್ದಾಣ", "latitude": 12.9845, "longitude": 77.6108, "stop_order": 3},
            {"name": "MG Road", "name_kannada": "ಎಂಜಿ ರೋಡ್", "latitude": 12.9759, "longitude": 77.6063, "stop_order": 4},
            {"name": "Indiranagar", "name_kannada": "ಇಂದಿರಾನಗರ", "latitude": 12.9719, "longitude": 77.6412, "stop_order": 5},
            {"name": "Marathahalli", "name_kannada": "ಮರಾಠಹಳ್ಳಿ", "latitude": 12.9591, "longitude": 77.6974, "stop_order": 6},
            {"name": "Brookefield", "name_kannada": "ಬ್ರೂಕ್‌ಫೀಲ್ಡ್", "latitude": 12.9698, "longitude": 77.7138, "stop_order": 7},
            {"name": "Whitefield", "name_kannada": "ವೈಟ್‌ಫೀಲ್ಡ್", "latitude": 12.9698, "longitude": 77.7499, "stop_order": 8},
        ],
        3: [  # Banashankari - Hebbal
            {"name": "Banashankari", "name_kannada": "ಬನಶಂಕರಿ", "latitude": 12.9249, "longitude": 77.5568, "stop_order": 1},
            {"name": "JP Nagar", "name_kannada": "ಜೆಪಿ ನಗರ", "latitude": 12.9081, "longitude": 77.5831, "stop_order": 2},
            {"name": "Jayanagar", "name_kannada": "ಜಯನಗರ", "latitude": 12.9279, "longitude": 77.5937, "stop_order": 3},
            {"name": "Lalbagh", "name_kannada": "ಲಾಲ್ಬಾಗ್", "latitude": 12.9507, "longitude": 77.5848, "stop_order": 4},
            {"name": "Vidhana Soudha", "name_kannada": "ವಿಧಾನ ಸೌಧ", "latitude": 12.9796, "longitude": 77.5910, "stop_order": 5},
            {"name": "Cubbon Park", "name_kannada": "ಕಬ್ಬನ್ ಪಾರ್ಕ್", "latitude": 12.9718, "longitude": 77.5946, "stop_order": 6},
            {"name": "Cantonment", "name_kannada": "ಕ್ಯಾಂಟೋನ್ಮೆಂಟ್", "latitude": 12.9845, "longitude": 77.6108, "stop_order": 7},
            {"name": "Hebbal", "name_kannada": "ಹೆಬ್ಬಾಳ್", "latitude": 13.0358, "longitude": 77.5946, "stop_order": 8},
        ]
    }
    
    all_stops = []
    for route in routes[:3]:  # Only create stops for first 3 routes
        if route.id in stops_data:
            for stop_data in stops_data[route.id]:
                stop_data["route_id"] = route.id
                stop = Stop(**stop_data)
                db.add(stop)
                all_stops.append(stop)
    
    db.commit()
    logger.info(f"Created {len(all_stops)} sample stops")
    return all_stops

def create_sample_trips(db: Session, vehicles, routes, drivers):
    """Create sample trips"""
    active_vehicles = [v for v in vehicles if v.status == VehicleStatus.ACTIVE]
    active_drivers = [d for d in drivers if d.status == DriverStatus.ACTIVE]
    
    trips = []
    for i in range(min(5, len(active_vehicles), len(active_drivers))):
        trip = Trip(
            vehicle_id=active_vehicles[i].id,
            route_id=routes[i % len(routes)].id,
            driver_id=active_drivers[i].id,
            start_time=datetime.now() - timedelta(minutes=random.randint(15, 60)),
            status=TripStatus.ACTIVE
        )
        db.add(trip)
        trips.append(trip)
    
    db.commit()
    logger.info(f"Created {len(trips)} sample trips")
    return trips

def create_sample_locations(db: Session, vehicles):
    """Create sample vehicle locations"""
    # Sample locations around Bangalore
    sample_locations = [
        (12.9279, 77.5937),  # Jayanagar
        (12.9591, 77.6974),  # Marathahalli
        (12.9507, 77.5848),  # Lalbagh
        (12.9716, 77.5946),  # Majestic
        (12.9845, 77.6108),  # Cantonment
    ]
    
    locations = []
    active_vehicles = [v for v in vehicles if v.status == VehicleStatus.ACTIVE]
    
    for i, vehicle in enumerate(active_vehicles[:5]):
        lat, lng = sample_locations[i % len(sample_locations)]
        location = VehicleLocation(
            vehicle_id=vehicle.id,
            latitude=lat,
            longitude=lng,
            speed=random.uniform(15.0, 35.0),
            bearing=random.randint(0, 359),
            recorded_at=datetime.now() - timedelta(seconds=random.randint(30, 300))
        )
        db.add(location)
        locations.append(location)
    
    db.commit()
    logger.info(f"Created {len(locations)} sample vehicle locations")
    return locations

def create_sample_subscriptions(db: Session, stops):
    """Create sample subscriptions"""
    subscriptions_data = [
        {"phone": "+919876543210", "channel": NotificationChannel.SMS, "eta_threshold": 5},
        {"phone": "+919876543211", "channel": NotificationChannel.WHATSAPP, "eta_threshold": 3},
        {"phone": "+919876543212", "channel": NotificationChannel.VOICE, "eta_threshold": 10},
        {"phone": "+919876543213", "channel": NotificationChannel.PUSH, "eta_threshold": 7},
        {"phone": "+919876543214", "channel": NotificationChannel.SMS, "eta_threshold": 5},
    ]
    
    subscriptions = []
    for i, sub_data in enumerate(subscriptions_data):
        if i < len(stops):
            sub_data["stop_id"] = stops[i].id
            subscription = Subscription(**sub_data)
            db.add(subscription)
            subscriptions.append(subscription)
    
    db.commit()
    logger.info(f"Created {len(subscriptions)} sample subscriptions")
    return subscriptions

def create_sample_locations_with_mock_generator(db: Session, vehicles, mock_generator):
    """Create sample vehicle locations using the mock generator"""
    locations = []
    routes = db.query(Route).filter(Route.is_active == True).all()
    
    for i, vehicle in enumerate(vehicles):
        if i < len(routes):
            route = routes[i]
            # Generate initial location for this vehicle on this route
            try:
                location_data = mock_generator.generate_bus_movements(
                    route.route_number, 
                    vehicle.id
                )
                
                location = VehicleLocation(
                    vehicle_id=vehicle.id,
                    latitude=location_data["latitude"],
                    longitude=location_data["longitude"],
                    speed=location_data["speed"],
                    bearing=location_data["bearing"],
                    recorded_at=datetime.now()
                )
                db.add(location)
                locations.append(location)
            except Exception as e:
                logger.warning(f"Could not generate location for vehicle {vehicle.id}: {e}")
    
    db.commit()
    logger.info(f"Created {len(locations)} sample vehicle locations using mock generator")
    return locations

def seed_database():
    """Main function to seed the database with realistic BMTC data"""
    db = SessionLocal()
    try:
        logger.info("Starting database seeding with realistic BMTC data...")
        
        # Use the new data seeding service
        seeding_service = DataSeedingService(db)
        
        # Seed all data using the mock generator
        result = seeding_service.seed_all_data(
            num_routes=20,
            num_vehicles=50,
            num_drivers=60,
            num_trips=30
        )
        
        logger.info(f"Database seeding completed successfully!")
        logger.info(f"Created: {result['routes']} routes, {result['vehicles']} vehicles, "
                   f"{result['drivers']} drivers, {result['trips']} trips, "
                   f"{result['total_stops']} stops")
        
        # Create some sample subscriptions
        stops = db.query(Stop).limit(10).all()
        create_sample_subscriptions(db, stops)
        
        # Create some initial vehicle locations
        vehicles = db.query(Vehicle).filter(Vehicle.status == VehicleStatus.ACTIVE).limit(10).all()
        create_sample_locations_with_mock_generator(db, vehicles, seeding_service.get_mock_generator())
        
        return True
        
    except Exception as e:
        logger.error(f"Error seeding database: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()