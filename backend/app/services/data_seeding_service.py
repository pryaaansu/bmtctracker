"""
Data Seeding Service

Integrates the mock data generator with the database to populate realistic BMTC data.
"""

from typing import List, Dict
from sqlalchemy.orm import Session
from ..models.route import Route
from ..models.stop import Stop
from ..models.vehicle import Vehicle, VehicleStatus
from ..models.driver import Driver
from ..models.trip import Trip, TripStatus
from .mock_data_generator import MockDataGenerator, BusMovementConfig
import random
from datetime import datetime, timedelta

class DataSeedingService:
    """Service to seed database with realistic BMTC data"""
    
    def __init__(self, db: Session):
        self.db = db
        self.mock_generator = MockDataGenerator()
    
    def seed_routes_and_stops(self, num_routes: int = 20) -> List[Route]:
        """Seed database with realistic routes and stops"""
        # Generate mock routes
        mock_routes = self.mock_generator.generate_realistic_routes(num_routes)
        
        created_routes = []
        
        for mock_route in mock_routes:
            # Create route
            route = Route(
                name=mock_route["name"],
                route_number=mock_route["route_number"],
                geojson=mock_route["geojson"],
                polyline=mock_route["polyline"],
                is_active=mock_route["is_active"]
            )
            
            self.db.add(route)
            self.db.flush()  # Get the route ID
            
            # Create stops for this route
            for stop_data in mock_route["stops"]:
                stop = Stop(
                    route_id=route.id,
                    name=stop_data["name"],
                    name_kannada=stop_data["name_kannada"],
                    latitude=stop_data["latitude"],
                    longitude=stop_data["longitude"],
                    stop_order=stop_data["stop_order"]
                )
                self.db.add(stop)
            
            created_routes.append(route)
        
        self.db.commit()
        return created_routes
    
    def seed_vehicles(self, num_vehicles: int = 50) -> List[Vehicle]:
        """Seed database with vehicles"""
        vehicles = []
        
        for i in range(1, num_vehicles + 1):
            # Generate realistic BMTC vehicle numbers
            vehicle_number = f"KA-01-F-{i:04d}"
            
            vehicle = Vehicle(
                vehicle_number=vehicle_number,
                capacity=random.choice([40, 45, 50, 55, 60]),  # Typical bus capacities
                status=random.choices(
                    [VehicleStatus.ACTIVE, VehicleStatus.MAINTENANCE, VehicleStatus.OFFLINE],
                    weights=[0.85, 0.10, 0.05]
                )[0]
            )
            
            self.db.add(vehicle)
            vehicles.append(vehicle)
        
        self.db.commit()
        return vehicles
    
    def seed_drivers(self, num_drivers: int = 60) -> List[Driver]:
        """Seed database with drivers"""
        drivers = []
        
        # Common Indian names for realistic data
        first_names = [
            "Rajesh", "Suresh", "Mahesh", "Ramesh", "Ganesh", "Naresh", "Dinesh",
            "Prakash", "Ashok", "Vinod", "Manoj", "Anil", "Sunil", "Ravi",
            "Kumar", "Mohan", "Rohan", "Sohan", "Gopal", "Kishore"
        ]
        
        last_names = [
            "Kumar", "Sharma", "Reddy", "Rao", "Gowda", "Nair", "Iyer",
            "Singh", "Gupta", "Agarwal", "Jain", "Patel", "Shah", "Mehta",
            "Verma", "Mishra", "Tiwari", "Pandey", "Srivastava", "Tripathi"
        ]
        
        for i in range(1, num_drivers + 1):
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            full_name = f"{first_name} {last_name}"
            
            # Generate realistic phone numbers
            phone = f"+91-{random.randint(7000000000, 9999999999)}"
            
            # Generate license numbers
            license_number = f"KA{random.randint(10, 99)}{random.randint(1000000000, 9999999999)}"
            
            driver = Driver(
                name=full_name,
                phone=phone,
                license_number=license_number,
                status=random.choices(
                    ["active", "inactive", "on_break"],
                    weights=[0.8, 0.1, 0.1]
                )[0]
            )
            
            self.db.add(driver)
            drivers.append(driver)
        
        self.db.commit()
        return drivers
    
    def assign_drivers_to_vehicles(self):
        """Assign drivers to vehicles"""
        vehicles = self.db.query(Vehicle).filter(Vehicle.status == VehicleStatus.ACTIVE).all()
        drivers = self.db.query(Driver).filter(Driver.status == "active").all()
        
        # Shuffle for random assignment
        random.shuffle(drivers)
        
        for i, vehicle in enumerate(vehicles):
            if i < len(drivers):
                driver = drivers[i]
                driver.assigned_vehicle_id = vehicle.id
        
        self.db.commit()
    
    def seed_active_trips(self, num_trips: int = 30) -> List[Trip]:
        """Seed database with active trips"""
        routes = self.db.query(Route).filter(Route.is_active == True).all()
        vehicles = self.db.query(Vehicle).filter(Vehicle.status == VehicleStatus.ACTIVE).all()
        drivers = self.db.query(Driver).filter(Driver.status == "active").all()
        
        if not routes or not vehicles or not drivers:
            raise ValueError("Need routes, vehicles, and drivers to create trips")
        
        trips = []
        
        for i in range(num_trips):
            route = random.choice(routes)
            vehicle = random.choice(vehicles)
            driver = random.choice(drivers)
            
            # Create trip starting within the last 2 hours
            start_time = datetime.now() - timedelta(minutes=random.randint(0, 120))
            
            trip = Trip(
                vehicle_id=vehicle.id,
                route_id=route.id,
                driver_id=driver.id,
                start_time=start_time,
                status=TripStatus.ACTIVE
            )
            
            self.db.add(trip)
            trips.append(trip)
        
        self.db.commit()
        return trips
    
    def get_mock_generator(self) -> MockDataGenerator:
        """Get the mock data generator instance"""
        return self.mock_generator
    
    def seed_all_data(self, num_routes: int = 20, num_vehicles: int = 50, 
                     num_drivers: int = 60, num_trips: int = 30) -> Dict:
        """Seed all data in the correct order"""
        print("Seeding routes and stops...")
        routes = self.seed_routes_and_stops(num_routes)
        
        print("Seeding vehicles...")
        vehicles = self.seed_vehicles(num_vehicles)
        
        print("Seeding drivers...")
        drivers = self.seed_drivers(num_drivers)
        
        print("Assigning drivers to vehicles...")
        self.assign_drivers_to_vehicles()
        
        print("Creating active trips...")
        trips = self.seed_active_trips(num_trips)
        
        return {
            "routes": len(routes),
            "vehicles": len(vehicles),
            "drivers": len(drivers),
            "trips": len(trips),
            "total_stops": sum(len(route.stops) for route in routes)
        }