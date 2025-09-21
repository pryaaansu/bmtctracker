#!/usr/bin/env python3
"""
Simple repository functionality test
"""
import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.append(str(Path(__file__).parent))

def test_repository_structure():
    """Test repository class structure and methods"""
    print("Testing repository structure...")
    
    # Test that we can create a mock repository
    from app.repositories.base import BaseRepository
    from typing import TypeVar
    
    # Create mock types
    ModelType = TypeVar("ModelType")
    CreateType = TypeVar("CreateType")
    UpdateType = TypeVar("UpdateType")
    
    class MockModel:
        __tablename__ = "test_table"
        id = 1
        
        class __table__:
            columns = []
    
    class MockSession:
        def query(self, model):
            return self
        def filter(self, condition):
            return self
        def first(self):
            return MockModel()
        def all(self):
            return [MockModel()]
        def add(self, obj):
            pass
        def commit(self):
            pass
        def refresh(self, obj):
            pass
        def rollback(self):
            pass
        def delete(self, obj):
            pass
        def count(self):
            return 1
    
    # Test base repository instantiation
    try:
        class TestRepo(BaseRepository[MockModel, dict, dict]):
            pass
        
        repo = TestRepo(MockModel, MockSession())
        
        # Test cache key generation
        cache_key = repo._get_cache_key("test", "123")
        assert "test_table:test:123" == cache_key
        
        # Test model to dict conversion
        model_dict = repo._model_to_dict(MockModel())
        assert isinstance(model_dict, dict)
        
        print("✅ Base repository structure test passed")
        return True
        
    except Exception as e:
        print(f"❌ Repository structure test failed: {e}")
        return False

def test_specific_repositories():
    """Test specific repository classes can be instantiated"""
    print("Testing specific repository classes...")
    
    try:
        from app.repositories.vehicle import VehicleRepository
        from app.repositories.route import RouteRepository
        from app.repositories.stop import StopRepository
        from app.repositories.subscription import SubscriptionRepository
        from app.repositories.location import VehicleLocationRepository
        
        # Mock session
        class MockSession:
            def query(self, model):
                return self
            def filter(self, condition):
                return self
            def first(self):
                return None
            def all(self):
                return []
        
        session = MockSession()
        
        # Test instantiation
        vehicle_repo = VehicleRepository(session)
        route_repo = RouteRepository(session)
        stop_repo = StopRepository(session)
        subscription_repo = SubscriptionRepository(session)
        location_repo = VehicleLocationRepository(session)
        
        # Test that they have expected methods
        assert hasattr(vehicle_repo, 'get_by_vehicle_number')
        assert hasattr(route_repo, 'get_by_route_number')
        assert hasattr(stop_repo, 'search_stops')
        assert hasattr(subscription_repo, 'get_by_phone')
        assert hasattr(location_repo, 'get_latest_by_vehicle')
        
        print("✅ Specific repository classes test passed")
        return True
        
    except Exception as e:
        print(f"❌ Specific repository test failed: {e}")
        return False

def test_repository_factory():
    """Test repository factory"""
    print("Testing repository factory...")
    
    try:
        from app.repositories.factory import RepositoryFactory
        
        class MockSession:
            pass
        
        factory = RepositoryFactory(MockSession())
        
        # Test that properties exist
        assert hasattr(factory, 'vehicle')
        assert hasattr(factory, 'route')
        assert hasattr(factory, 'stop')
        assert hasattr(factory, 'subscription')
        assert hasattr(factory, 'location')
        
        print("✅ Repository factory test passed")
        return True
        
    except Exception as e:
        print(f"❌ Repository factory test failed: {e}")
        return False

def test_cache_functionality():
    """Test caching functionality"""
    print("Testing cache functionality...")
    
    try:
        from app.repositories.base import BaseRepository
        
        class MockModel:
            __tablename__ = "test_table"
            id = 1
        
        class MockSession:
            pass
        
        class TestRepo(BaseRepository[MockModel, dict, dict]):
            pass
        
        repo = TestRepo(MockModel, MockSession())
        
        # Test cache key generation
        key = repo._get_cache_key("prefix", "identifier")
        assert key == "test_table:prefix:identifier"
        
        # Test that cache methods exist and don't crash
        repo._cache_get("test_key")  # Should return None when Redis unavailable
        repo._cache_set("test_key", {"test": "data"})  # Should not crash
        repo._cache_delete("test_key")  # Should not crash
        repo._cache_delete_pattern("test_*")  # Should not crash
        
        print("✅ Cache functionality test passed")
        return True
        
    except Exception as e:
        print(f"❌ Cache functionality test failed: {e}")
        return False

if __name__ == "__main__":
    print("Running simple repository tests...")
    
    tests = [
        test_repository_structure,
        test_specific_repositories,
        test_repository_factory,
        test_cache_functionality,
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
        print()  # Add spacing between tests
    
    print(f"{passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All repository tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed")
        sys.exit(1)