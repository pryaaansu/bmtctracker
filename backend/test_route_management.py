#!/usr/bin/env python3
"""
Test script for Route Management functionality
Tests the interactive route creation and editing features
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
ADMIN_EMAIL = "admin@bmtc.gov.in"
ADMIN_PASSWORD = "admin123"

def get_auth_token():
    """Get authentication token for admin user"""
    login_data = {
        "username": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/auth/login", data=login_data)
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"Login failed: {response.status_code} - {response.text}")
        return None

def test_route_creation():
    """Test creating a new route with stops"""
    token = get_auth_token()
    if not token:
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test route data
    route_data = {
        "name": "Test Route - Majestic to Electronic City",
        "route_number": "TEST001",
        "geojson": json.dumps({
            "type": "LineString",
            "coordinates": [
                [77.5946, 12.9716],  # Majestic
                [77.6648, 12.8456]   # Electronic City
            ]
        }),
        "polyline": "12.9716,77.5946;12.8456,77.6648",
        "stops": [
            {
                "name": "Majestic Bus Station",
                "name_kannada": "ಮೆಜೆಸ್ಟಿಕ್ ಬಸ್ ನಿಲ್ದಾಣ",
                "latitude": 12.9716,
                "longitude": 77.5946,
                "stop_order": 0
            },
            {
                "name": "Banashankari",
                "name_kannada": "ಬನಶಂಕರಿ",
                "latitude": 12.9250,
                "longitude": 77.5667,
                "stop_order": 1
            },
            {
                "name": "Electronic City",
                "name_kannada": "ಎಲೆಕ್ಟ್ರಾನಿಕ್ ಸಿಟಿ",
                "latitude": 12.8456,
                "longitude": 77.6648,
                "stop_order": 2
            }
        ],
        "is_active": True
    }
    
    print("Testing route creation...")
    response = requests.post(
        f"{BASE_URL}/api/v1/admin/routes",
        headers=headers,
        json=route_data
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✓ Route created successfully: {result}")
        return result["route"]["id"]
    else:
        print(f"✗ Route creation failed: {response.status_code} - {response.text}")
        return None

def test_route_validation():
    """Test route validation"""
    token = get_auth_token()
    if not token:
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test invalid route data (duplicate route number)
    invalid_route_data = {
        "name": "Another Test Route",
        "route_number": "TEST001",  # Duplicate
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
    
    print("Testing route validation...")
    response = requests.post(
        f"{BASE_URL}/api/v1/admin/routes/validate",
        headers=headers,
        json=invalid_route_data
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✓ Validation response: {result}")
        return not result["is_valid"]  # Should be invalid
    else:
        print(f"✗ Validation failed: {response.status_code} - {response.text}")
        return False

def test_route_update(route_id):
    """Test updating an existing route"""
    token = get_auth_token()
    if not token:
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    
    update_data = {
        "name": "Updated Test Route - Majestic to Electronic City Express",
        "is_active": False
    }
    
    print(f"Testing route update for route ID {route_id}...")
    response = requests.put(
        f"{BASE_URL}/api/v1/admin/routes/{route_id}",
        headers=headers,
        json=update_data
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✓ Route updated successfully: {result}")
        return True
    else:
        print(f"✗ Route update failed: {response.status_code} - {response.text}")
        return False

def test_stop_management(route_id):
    """Test adding and managing stops"""
    token = get_auth_token()
    if not token:
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Add a new stop
    new_stop_data = {
        "name": "Intermediate Stop",
        "name_kannada": "ಮಧ್ಯಂತರ ನಿಲ್ದಾಣ",
        "latitude": 12.9000,
        "longitude": 77.6000,
        "stop_order": 1  # Insert between existing stops
    }
    
    print(f"Testing stop addition to route {route_id}...")
    response = requests.post(
        f"{BASE_URL}/api/v1/admin/routes/{route_id}/stops",
        headers=headers,
        json=new_stop_data
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✓ Stop added successfully: {result}")
        return True
    else:
        print(f"✗ Stop addition failed: {response.status_code} - {response.text}")
        return False

def test_bulk_operations():
    """Test bulk import/export operations"""
    token = get_auth_token()
    if not token:
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test CSV import validation
    csv_data = """name,route_number,geojson,polyline,is_active
Test Bulk Route 1,BULK001,"{""type"":""LineString"",""coordinates"":[[77.5946,12.9716],[77.6648,12.8456]]}","12.9716,77.5946;12.8456,77.6648",true
Test Bulk Route 2,BULK002,"{""type"":""LineString"",""coordinates"":[[77.5946,12.9716],[77.6648,12.8456]]}","12.9716,77.5946;12.8456,77.6648",true"""
    
    import_data = {
        "format": "csv",
        "data": csv_data,
        "validate_only": True,
        "overwrite_existing": False
    }
    
    print("Testing bulk import validation...")
    response = requests.post(
        f"{BASE_URL}/api/v1/admin/routes/bulk-import",
        headers=headers,
        json=import_data
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✓ Bulk import validation: {result}")
        return result["success"]
    else:
        print(f"✗ Bulk import validation failed: {response.status_code} - {response.text}")
        return False

def test_route_deletion(route_id):
    """Test deleting a route"""
    token = get_auth_token()
    if not token:
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"Testing route deletion for route ID {route_id}...")
    response = requests.delete(
        f"{BASE_URL}/api/v1/admin/routes/{route_id}",
        headers=headers
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✓ Route deleted successfully: {result}")
        return True
    else:
        print(f"✗ Route deletion failed: {response.status_code} - {response.text}")
        return False

def main():
    """Run all route management tests"""
    print("=" * 60)
    print("BMTC Route Management Test Suite")
    print("=" * 60)
    print(f"Testing against: {BASE_URL}")
    print(f"Timestamp: {datetime.now()}")
    print()
    
    # Test sequence
    tests_passed = 0
    total_tests = 6
    
    # 1. Test route creation
    route_id = test_route_creation()
    if route_id:
        tests_passed += 1
    print()
    
    # 2. Test route validation
    if test_route_validation():
        tests_passed += 1
    print()
    
    # 3. Test route update (if route was created)
    if route_id and test_route_update(route_id):
        tests_passed += 1
    print()
    
    # 4. Test stop management (if route was created)
    if route_id and test_stop_management(route_id):
        tests_passed += 1
    print()
    
    # 5. Test bulk operations
    if test_bulk_operations():
        tests_passed += 1
    print()
    
    # 6. Test route deletion (if route was created)
    if route_id and test_route_deletion(route_id):
        tests_passed += 1
    print()
    
    # Summary
    print("=" * 60)
    print(f"Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("✓ All route management tests passed!")
        return 0
    else:
        print("✗ Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())