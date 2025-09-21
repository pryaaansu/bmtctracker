#!/usr/bin/env python3
"""
Unit tests for Route Management functionality
Tests the route management schemas and validation logic
"""

import pytest
import json
from pydantic import ValidationError
from app.schemas.admin import (
    RouteCreateRequest, RouteUpdateRequest, RouteStopCreate,
    RouteStopUpdate, RouteStopReorderRequest, RouteValidationResult,
    BulkRouteImport, BulkRouteExport
)

def test_route_create_request_schema():
    """Test RouteCreateRequest schema validation"""
    # Valid route data
    valid_data = {
        "name": "Test Route",
        "route_number": "TEST001",
        "geojson": json.dumps({
            "type": "LineString",
            "coordinates": [[77.5946, 12.9716], [77.6648, 12.8456]]
        }),
        "polyline": "12.9716,77.5946;12.8456,77.6648",
        "stops": [
            {
                "name": "Stop 1",
                "latitude": 12.9716,
                "longitude": 77.5946,
                "stop_order": 0
            }
        ],
        "is_active": True
    }
    
    route = RouteCreateRequest(**valid_data)
    assert route.name == "Test Route"
    assert route.route_number == "TEST001"
    assert len(route.stops) == 1
    assert route.is_active is True
    print("✓ RouteCreateRequest schema validation passed")

def test_route_stop_create_schema():
    """Test RouteStopCreate schema validation"""
    # Valid stop data
    valid_stop = {
        "name": "Test Stop",
        "name_kannada": "ಟೆಸ್ಟ್ ನಿಲ್ದಾಣ",
        "latitude": 12.9716,
        "longitude": 77.5946,
        "stop_order": 0
    }
    
    stop = RouteStopCreate(**valid_stop)
    assert stop.name == "Test Stop"
    assert stop.name_kannada == "ಟೆಸ್ಟ್ ನಿಲ್ದಾಣ"
    assert stop.latitude == 12.9716
    assert stop.longitude == 77.5946
    assert stop.stop_order == 0
    print("✓ RouteStopCreate schema validation passed")

def test_route_stop_validation():
    """Test RouteStopCreate validation constraints"""
    # Test invalid latitude
    try:
        RouteStopCreate(
            name="Test Stop",
            latitude=100.0,  # Invalid latitude
            longitude=77.5946,
            stop_order=0
        )
        assert False, "Should have raised validation error for invalid latitude"
    except ValidationError:
        print("✓ Latitude validation constraint works")
    
    # Test invalid longitude
    try:
        RouteStopCreate(
            name="Test Stop",
            latitude=12.9716,
            longitude=200.0,  # Invalid longitude
            stop_order=0
        )
        assert False, "Should have raised validation error for invalid longitude"
    except ValidationError:
        print("✓ Longitude validation constraint works")

def test_bulk_import_schema():
    """Test BulkRouteImport schema validation"""
    # Valid CSV import
    csv_import = BulkRouteImport(
        format="csv",
        data="name,route_number,geojson,polyline\nTest,001,{},line",
        validate_only=True,
        overwrite_existing=False
    )
    
    assert csv_import.format == "csv"
    assert csv_import.validate_only is True
    assert csv_import.overwrite_existing is False
    print("✓ BulkRouteImport schema validation passed")
    
    # Test invalid format
    try:
        BulkRouteImport(
            format="invalid",  # Invalid format
            data="test data"
        )
        assert False, "Should have raised validation error for invalid format"
    except ValidationError:
        print("✓ Format validation constraint works")

def test_bulk_export_schema():
    """Test BulkRouteExport schema validation"""
    # Valid export request
    export_request = BulkRouteExport(
        format="json",
        route_ids=[1, 2, 3],
        include_stops=True,
        include_inactive=False
    )
    
    assert export_request.format == "json"
    assert export_request.route_ids == [1, 2, 3]
    assert export_request.include_stops is True
    assert export_request.include_inactive is False
    print("✓ BulkRouteExport schema validation passed")

def test_route_validation_result_schema():
    """Test RouteValidationResult schema"""
    validation_result = RouteValidationResult(
        is_valid=False,
        errors=["Route number already exists"],
        warnings=["Stops are very close together"],
        conflicts=[{"type": "duplicate", "field": "route_number"}]
    )
    
    assert validation_result.is_valid is False
    assert len(validation_result.errors) == 1
    assert len(validation_result.warnings) == 1
    assert len(validation_result.conflicts) == 1
    print("✓ RouteValidationResult schema validation passed")

def test_route_update_schema():
    """Test RouteUpdateRequest schema"""
    # Partial update
    update_data = RouteUpdateRequest(
        name="Updated Route Name",
        is_active=False
    )
    
    assert update_data.name == "Updated Route Name"
    assert update_data.is_active is False
    assert update_data.route_number is None  # Not provided
    print("✓ RouteUpdateRequest schema validation passed")

def test_stop_reorder_schema():
    """Test RouteStopReorderRequest schema"""
    reorder_data = RouteStopReorderRequest(
        stop_orders=[
            {"stop_id": 1, "new_order": 0},
            {"stop_id": 2, "new_order": 1},
            {"stop_id": 3, "new_order": 2}
        ]
    )
    
    assert len(reorder_data.stop_orders) == 3
    assert reorder_data.stop_orders[0]["stop_id"] == 1
    assert reorder_data.stop_orders[0]["new_order"] == 0
    print("✓ RouteStopReorderRequest schema validation passed")

def main():
    """Run all unit tests"""
    print("=" * 60)
    print("Route Management Unit Tests")
    print("=" * 60)
    
    tests = [
        test_route_create_request_schema,
        test_route_stop_create_schema,
        test_route_stop_validation,
        test_bulk_import_schema,
        test_bulk_export_schema,
        test_route_validation_result_schema,
        test_route_update_schema,
        test_stop_reorder_schema
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"✗ {test.__name__} failed: {e}")
    
    print()
    print("=" * 60)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ All unit tests passed!")
        return 0
    else:
        print("✗ Some tests failed.")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())