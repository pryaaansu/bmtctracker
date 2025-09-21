import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.emergency import EmergencyIncident, EmergencyBroadcast, EmergencyContact, EmergencyType, EmergencyStatus
from app.models.user import User, UserRole

def test_report_emergency_anonymous(client: TestClient, db: Session):
    """Test reporting emergency without authentication"""
    emergency_data = {
        "type": "medical",
        "description": "Person collapsed at bus stop",
        "latitude": 12.9716,
        "longitude": 77.5946,
        "phone_number": "+91-9876543210"
    }
    
    response = client.post("/api/v1/emergency/report", json=emergency_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["type"] == "medical"
    assert data["description"] == "Person collapsed at bus stop"
    assert data["status"] == "reported"
    assert data["emergency_call_made"] == True  # Medical emergencies trigger calls

def test_report_emergency_authenticated(client: TestClient, db: Session, test_user: User):
    """Test reporting emergency with authentication"""
    # Login first
    login_response = client.post("/api/v1/auth/login", data={
        "username": test_user.email,
        "password": "testpass123"
    })
    token = login_response.json()["access_token"]
    
    emergency_data = {
        "type": "safety",
        "description": "Suspicious activity near bus stop",
        "latitude": 12.9716,
        "longitude": 77.5946
    }
    
    response = client.post(
        "/api/v1/emergency/report", 
        json=emergency_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    
    data = response.json()
    assert data["type"] == "safety"
    assert data["user_id"] == test_user.id
    assert data["emergency_call_made"] == False  # Safety incidents don't auto-trigger calls

def test_get_incidents_admin_only(client: TestClient, db: Session, test_admin: User):
    """Test that only admins can view incidents"""
    # Create test incident
    incident = EmergencyIncident(
        type=EmergencyType.ACCIDENT,
        description="Bus accident reported",
        latitude=12.9716,
        longitude=77.5946,
        status=EmergencyStatus.REPORTED
    )
    db.add(incident)
    db.commit()
    
    # Login as admin
    login_response = client.post("/api/v1/auth/login", data={
        "username": test_admin.email,
        "password": "adminpass123"
    })
    token = login_response.json()["access_token"]
    
    response = client.get(
        "/api/v1/emergency/incidents",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    
    data = response.json()
    assert len(data) >= 1
    assert data[0]["type"] == "accident"

def test_get_incidents_unauthorized(client: TestClient, db: Session, test_user: User):
    """Test that regular users cannot view incidents"""
    # Login as regular user
    login_response = client.post("/api/v1/auth/login", data={
        "username": test_user.email,
        "password": "testpass123"
    })
    token = login_response.json()["access_token"]
    
    response = client.get(
        "/api/v1/emergency/incidents",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403

def test_update_incident(client: TestClient, db: Session, test_admin: User):
    """Test updating an emergency incident"""
    # Create test incident
    incident = EmergencyIncident(
        type=EmergencyType.HARASSMENT,
        description="Harassment reported on bus",
        status=EmergencyStatus.REPORTED
    )
    db.add(incident)
    db.commit()
    db.refresh(incident)
    
    # Login as admin
    login_response = client.post("/api/v1/auth/login", data={
        "username": test_admin.email,
        "password": "adminpass123"
    })
    token = login_response.json()["access_token"]
    
    update_data = {
        "status": "acknowledged",
        "admin_notes": "Incident acknowledged, investigating"
    }
    
    response = client.put(
        f"/api/v1/emergency/incidents/{incident.id}",
        json=update_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "acknowledged"
    assert data["admin_notes"] == "Incident acknowledged, investigating"
    assert data["assigned_admin_id"] == test_admin.id
    assert data["acknowledged_at"] is not None

def test_create_emergency_broadcast(client: TestClient, db: Session, test_admin: User):
    """Test creating an emergency broadcast"""
    # Login as admin
    login_response = client.post("/api/v1/auth/login", data={
        "username": test_admin.email,
        "password": "adminpass123"
    })
    token = login_response.json()["access_token"]
    
    broadcast_data = {
        "title": "Service Disruption Alert",
        "message": "Bus services on Route 500D are temporarily suspended due to road closure.",
        "send_sms": True,
        "send_push": True,
        "send_whatsapp": False
    }
    
    response = client.post(
        "/api/v1/emergency/broadcast",
        json=broadcast_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    
    data = response.json()
    assert data["title"] == "Service Disruption Alert"
    assert data["sent_by_admin_id"] == test_admin.id
    assert data["total_recipients"] == 100  # Mock data
    assert data["successful_deliveries"] == 95

def test_get_emergency_contacts_public(client: TestClient, db: Session):
    """Test that emergency contacts are publicly accessible"""
    # Create test contact
    contact = EmergencyContact(
        name="Test Emergency Service",
        phone_number="123-456-7890",
        type="test",
        is_active=True,
        priority=1
    )
    db.add(contact)
    db.commit()
    
    response = client.get("/api/v1/emergency/contacts")
    assert response.status_code == 200
    
    data = response.json()
    assert len(data) >= 1
    
    # Find our test contact
    test_contact = next((c for c in data if c["name"] == "Test Emergency Service"), None)
    assert test_contact is not None
    assert test_contact["phone_number"] == "123-456-7890"
    assert test_contact["is_active"] == True

def test_create_emergency_contact_admin_only(client: TestClient, db: Session, test_admin: User):
    """Test that only admins can create emergency contacts"""
    # Login as admin
    login_response = client.post("/api/v1/auth/login", data={
        "username": test_admin.email,
        "password": "adminpass123"
    })
    token = login_response.json()["access_token"]
    
    contact_data = {
        "name": "New Emergency Service",
        "phone_number": "+91-9876543210",
        "type": "custom",
        "priority": 2
    }
    
    response = client.post(
        "/api/v1/emergency/contacts",
        json=contact_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    
    data = response.json()
    assert data["name"] == "New Emergency Service"
    assert data["phone_number"] == "+91-9876543210"
    assert data["type"] == "custom"
    assert data["priority"] == 2

def test_emergency_stats_admin_only(client: TestClient, db: Session, test_admin: User):
    """Test emergency statistics endpoint"""
    # Create some test incidents
    incidents = [
        EmergencyIncident(type=EmergencyType.MEDICAL, status=EmergencyStatus.REPORTED),
        EmergencyIncident(type=EmergencyType.SAFETY, status=EmergencyStatus.ACKNOWLEDGED),
        EmergencyIncident(type=EmergencyType.ACCIDENT, status=EmergencyStatus.RESOLVED)
    ]
    
    for incident in incidents:
        db.add(incident)
    db.commit()
    
    # Login as admin
    login_response = client.post("/api/v1/auth/login", data={
        "username": test_admin.email,
        "password": "adminpass123"
    })
    token = login_response.json()["access_token"]
    
    response = client.get(
        "/api/v1/emergency/stats",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    
    data = response.json()
    assert "total_incidents" in data
    assert "incidents_by_type" in data
    assert "incidents_by_status" in data
    assert "recent_incidents" in data
    assert data["total_incidents"] >= 3

def test_emergency_dashboard(client: TestClient, db: Session, test_admin: User):
    """Test emergency dashboard endpoint"""
    # Login as admin
    login_response = client.post("/api/v1/auth/login", data={
        "username": test_admin.email,
        "password": "adminpass123"
    })
    token = login_response.json()["access_token"]
    
    response = client.get(
        "/api/v1/emergency/dashboard",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    
    data = response.json()
    assert "stats" in data
    assert "recent_broadcasts" in data
    assert "emergency_contacts" in data
    
    # Check stats structure
    stats = data["stats"]
    assert "total_incidents" in stats
    assert "incidents_by_type" in stats
    assert "incidents_by_status" in stats
    assert "recent_incidents" in stats

def test_invalid_emergency_type(client: TestClient):
    """Test reporting emergency with invalid type"""
    emergency_data = {
        "type": "invalid_type",
        "description": "Test incident",
        "latitude": 12.9716,
        "longitude": 77.5946
    }
    
    response = client.post("/api/v1/emergency/report", json=emergency_data)
    assert response.status_code == 422  # Validation error

def test_invalid_coordinates(client: TestClient):
    """Test reporting emergency with invalid coordinates"""
    emergency_data = {
        "type": "safety",
        "description": "Test incident",
        "latitude": 200.0,  # Invalid latitude
        "longitude": 77.5946
    }
    
    response = client.post("/api/v1/emergency/report", json=emergency_data)
    assert response.status_code == 422  # Validation error