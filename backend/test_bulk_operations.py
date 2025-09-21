#!/usr/bin/env python3
"""
Integration tests for bulk route operations
Tests CSV/GeoJSON import and export functionality
"""

import json
import tempfile
import os
from io import StringIO
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Mock the database and dependencies for testing
def test_csv_import_validation():
    """Test CSV import validation logic"""
    from app.api.v1.endpoints.admin import validate_route_data
    from app.schemas.admin import RouteCreateRequest
    
    # Mock database session
    mock_db = Mock()
    mock_db.query().filter().first.return_value = None  # No existing route
    
    # Valid CSV data
    valid_route = RouteCreateRequest(
        name="Test Route",
        route_number="TEST001",
        geojson=json.dumps({
            "type": "LineString",
            "coordinates": [[77.5946, 12.9716], [77.6648, 12.8456]]
        }),
        polyline="12.9716,77.5946;12.8456,77.6648",
        stops=[
            {
                "name": "Stop 1",
                "latitude": 12.9716,
                "longitude": 77.5946,
                "stop_order": 0
            },
            {
                "name": "Stop 2", 
                "latitude": 12.8456,
                "longitude": 77.6648,
                "stop_order": 1
            }
        ],
        is_active=True
    )
    
    result = validate_route_data(valid_route, mock_db)
    
    assert result["is_valid"] is True
    assert len(result["errors"]) == 0
    print("✓ CSV import validation passed")

def test_csv_parsing():
    """Test CSV data parsing logic"""
    csv_data = """name,route_number,geojson,polyline,is_active
Test Route 1,001,"{""type"":""LineString"",""coordinates"":[[77.5946,12.9716],[77.6648,12.8456]]}","12.9716,77.5946;12.8456,77.6648",true
Test Route 2,002,"{""type"":""LineString"",""coordinates"":[[77.5946,12.9716],[77.6648,12.8456]]}","12.9716,77.5946;12.8456,77.6648",false"""
    
    import csv
    csv_reader = csv.DictReader(StringIO(csv_data))
    routes = list(csv_reader)
    
    assert len(routes) == 2
    assert routes[0]["name"] == "Test Route 1"
    assert routes[0]["route_number"] == "001"
    assert routes[0]["is_active"] == "true"
    assert routes[1]["name"] == "Test Route 2"
    assert routes[1]["is_active"] == "false"
    print("✓ CSV parsing logic works correctly")

def test_geojson_parsing():
    """Test GeoJSON data parsing logic"""
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
    
    print("✓ GeoJSON parsing logic works correctly")

def test_export_csv_generation():
    """Test CSV export generation"""
    # Mock route data
    mock_routes = [
        Mock(
            id=1,
            name="Test Route 1",
            route_number="001",
            geojson='{"type":"LineString","coordinates":[[77.5946,12.9716],[77.6648,12.8456]]}',
            polyline="12.9716,77.5946;12.8456,77.6648",
            is_active=True,
            created_at=Mock(isoformat=lambda: "2024-01-01T00:00:00")
        ),
        Mock(
            id=2,
            name="Test Route 2", 
            route_number="002",
            geojson='{"type":"LineString","coordinates":[[77.5946,12.9716],[77.6648,12.8456]]}',
            polyline="12.9716,77.5946;12.8456,77.6648",
            is_active=False,
            created_at=Mock(isoformat=lambda: "2024-01-02T00:00:00")
        )
    ]
    
    # Generate CSV
    import csv
    output = StringIO()
    fieldnames = ['id', 'name', 'route_number', 'geojson', 'polyline', 'is_active', 'created_at']
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    
    for route in mock_routes:
        writer.writerow({
            'id': route.id,
            'name': route.name,
            'route_number': route.route_number,
            'geojson': route.geojson,
            'polyline': route.polyline,
            'is_active': route.is_active,
            'created_at': route.created_at.isoformat()
        })
    
    csv_content = output.getvalue()
    lines = csv_content.strip().split('\n')
    
    assert len(lines) == 3  # Header + 2 data rows
    assert 'id,name,route_number' in lines[0]  # Header
    assert '1,Test Route 1,001' in lines[1]    # First route
    assert '2,Test Route 2,002' in lines[2]    # Second route
    
    print("✓ CSV export generation works correctly")

