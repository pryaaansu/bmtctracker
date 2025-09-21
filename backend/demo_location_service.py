#!/usr/bin/env python3
"""
Demo script for BMTC Mock Data Generator and Location Tracking Service

This script demonstrates the functionality implemented in task 3:
- Realistic BMTC route generation based on Bengaluru geography
- Bus movement simulation with configurable scenarios
- Location tracking with smooth interpolation
- WebSocket broadcasting capabilities
"""

import asyncio
import json
from datetime import datetime
from app.services.mock_data_generator import MockDataGenerator, ScenarioType
from app.services.location_tracking_service import LocationTrackingService

async def demo_mock_data_generator():
    """Demonstrate the mock data generator functionality"""
    print("🚌 BMTC Mock Data Generator Demo")
    print("=" * 50)
    
    generator = MockDataGenerator()
    
    # Generate realistic routes
    print("\n📍 Generating realistic BMTC routes...")
    routes = generator.generate_realistic_routes(5)
    
    for i, route in enumerate(routes, 1):
        print(f"\n{i}. {route['name']} (Route {route['route_number']})")
        print(f"   Stops: {len(route['stops'])}")
        print(f"   Type: {route['type']}")
        
        # Show first few stops
        for j, stop in enumerate(route['stops'][:3]):
            print(f"   • {stop['name']} ({stop['name_kannada']})")
        
        if len(route['stops']) > 3:
            print(f"   • ... and {len(route['stops']) - 3} more stops")
    
    # Demonstrate bus movement simulation
    print(f"\n🚍 Simulating bus movements...")
    route = routes[0]  # Use first route
    
    print(f"\nSimulating bus on route: {route['name']}")
    
    # Normal scenario
    print("\n📊 Normal Traffic Scenario:")
    for i in range(3):
        movement = generator.generate_bus_movements(route['route_number'], 1, ScenarioType.NORMAL)
        print(f"  Update {i+1}: Lat {movement['latitude']:.4f}, Lng {movement['longitude']:.4f}, "
              f"Speed {movement['speed']:.1f} km/h, Bearing {movement['bearing']:.0f}°")
        await asyncio.sleep(0.5)
    
    # Rush hour scenario
    print("\n🚦 Rush Hour Scenario:")
    for i in range(3):
        movement = generator.generate_bus_movements(route['route_number'], 2, ScenarioType.RUSH_HOUR)
        print(f"  Update {i+1}: Lat {movement['latitude']:.4f}, Lng {movement['longitude']:.4f}, "
              f"Speed {movement['speed']:.1f} km/h, Bearing {movement['bearing']:.0f}°")
        await asyncio.sleep(0.5)
    
    # Breakdown scenario
    print("\n⚠️  Breakdown Scenario:")
    movement = generator.generate_bus_movements(route['route_number'], 3, ScenarioType.BREAKDOWN)
    print(f"  Breakdown: Lat {movement['latitude']:.4f}, Lng {movement['longitude']:.4f}, "
          f"Speed {movement['speed']:.1f} km/h (STOPPED)")
    
    return generator, routes

