#!/usr/bin/env python3
"""
Simple test script for emergency functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models.emergency import EmergencyIncident, EmergencyBroadcast, EmergencyContact, EmergencyType, EmergencyStatus
from app.schemas.emergency import EmergencyReportCreate, EmergencyBroadcastCreate
from app.repositories.emergency import EmergencyRepository, EmergencyBroadcastRepository, EmergencyContactRepository

def test_emergency_models():
    """Test that emergency models can be imported and instantiated"""
    print("Testing emergency models...")
    
    # Test EmergencyIncident
    incident = EmergencyIncident(
        type=EmergencyType.MEDICAL,
        description="Test incident",
        latitude=12.9716,
        longitude=77.5946,
        status=EmergencyStatus.REPORTED
    )
    print(f"✓ EmergencyIncident created: {incident.type}")
    
    # Test EmergencyBroadcast
    broadcast = EmergencyBroadcast(
        title="Test Alert",
        message="Test message",
        sent_by_admin_id=1
    )
    print(f"✓ EmergencyBroadcast created: {broadcast.title}")
    
    # Test EmergencyContact
    contact = EmergencyContact(
        name="Test Emergency Service",
        phone_number="123-456-7890",
        type="test",
        priority=1
    )
    print(f"✓ EmergencyContact created: {contact.name}")
    
    print("All emergency models work correctly!")

def test_emergency_schemas():
    """Test that emergency schemas work correctly"""
    print("\nTesting emergency schemas...")
    
    # Test EmergencyReportCreate
    report_data = EmergencyReportCreate(
        type=EmergencyType.SAFETY,
        description="Test safety incident",
        latitude=12.9716,
        longitude=77.5946,
        phone_number="+91-9876543210"
    )
    print(f"✓ EmergencyReportCreate validated: {report_data.type}")
    
    # Test EmergencyBroadcastCreate
    broadcast_data = EmergencyBroadcastCreate(
        title="Test Broadcast",
        message="Test broadcast message",
        send_sms=True,
        send_push=True
    )
    print(f"✓ EmergencyBroadcastCreate validated: {broadcast_data.title}")
    
    print("All emergency schemas work correctly!")

def test_emergency_enums():
    """Test that emergency enums work correctly"""
    print("\nTesting emergency enums...")
    
    # Test EmergencyType
    types = [EmergencyType.MEDICAL, EmergencyType.SAFETY, EmergencyType.HARASSMENT, EmergencyType.ACCIDENT, EmergencyType.OTHER]
    print(f"✓ EmergencyType values: {[t.value for t in types]}")
    
    # Test EmergencyStatus
    statuses = [EmergencyStatus.REPORTED, EmergencyStatus.ACKNOWLEDGED, EmergencyStatus.IN_PROGRESS, EmergencyStatus.RESOLVED, EmergencyStatus.CLOSED]
    print(f"✓ EmergencyStatus values: {[s.value for s in statuses]}")
    
    print("All emergency enums work correctly!")

if __name__ == "__main__":
    print("Running emergency functionality tests...\n")
    
    try:
        test_emergency_models()
        test_emergency_schemas()
        test_emergency_enums()
        print("\n🎉 All emergency tests passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)