#!/usr/bin/env python3
"""
Simple tests for bulk route operations logic
Tests the core parsing and validation logic without dependencies
"""

import json
import csv
from io import StringIO
import math

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points in meters using Haversine formula"""
    R = 6371  # Earth's radius in kilometers
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = (math.sin(delta_lat / 2) ** 2 +
         math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c * 1000  # Convert to meters

def validate_geojson(geojson_str: str) -> tuple[bool, str]:
    """Validate GeoJSON format"""
    try:
        geojson_data = json.loads(geojson_str)
        if geojson_data.get("type") not in ["LineString", "MultiLineString"]:
            return False, "GeoJSON should be LineString or MultiLineString for routes"
        return True, ""
    except json.JSONDecodeError:
        return False, "Invalid GeoJSON format"

def test_csv_parsing():
    """Test CSV data parsing"""
    csv_data = """name,route_number,geojson,polyline,is_active
Test Route 1,001,"{""type"":""LineString"",""coordinates"":[[77.5946,12.9716],[77.6648,12.8456]]}","12.9716,77.5946;12.8456,77.6648",true
Test Route 2,002,"{""type"":""LineString"",""coordinates"":[[77.5946,12.9716],[77.6648,12.8456]]}","12.9716,77.5946;12.8456,77.6648",false"""
    
    csv_reader = csv.DictReader(StringIO(csv_data))
    routes = list(csv_reader)
    
    assert len(routes) == 2
    assert routes[0]["name"] == "Test Route 1"
    assert routes[0]["route_number"] == "001"
    assert routes[0]["is_active"] == "true"
    assert routes[1]["name"] == "Test Route 2"
    assert routes[1]["is_active"] == "false"
    
    # Validate GeoJSON in each route
    for route in routes:
        is_valid, error = validate_geojson(route["geojson"])
        assert is_valid, f"Invalid GeoJSON: {error}"
    
    print("✓ CSV parsing works correctly")

def test_geojson_parsing():
    """Test GeoJSON data parsing"""
    geojson_data = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "name": "Test Route 1",
                    "route_number": "001",
                    "is_active": True
                },
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[77.5946, 12.9716], [77.6648, 12.8456]]
                }
            },
            {
                "type": "Feature", 
                "properties": {
                    "name": "Test Route 2",
                    "route_number": "002",
                    "is_active": False
                },
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[77.5946, 12.9716], [77.6648, 12.8456]]
                }
            }
        ]
    }
    
    features = geojson_data.get("features", [])
    assert len(features) == 2
    
    for i, feature in enumerate(features):
        properties = feature.get("properties", {})
        geometry = feature.get("geometry", {})
        
        assert properties.get("name") == f"Test Route {i+1}"
        assert properties.get("route_number") == f"00{i+1}"
        assert geometry.get("type") == "LineString"
        assert len(geometry.get("coordinates", [])) == 2
    
    print("✓ GeoJSON parsing works correctly")

def test_csv_export_generation():
    """Test CSV export generation"""
    # Mock route data
    routes_data = [
        {
            "id": 1,
            "name": "Test Route 1",
            "route_number": "001",
            "geojson": '{"type":"LineString","coordinates":[[77.5946,12.9716],[77.6648,12.8456]]}',
            "polyline": "12.9716,77.5946;12.8456,77.6648",
            "is_active": True,
            "created_at": "2024-01-01T00:00:00"
        },
        {
            "id": 2,
            "name": "Test Route 2", 
            "route_number": "002",
            "geojson": '{"type":"LineString","coordinates":[[77.5946,12.9716],[77.6648,12.8456]]}',
            "polyline": "12.9716,77.5946;12.8456,77.6648",
            "is_active": False,
            "created_at": "2024-01-02T00:00:00"
        }
    ]
    
    # Generate CSV
    output = StringIO()
    fieldnames = ['id', 'name', 'route_number', 'geojson', 'polyline', 'is_active', 'created_at']
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    
    for route in routes_data:
        writer.writerow(route)
    
    csv_content = output.getvalue()
    lines = csv_content.strip().split('\n')
    
    assert len(lines) == 3  # Header + 2 data rows
    assert 'id,name,route_number' in lines[0]  # Header
    assert '1,Test Route 1,001' in lines[1]    # First route
    assert '2,Test Route 2,002' in lines[2]    # Second route
    
    print("✓ CSV export generation works correctly")

def test_geojson_export_generation():
    """Test GeoJSON export generation"""
    # Mock route data
    routes_data = [
        {
            "id": 1,
            "name": "Test Route 1",
            "route_number": "001",
            "geojson": '{"type":"LineString","coordinates":[[77.5946,12.9716],[77.6648,12.8456]]}',
            "is_active": True,
            "created_at": "2024-01-01T00:00:00"
        }
    ]
    
    # Generate GeoJSON
    features = []
    for route in routes_data:
        try:
            geometry = json.loads(route["geojson"])
        except json.JSONDecodeError:
            geometry = {"type": "LineString", "coordinates": []}
        
        properties = {
            'id': route["id"],
            'name': route["name"],
            'route_number': route["route_number"],
            'is_active': route["is_active"],
            'created_at': route["created_at"]
        }
        
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
    
    assert geojson_data['type'] == 'FeatureCollection'
    assert len(geojson_data['features']) == 1
    
    feature = geojson_data['features'][0]
    assert feature['type'] == 'Feature'
    assert feature['properties']['name'] == 'Test Route 1'
    assert feature['geometry']['type'] == 'LineString'
    
    print("✓ GeoJSON export generation works correctly")

def test_distance_calculation():
    """Test distance calculation between stops"""
    # Distance between Majestic (12.9716, 77.5946) and Electronic City (12.8456, 77.6648)
    distance = calculate_distance(12.9716, 77.5946, 12.8456, 77.6648)
    
    # Should be approximately 15-20 km
    assert 15000 < distance < 25000, f"Distance {distance}m seems incorrect"
    
    # Test very close points
    close_distance = calculate_distance(12.9716, 77.5946, 12.9720, 77.5950)
    assert close_distance < 100, f"Close distance {close_distance}m should be less than 100m"
    
    print("✓ Distance calculation works correctly")

def test_route_validation():
    """Test route validation logic"""
    # Test valid route
    valid_route = {
        "name": "Test Route",
        "route_number": "TEST001",
        "geojson": '{"type":"LineString","coordinates":[[77.5946,12.9716],[77.6648,12.8456]]}',
        "stops": [
            {"name": "Stop 1", "latitude": 12.9716, "longitude": 77.5946, "stop_order": 0},
            {"name": "Stop 2", "latitude": 12.8456, "longitude": 77.6648, "stop_order": 1}
        ]
    }
    
    errors = []
    warnings = []
    
    # Validate GeoJSON
    is_valid, error = validate_geojson(valid_route["geojson"])
    if not is_valid:
        errors.append(error)
    
    # Check for duplicate stop orders
    stop_orders = [stop["stop_order"] for stop in valid_route["stops"]]
    if len(stop_orders) != len(set(stop_orders)):
        errors.append("Duplicate stop orders found")
    
    # Check for stops too close together
    stops = valid_route["stops"]
    for i, stop1 in enumerate(stops):
        for j, stop2 in enumerate(stops[i+1:], i+1):
            distance = calculate_distance(
                stop1["latitude"], stop1["longitude"],
                stop2["latitude"], stop2["longitude"]
            )
            if distance < 100:  # Less than 100 meters
                warnings.append(f"Stops '{stop1['name']}' and '{stop2['name']}' are very close ({distance:.0f}m)")
    
    assert len(errors) == 0, f"Validation should pass but got errors: {errors}"
    print("✓ Route validation works correctly")

def test_invalid_data_handling():
    """Test handling of invalid data"""
    # Test invalid GeoJSON
    invalid_geojson = '{"type":"Point","coordinates":[77.5946,12.9716]}'  # Point instead of LineString
    is_valid, error = validate_geojson(invalid_geojson)
    assert not is_valid
    assert "LineString" in error
    
    # Test malformed JSON
    malformed_json = '{"type":"LineString","coordinates":[77.5946,12.9716'  # Missing closing brackets
    is_valid, error = validate_geojson(malformed_json)
    assert not is_valid
    assert "Invalid GeoJSON format" in error
    
    print("✓ Invalid data handling works correctly")

def test_csv_with_stops_data():
    """Test CSV parsing with embedded stops data"""
    csv_data = """name,route_number,geojson,polyline,is_active,stops_data
