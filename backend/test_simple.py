#!/usr/bin/env python3
"""
Simple test to verify repository functionality without external dependencies
"""
import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.append(str(Path(__file__).parent))

def test_repository_imports():
    """Test that all repository classes can be imported"""
    try:
        from app.repositories.base import BaseRepository
        from app.repositories.vehicle import VehicleRepository
        from app.repositories.route import RouteRepository
        from app.repositories.stop import StopRepository
        from app.repositories.subscription import SubscriptionRepository
        from app.repositories.location import VehicleLocationRepository
        from app.repositories.factory import RepositoryFactory
        
        print("✅ All repository classes imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_model_imports():
    """Test that all model classes can be imported"""
    try:
        from app.models.vehicle import Vehicle, VehicleStatus
        from app.models.route import Route
        from app.models.stop import Stop
        from app.models.subscription import Subscription, NotificationChannel
        from app.models.location import VehicleLocation
        
        print("✅ All model classes imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Model import error: {e}")
        return False

def test_database_config():
    """Test database configuration"""
    try:
        from app.core.config import Settings
        
        # Test that settings can be instantiated
        settings = Settings()
        print(f"✅ Database configuration loaded: {settings.DATABASE_URL}")
        return True
    except Exception as e:
        print(f"❌ Database config error: {e}")
        return False

if __name__ == "__main__":
    print("Running simple repository tests...")
    
    tests = [
        test_model_imports,
        test_repository_imports,
        test_database_config,
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n{passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All basic tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed")
        sys.exit(1)