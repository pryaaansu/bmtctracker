import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import get_db, Base
from app.models.user import User, UserRole
from app.core.auth import get_password_hash

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_auth_integration.db"
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

class TestAuthenticationIntegration:
    """Integration tests for the complete authentication flow"""
    
    def test_complete_user_journey(self, client):
        """Test complete user journey from registration to profile management"""
        
        # 1. Register a new user
        user_data = {
            "email": "journey@example.com",
            "password": "journey123",
            "full_name": "Journey User",
            "phone": "+919876543220",
            "role": "passenger"
        }
        
        register_response = client.post("/api/v1/auth/register", json=user_data)
        assert register_response.status_code == 200
        user_id = register_response.json()["id"]
        
        # 2. Login with the new user
        login_data = {
            "email": user_data["email"],
            "password": user_data["password"]
        }
        
        login_response = client.post("/api/v1/auth/login", json=login_data)
        assert login_response.status_code == 200
        
        token_data = login_response.json()
        assert "access_token" in token_data
        assert token_data["user"]["email"] == user_data["email"]
        
        token = token_data["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 3. Get current user info
        me_response = client.get("/api/v1/auth/me", headers=headers)
        assert me_response.status_code == 200
        assert me_response.json()["email"] == user_data["email"]
        
        # 4. Get user profile
        profile_response = client.get("/api/v1/users/profile", headers=headers)
        assert profile_response.status_code == 200
        assert profile_response.json()["full_name"] == user_data["full_name"]
        
        # 5. Update user profile
        update_data = {
            "full_name": "Updated Journey User",
            "phone": "+919876543221"
        }
        
        update_response = client.put("/api/v1/users/profile", json=update_data, headers=headers)
        assert update_response.status_code == 200
        
        updated_user = update_response.json()
        assert updated_user["full_name"] == "Updated Journey User"
        assert updated_user["phone"] == "+919876543221"
        
        # 6. Change password
        password_change_data = {
            "current_password": "journey123",
            "new_password": "newjourney123"
        }
        
        change_password_response = client.post("/api/v1/auth/change-password", json=password_change_data, headers=headers)
        assert change_password_response.status_code == 200
        
        # 7. Login with new password
        new_login_data = {
            "email": user_data["email"],
            "password": "newjourney123"
        }
        
        new_login_response = client.post("/api/v1/auth/login", json=new_login_data)
        assert new_login_response.status_code == 200
        
        # 8. Verify old password doesn't work
        old_login_response = client.post("/api/v1/auth/login", json=login_data)
        assert old_login_response.status_code == 401
    
    def test_admin_user_management_flow(self, client):
        """Test admin user management capabilities"""
        
        # 1. Create admin user
        db = TestingSessionLocal()
        admin_user = User(
            email="admin@integration.com",
            hashed_password=get_password_hash("admin123"),
            full_name="Integration Admin",
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True
        )
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        # 2. Create regular user
        regular_user = User(
            email="user@integration.com",
            hashed_password=get_password_hash("user123"),
            full_name="Integration User",
            role=UserRole.PASSENGER,
            is_active=True,
            is_verified=True
        )
        db.add(regular_user)
        db.commit()
        db.refresh(regular_user)
        db.close()
        
        # 3. Login as admin
        admin_login_data = {
            "email": "admin@integration.com",
            "password": "admin123"
        }
        
        admin_login_response = client.post("/api/v1/auth/login", json=admin_login_data)
        assert admin_login_response.status_code == 200
        
        admin_token = admin_login_response.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        
        # 4. List all users
        users_response = client.get("/api/v1/users/", headers=admin_headers)
        assert users_response.status_code == 200
        
        users = users_response.json()
        assert len(users) >= 2
        
        # 5. Get specific user
        user_response = client.get(f"/api/v1/users/{regular_user.id}", headers=admin_headers)
        assert user_response.status_code == 200
        assert user_response.json()["email"] == "user@integration.com"
        
        # 6. Update user as admin
        admin_update_data = {
            "full_name": "Admin Updated User",
            "is_active": False
        }
        
        admin_update_response = client.put(f"/api/v1/users/{regular_user.id}", json=admin_update_data, headers=admin_headers)
        assert admin_update_response.status_code == 200
        
        updated_user = admin_update_response.json()
        assert updated_user["full_name"] == "Admin Updated User"
        assert updated_user["is_active"] is False
        
        # 7. Activate user
        activate_response = client.post(f"/api/v1/auth/users/{regular_user.id}/activate", headers=admin_headers)
        assert activate_response.status_code == 200
        assert activate_response.json()["is_active"] is True
        
        # 8. Deactivate user
        deactivate_response = client.post(f"/api/v1/auth/users/{regular_user.id}/deactivate", headers=admin_headers)
        assert deactivate_response.status_code == 200
        assert deactivate_response.json()["is_active"] is False
    
    def test_role_based_access_control(self, client):
        """Test role-based access control"""
        
        # Create users with different roles
        db = TestingSessionLocal()
        
        passenger = User(
            email="passenger@rbac.com",
            hashed_password=get_password_hash("pass123"),
            role=UserRole.PASSENGER,
            is_active=True,
            is_verified=True
        )
        
        driver = User(
            email="driver@rbac.com",
            hashed_password=get_password_hash("driver123"),
            role=UserRole.DRIVER,
            is_active=True,
            is_verified=True
        )
        
        admin = User(
            email="admin@rbac.com",
            hashed_password=get_password_hash("admin123"),
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True
        )
        
        db.add_all([passenger, driver, admin])
        db.commit()
        db.close()
        
        # Test passenger access
        passenger_login = client.post("/api/v1/auth/login", json={
            "email": "passenger@rbac.com",
            "password": "pass123"
        })
        passenger_token = passenger_login.json()["access_token"]
        passenger_headers = {"Authorization": f"Bearer {passenger_token}"}
        
        # Passenger should NOT access admin endpoints
        admin_response = client.get("/api/v1/users/", headers=passenger_headers)
        assert admin_response.status_code == 403
        
        # Passenger should access their own profile
        profile_response = client.get("/api/v1/users/profile", headers=passenger_headers)
        assert profile_response.status_code == 200
        
        # Test admin access
        admin_login = client.post("/api/v1/auth/login", json={
            "email": "admin@rbac.com",
            "password": "admin123"
        })
        admin_token = admin_login.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Admin should access admin endpoints
        admin_users_response = client.get("/api/v1/users/", headers=admin_headers)
        assert admin_users_response.status_code == 200
        
        # Admin should access their own profile
        admin_profile_response = client.get("/api/v1/users/profile", headers=admin_headers)
        assert admin_profile_response.status_code == 200
    
    def test_password_reset_flow(self, client):
        """Test password reset functionality"""
        
        # Create a user
        db = TestingSessionLocal()
        user = User(
            email="reset@example.com",
            hashed_password=get_password_hash("original123"),
            full_name="Reset User",
            is_active=True,
            is_verified=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        db.close()
        
        # 1. Request password reset
        reset_request = client.post("/api/v1/auth/password-reset", json={
            "email": "reset@example.com"
        })
        assert reset_request.status_code == 200
        
        # In demo mode, we get the reset token
        reset_token = reset_request.json().get("reset_token")
        assert reset_token is not None
        
        # 2. Confirm password reset
        reset_confirm = client.post("/api/v1/auth/password-reset/confirm", json={
            "token": reset_token,
            "new_password": "newreset123"
        })
        assert reset_confirm.status_code == 200
        
        # 3. Login with new password
        new_login = client.post("/api/v1/auth/login", json={
            "email": "reset@example.com",
            "password": "newreset123"
        })
        assert new_login.status_code == 200
        
        # 4. Verify old password doesn't work
        old_login = client.post("/api/v1/auth/login", json={
            "email": "reset@example.com",
            "password": "original123"
        })
        assert old_login.status_code == 401