Test Route,001,"{""type"":""LineString"",""coordinates"":[[77.5946,12.9716],[77.6648,12.8456]]}","12.9716,77.5946;12.8456,77.6648",true,"[{""name"":""Stop 1"",""latitude"":12.9716,""longitude"":77.5946,""stop_order"":0}]" """
    
    csv_reader = csv.DictReader(StringIO(csv_data))
    routes = list(csv_reader)
    
    assert len(routes) == 1
    route = routes[0]
    
    # Parse embedded stops data
    stops_data = json.loads(route["stops_data"])
    assert len(stops_data) == 1
    assert stops_data[0]["name"] == "Stop 1"
    assert stops_data[0]["latitude"] == 12.9716
    
    print("✓ CSV with stops data parsing works correctly")

def main():
    """Run all bulk operations tests"""
    print("=" * 60)
    print("Bulk Route Operations Logic Tests")
    print("=" * 60)
    
    tests = [
        test_csv_parsing,
        test_geojson_parsing,
        test_csv_export_generation,
        test_geojson_export_generation,
        test_distance_calculation,
        test_route_validation,
        test_invalid_data_handling,
        test_csv_with_stops_data
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"✗ {test.__name__} failed: {e}")
            import traceback
            traceback.print_exc()
    
    print()
    print("=" * 60)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ All bulk operations logic tests passed!")
        return 0
    else:
        print("✗ Some tests failed.")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())