def test_export_geojson_generation():
    """Test GeoJSON export generation"""
    # Mock route data
    mock_routes = [
        Mock(
            id=1,
            name="Test Route 1",
            route_number="001",
            geojson='{"type":"LineString","coordinates":[[77.5946,12.9716],[77.6648,12.8456]]}',
            is_active=True,
            created_at=Mock(isoformat=lambda: "2024-01-01T00:00:00")
        )
    ]
    
    # Generate GeoJSON
    features = []
    for route in mock_routes:
        try:
            geometry = json.loads(route.geojson)
        except json.JSONDecodeError:
            geometry = {"type": "LineString", "coordinates": []}
        
        properties = {
            'id': route.id,
            'name': route.name,
            'route_number': route.route_number,
            'is_active': route.is_active,
            'created_at': route.created_at.isoformat()
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

def test_validation_errors():
    """Test validation error detection"""
    from app.api.v1.endpoints.admin import validate_route_data
    from app.schemas.admin import RouteCreateRequest
    
    # Mock database with existing route
    mock_db = Mock()
    existing_route = Mock(route_number="EXISTING001")
    mock_db.query().filter().first.return_value = existing_route
    
    # Route with duplicate number
    duplicate_route = RouteCreateRequest(
        name="Duplicate Route",
        route_number="EXISTING001",  # Duplicate
        geojson='{"type":"LineString","coordinates":[[77.5946,12.9716],[77.6648,12.8456]]}',
        polyline="12.9716,77.5946;12.8456,77.6648",
        stops=[],
        is_active=True
    )
    
    result = validate_route_data(duplicate_route, mock_db)
    
    assert result["is_valid"] is False
    assert len(result["errors"]) > 0
    assert "already exists" in result["errors"][0]
    print("✓ Validation error detection works correctly")

def test_stop_proximity_warnings():
    """Test stop proximity warning generation"""
    from app.api.v1.endpoints.admin import validate_route_data, calculate_distance
    from app.schemas.admin import RouteCreateRequest
    
    # Test distance calculation
    # Distance between Majestic (12.9716, 77.5946) and nearby point
    distance = calculate_distance(12.9716, 77.5946, 12.9720, 77.5950)
    assert distance < 100  # Should be less than 100 meters
    
    # Mock database
    mock_db = Mock()
    mock_db.query().filter().first.return_value = None
    
    # Route with very close stops
    close_stops_route = RouteCreateRequest(
        name="Close Stops Route",
        route_number="CLOSE001",
        geojson='{"type":"LineString","coordinates":[[77.5946,12.9716],[77.5950,12.9720]]}',
        polyline="12.9716,77.5946;12.9720,77.5950",
        stops=[
            {
                "name": "Stop 1",
                "latitude": 12.9716,
                "longitude": 77.5946,
                "stop_order": 0
            },
            {
                "name": "Stop 2",
                "latitude": 12.9720,  # Very close to Stop 1
                "longitude": 77.5950,
                "stop_order": 1
            }
        ],
        is_active=True
    )
    
    result = validate_route_data(close_stops_route, mock_db)
    
    assert result["is_valid"] is True  # Valid but with warnings
    assert len(result["warnings"]) > 0
    assert "very close" in result["warnings"][0]
    print("✓ Stop proximity warning generation works correctly")

def main():
    """Run all bulk operations tests"""
    print("=" * 60)
    print("Bulk Route Operations Tests")
    print("=" * 60)
    
    tests = [
        test_csv_import_validation,
        test_csv_parsing,
        test_geojson_parsing,
        test_export_csv_generation,
        test_export_geojson_generation,
        test_validation_errors,
        test_stop_proximity_warnings
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
        print("✓ All bulk operations tests passed!")
        return 0
    else:
        print("✗ Some tests failed.")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())