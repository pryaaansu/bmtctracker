#!/usr/bin/env python3
"""
Simple test for emergency core functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_emergency_imports():
    """Test that emergency modules can be imported"""
    print("Testing emergency imports...")
    
    try:
        from app.models.emergency import EmergencyType, EmergencyStatus
        print(f"✓ EmergencyType imported: {list(EmergencyType)}")
        print(f"✓ EmergencyStatus imported: {list(EmergencyStatus)}")
        
        # Test enum values
        assert EmergencyType.MEDICAL.value == "medical"
        assert EmergencyType.SAFETY.value == "safety"
        assert EmergencyType.HARASSMENT.value == "harassment"
        assert EmergencyType.ACCIDENT.value == "accident"
        assert EmergencyType.OTHER.value == "other"
        print("✓ EmergencyType values correct")
        
        assert EmergencyStatus.REPORTED.value == "reported"
        assert EmergencyStatus.ACKNOWLEDGED.value == "acknowledged"
        assert EmergencyStatus.IN_PROGRESS.value == "in_progress"
        assert EmergencyStatus.RESOLVED.value == "resolved"
        assert EmergencyStatus.CLOSED.value == "closed"
        print("✓ EmergencyStatus values correct")
        
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_emergency_api_structure():
    """Test that emergency API endpoints are structured correctly"""
    print("\nTesting emergency API structure...")
    
    try:
        # Read the emergency API file
        with open('backend/app/api/v1/endpoints/emergency.py', 'r') as f:
            content = f.read()
        
        # Check for required endpoints
        required_endpoints = [
            '@router.post("/report"',
            '@router.get("/incidents"',
            '@router.put("/incidents/{incident_id}"',
            '@router.post("/broadcast"',
            '@router.get("/contacts"',
            '@router.get("/stats"',
            '@router.get("/dashboard"'
        ]
        
        for endpoint in required_endpoints:
            if endpoint in content:
                print(f"✓ Found endpoint: {endpoint}")
            else:
                print(f"❌ Missing endpoint: {endpoint}")
                return False
        
        return True
    except Exception as e:
        print(f"❌ API structure test failed: {e}")
        return False

def test_emergency_schemas():
    """Test emergency schema structure"""
    print("\nTesting emergency schemas...")
    
    try:
        # Read the emergency schema file
        with open('backend/app/schemas/emergency.py', 'r') as f:
            content = f.read()
        
        # Check for required schemas
        required_schemas = [
            'class EmergencyReportCreate',
            'class EmergencyIncidentResponse',
            'class EmergencyBroadcastCreate',
            'class EmergencyBroadcastResponse',
            'class EmergencyContactResponse'
        ]
        
        for schema in required_schemas:
            if schema in content:
                print(f"✓ Found schema: {schema}")
            else:
                print(f"❌ Missing schema: {schema}")
                return False
        
        return True
    except Exception as e:
        print(f"❌ Schema test failed: {e}")
        return False

def test_frontend_components():
    """Test that frontend emergency components exist"""
    print("\nTesting frontend components...")
    
    try:
        # Check SOS button
        if os.path.exists('src/components/ui/SOSButton.tsx'):
            print("✓ SOSButton component exists")
        else:
            print("❌ SOSButton component missing")
            return False
        
        # Check Emergency Management
        if os.path.exists('src/components/ui/EmergencyManagement.tsx'):
            print("✓ EmergencyManagement component exists")
        else:
            print("❌ EmergencyManagement component missing")
            return False
        
        # Check if components are exported
        with open('src/components/ui/index.ts', 'r') as f:
            content = f.read()
            if 'SOSButton' in content and 'EmergencyManagement' in content:
                print("✓ Emergency components are exported")
            else:
                print("❌ Emergency components not properly exported")
                return False
        
        return True
    except Exception as e:
        print(f"❌ Frontend component test failed: {e}")
        return False

if __name__ == "__main__":
    print("Running emergency core functionality tests...\n")
    
    tests = [
        test_emergency_imports,
        test_emergency_api_structure,
        test_emergency_schemas,
        test_frontend_components
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All emergency core tests passed!")
    else:
        print("❌ Some tests failed")
        sys.exit(1)