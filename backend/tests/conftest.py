"""
Test configuration and fixtures
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.models import *  # Import all models

# Use in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test"""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def sample_vehicle_data():
    """Sample vehicle data for testing"""
    return {
        "vehicle_number": "KA01-TEST",
        "capacity": 40,
        "status": "active"
    }

@pytest.fixture
def sample_route_data():
    """Sample route data for testing"""
    return {
        "name": "Test Route",
        "route_number": "TEST1",
        "geojson": '{"type":"LineString","coordinates":[[77.5946,12.9716],[77.6648,12.8456]]}',
        "polyline": "test_polyline_data",
        "is_active": True
    }

@pytest.fixture
def sample_stop_data():
    """Sample stop data for testing"""
    return {
        "route_id": 1,
        "name": "Test Stop",
        "name_kannada": "ಟೆಸ್ಟ್ ಸ್ಟಾಪ್",
        "latitude": 12.9716,
        "longitude": 77.5946,
        "stop_order": 1
    }