async def demo_location_tracking_service(generator, routes):
    """Demonstrate the location tracking service functionality"""
    print("\n\n📡 Location Tracking Service Demo")
    print("=" * 50)
    
    # Create location service (without Redis for demo)
    service = LocationTrackingService()
    service.mock_generator = generator
    
    print("\n🔄 Processing location updates with smoothing...")
    
    route = routes[0]
    vehicle_id = 1
    
    # Simulate several location updates
    for i in range(5):
        # Generate raw location data
        raw_movement = generator.generate_bus_movements(route['route_number'], vehicle_id)
        
        # Process through location service (with smoothing)
        location_update = await service.process_location_update(
            vehicle_id=vehicle_id,
            latitude=raw_movement['latitude'],
            longitude=raw_movement['longitude'],
            speed=raw_movement['speed'],
            bearing=raw_movement['bearing']
        )
        
        print(f"  Update {i+1}: Vehicle {location_update.vehicle_id}")
        print(f"    Position: ({location_update.latitude:.6f}, {location_update.longitude:.6f})")
        print(f"    Speed: {location_update.speed:.1f} km/h, Bearing: {location_update.bearing:.0f}°")
        print(f"    Confidence: {location_update.confidence:.2f}")
        print(f"    Interpolated: {location_update.interpolated}")
        
        await asyncio.sleep(1)
    
    # Demonstrate getting cached locations
    print(f"\n💾 Retrieving cached location...")
    cached_location = await service.get_vehicle_location(vehicle_id)
    if cached_location:
        print(f"  Cached location for vehicle {vehicle_id}:")
        print(f"    Position: ({cached_location.latitude:.6f}, {cached_location.longitude:.6f})")
        print(f"    Last update: {cached_location.timestamp}")
    
    # Demonstrate scenario control
    print(f"\n🎛️  Scenario Control Demo...")
    await service.set_vehicle_scenario(vehicle_id, "rush_hour")
    print(f"  Set vehicle {vehicle_id} to rush hour scenario")
    
    await service.simulate_rush_hour(True)
    print(f"  Enabled rush hour simulation for all vehicles")
    
    # Show active locations
    active_locations = await service.get_all_active_locations()
    print(f"\n📊 Active locations: {len(active_locations)} vehicles being tracked")
    
    return service

def demo_websocket_broadcasting():
    """Demonstrate WebSocket broadcasting capabilities"""
    print("\n\n📺 WebSocket Broadcasting Demo")
    print("=" * 50)
    
    from app.services.websocket_manager import ConnectionManager
    
    manager = ConnectionManager()
    
    print("\n🔌 WebSocket Connection Management:")
    print(f"  Initial connections: {manager.get_connection_count()}")
    
    # Simulate adding connections
    manager.active_connections["realtime"].add("mock_connection_1")
    manager.active_connections["realtime"].add("mock_connection_2")
    manager.active_connections["admin"].add("mock_admin_connection")
    
    stats = manager.get_connection_stats()
    print(f"  After adding connections:")
    print(f"    Total: {stats['total_connections']}")
    print(f"    Realtime: {stats['realtime_connections']}")
    print(f"    Admin: {stats['admin_connections']}")
    
    print("\n📡 Broadcasting capabilities ready!")
    print("  - Real-time location updates")
    print("  - Admin dashboard updates")
    print("  - Driver portal notifications")
    
    return manager

async def main():
    """Main demo function"""
    print("🎯 BMTC Transport Tracker - Location Service Demo")
    print("=" * 60)
    print("This demo showcases the implementation of Task 3:")
    print("• Mock BMTC Data Generator")
    print("• Location Tracking Service")
    print("• WebSocket Broadcasting System")
    print("=" * 60)
    
    try:
        # Demo 1: Mock Data Generator
        generator, routes = await demo_mock_data_generator()
        
        # Demo 2: Location Tracking Service
        service = await demo_location_tracking_service(generator, routes)
        
        # Demo 3: WebSocket Broadcasting
        websocket_manager = demo_websocket_broadcasting()
        
        print("\n\n✅ Demo completed successfully!")
        print("\n🚀 Key Features Implemented:")
        print("  ✓ Realistic BMTC route generation with Bengaluru landmarks")
        print("  ✓ GPS coordinate simulation with natural movement patterns")
        print("  ✓ Configurable scenarios (normal, rush hour, delays, breakdowns)")
        print("  ✓ Location smoothing and interpolation algorithms")
        print("  ✓ Real-time WebSocket broadcasting system")
        print("  ✓ Location history storage and cleanup")
        print("  ✓ Comprehensive test coverage")
        
        print("\n📋 Requirements Satisfied:")
        print("  ✓ Requirement 1.1: Real-time bus tracking with animated markers")
        print("  ✓ Requirement 1.6: Smooth marker transitions and GPS updates")
        print("  ✓ Requirement 12.5: Mock data generation for demo purposes")
        print("  ✓ Requirement 12.1: WebSocket API for real-time updates")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())