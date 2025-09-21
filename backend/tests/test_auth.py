import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from app.core.database import get_db, Base
from app.models.user import User, UserRole
from app.core.auth import get_password_hash

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_auth.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="module")
def client():
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def test_user():
    db = TestingSessionLocal()
    user = User(
        email="test@example.com",
        phone="+919876543210",
        hashed_password=get_password_hash("testpass123"),
        full_name="Test User",
        role=UserRole.PASSENGER,
        is_active=True,
        is_verified=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    yield user
    db.delete(user)
    db.commit()
    db.close()

@pytest.fixture
def admin_user():
    db = TestingSessionLocal()
    user = User(
        email="admin@example.com",
        hashed_password=get_password_hash("adminpass123"),
        full_name="Admin User",
        role=UserRole.ADMIN,
        is_active=True,
        is_verified=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    yield user
    db.delete(user)
    db.commit()
    db.close()

class TestUserRegistration:
    def test_register_user_success(self, client):
        """Test successful user registration"""
        user_data = {
            "email": "newuser@example.com",
            "password": "newpass123",
            "full_name": "New User",
            "phone": "+919876543213",
            "role": "passenger"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["full_name"] == user_data["full_name"]
        assert data["phone"] == user_data["phone"]
        assert data["role"] == user_data["role"]
        assert data["is_active"] is True
        assert data["is_verified"] is False
        assert "id" in data
    
    def test_register_user_duplicate_email(self, client, test_user):
        """Test registration with duplicate email"""
        user_data = {
            "email": test_user.email,
            "password": "newpass123",
            "full_name": "Another User"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]
    
    def test_register_user_duplicate_phone(self, client, test_user):
        """Test registration with duplicate phone"""
        user_data = {
            "email": "another@example.com",
            "password": "newpass123",
            "phone": test_user.phone
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 400
        assert "Phone number already registered" in response.json()["detail"]
    
    def test_register_user_invalid_phone(self, client):
        """Test registration with invalid phone number"""
        user_data = {
            "email": "user@example.com",
            "password": "newpass123",
            "phone": "invalid-phone"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 422
    
    def test_register_user_short_password(self, client):
        """Test registration with short password"""
        user_data = {
            "email": "user@example.com",
            "password": "123"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 422

class TestUserLogin:
    def test_login_success(self, client, test_user):
        """Test successful login"""
        login_data = {
            "email": test_user.email,
            "password": "testpass123"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
        assert data["user"]["email"] == test_user.email
    
    def test_login_invalid_email(self, client):
        """Test login with invalid email"""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "testpass123"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]
    
    def test_login_invalid_password(self, client, test_user):
        """Test login with invalid password"""
        login_data = {
            "email": test_user.email,
            "password": "wrongpassword"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]

class TestProtectedEndpoints:
    def test_get_current_user_success(self, client, test_user):
        """Test getting current user info with valid token"""
        # Login first
        login_data = {
            "email": test_user.email,
            "password": "testpass123"
        }
        login_response = client.post("/api/v1/auth/login", json=login_data)
        token = login_response.json()["access_token"]
        
        # Get current user
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["email"] == test_user.email
        assert data["id"] == test_user.id
    
    def test_get_current_user_no_token(self, client):
        """Test getting current user without token"""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 403
    
    def test_get_current_user_invalid_token(self, client):
        """Test getting current user with invalid token"""
        headers = {"Authorization": "Bearer invalid-token"}
        response = client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 401

class TestPasswordReset:
    def test_request_password_reset(self, client, test_user):
        """Test password reset request"""
        reset_data = {"email": test_user.email}
        
        response = client.post("/api/v1/auth/password-reset", json=reset_data)
        assert response.status_code == 200
        assert "reset_token" in response.json()  # Only in demo mode
    
    def test_request_password_reset_nonexistent_email(self, client):
        """Test password reset request with nonexistent email"""
        reset_data = {"email": "nonexistent@example.com"}
        
        response = client.post("/api/v1/auth/password-reset", json=reset_data)
        assert response.status_code == 200  # Don't reveal if email exists

class TestAdminEndpoints:
    def test_activate_user_as_admin(self, client, admin_user, test_user):
        """Test activating user as admin"""
        # Login as admin
        login_data = {
            "email": admin_user.email,
            "password": "adminpass123"
        }
        login_response = client.post("/api/v1/auth/login", json=login_data)
        token = login_response.json()["access_token"]
        
        # Activate user
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post(f"/api/v1/auth/users/{test_user.id}/activate", headers=headers)
        assert response.status_code == 200
    
    def test_activate_user_as_non_admin(self, client, test_user):
        """Test activating user as non-admin (should fail)"""
        # Login as regular user
        login_data = {
            "email": test_user.email,
            "password": "testpass123"
        }
        login_response = client.post("/api/v1/auth/login", json=login_data)
        token = login_response.json()["access_token"]
        
        # Try to activate user
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post(f"/api/v1/auth/users/{test_user.id}/activate", headers=headers)
        assert response.status_code == 403

class TestProfileManagement:
    def test_get_user_profile(self, client, test_user):
        """Test getting user profile"""
        # Login first
        login_data = {
            "email": test_user.email,
            "password": "testpass123"
        }
        login_response = client.post("/api/v1/auth/login", json=login_data)
        token = login_response.json()["access_token"]
        
        # Get profile
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/v1/users/profile", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["email"] == test_user.email
        assert data["full_name"] == test_user.full_name
    
    def test_update_user_profile(self, client, test_user):
        """Test updating user profile"""
        # Login first
        login_data = {
            "email": test_user.email,
            "password": "testpass123"
        }
        login_response = client.post("/api/v1/auth/login", json=login_data)
        token = login_response.json()["access_token"]
        
        # Update profile
        update_data = {
            "full_name": "Updated Name",
            "phone": "+919876543299"
        }
        headers = {"Authorization": f"Bearer {token}"}
        response = client.put("/api/v1/users/profile", json=update_data, headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["full_name"] == "Updated Name"
        assert data["phone"] == "+919876543299"
    
    def test_update_profile_duplicate_email(self, client, test_user):
        """Test updating profile with duplicate email"""
        # Create another user
        db = TestingSessionLocal()
        another_user = User(
            email="another@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="Another User",
            role=UserRole.PASSENGER,
            is_active=True,
            is_verified=True
        )
        db.add(another_user)
        db.commit()
        
        # Login as test user
        login_data = {
            "email": test_user.email,
            "password": "testpass123"
        }
        login_response = client.post("/api/v1/auth/login", json=login_data)
        token = login_response.json()["access_token"]
        
        # Try to update with another user's email
        update_data = {"email": "another@example.com"}
        headers = {"Authorization": f"Bearer {token}"}
        response = client.put("/api/v1/users/profile", json=update_data, headers=headers)
        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]
        
        # Cleanup
        db.delete(another_user)
        db.commit()
        db.close()

class TestUserManagement:
    def test_list_users_as_admin(self, client, admin_user, test_user):
        """Test listing users as admin"""
        # Login as admin
        login_data = {
            "email": admin_user.email,
            "password": "adminpass123"
        }
        login_response = client.post("/api/v1/auth/login", json=login_data)
        token = login_response.json()["access_token"]
        
        # List users
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/v1/users/", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2  # At least admin and test user
    
    def test_list_users_as_non_admin(self, client, test_user):
        """Test listing users as non-admin (should fail)"""
        # Login as regular user
        login_data = {
            "email": test_user.email,
            "password": "testpass123"
        }
        login_response = client.post("/api/v1/auth/login", json=login_data)
        token = login_response.json()["access_token"]
        
        # Try to list users
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/v1/users/", headers=headers)
        assert response.status_code == 403
    
    def test_get_user_by_id_as_admin(self, client, admin_user, test_user):
        """Test getting user by ID as admin"""
        # Login as admin
        login_data = {
            "email": admin_user.email,
            "password": "adminpass123"
        }
        login_response = client.post("/api/v1/auth/login", json=login_data)
        token = login_response.json()["access_token"]
        
        # Get user by ID
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get(f"/api/v1/users/{test_user.id}", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == test_user.id
        assert data["email"] == test_user.email
    
    def test_update_user_as_admin(self, client, admin_user, test_user):
        """Test updating user as admin"""
        # Login as admin
        login_data = {
            "email": admin_user.email,
            "password": "adminpass123"
        }
        login_response = client.post("/api/v1/auth/login", json=login_data)
        token = login_response.json()["access_token"]
        
        # Update user
        update_data = {
            "full_name": "Admin Updated Name",
            "is_active": False
        }
        headers = {"Authorization": f"Bearer {token}"}
        response = client.put(f"/api/v1/users/{test_user.id}", json=update_data, headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["full_name"] == "Admin Updated Name"
        assert data["is_active"] is False