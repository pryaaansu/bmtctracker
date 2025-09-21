"""
Base repository class with common CRUD operations and caching
"""
from typing import Generic, TypeVar, Type, List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from pydantic import BaseModel
import redis
import json
import logging
from abc import ABC, abstractmethod

try:
    from ..core.config import settings
except ImportError:
    from ..core.simple_config import simple_settings as settings

logger = logging.getLogger(__name__)

# Type variables for generic repository
ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType], ABC):
    """Base repository class with CRUD operations and Redis caching"""
    
    def __init__(self, model: Type[ModelType], db: Session):
        self.model = model
        self.db = db
        self._redis_client = None
        self._cache_ttl = 300  # 5 minutes default TTL
    
    @property
    def redis_client(self) -> Optional[redis.Redis]:
        """Get Redis client with lazy initialization"""
        if self._redis_client is None:
            try:
                self._redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
                # Test connection
                self._redis_client.ping()
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}. Caching disabled.")
                self._redis_client = None
        return self._redis_client
    
    def _get_cache_key(self, prefix: str, identifier: Any) -> str:
        """Generate cache key"""
        return f"{self.model.__tablename__}:{prefix}:{identifier}"
    
    def _cache_get(self, key: str) -> Optional[Dict]:
        """Get data from cache"""
        if not self.redis_client:
            return None
        try:
            data = self.redis_client.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.warning(f"Cache get error: {e}")
            return None
    
    def _cache_set(self, key: str, data: Dict, ttl: Optional[int] = None) -> None:
        """Set data in cache"""
        if not self.redis_client:
            return
        try:
            ttl = ttl or self._cache_ttl
            self.redis_client.setex(key, ttl, json.dumps(data, default=str))
        except Exception as e:
            logger.warning(f"Cache set error: {e}")
    
    def _cache_delete(self, key: str) -> None:
        """Delete data from cache"""
        if not self.redis_client:
            return
        try:
            self.redis_client.delete(key)
        except Exception as e:
            logger.warning(f"Cache delete error: {e}")
    
    def _cache_delete_pattern(self, pattern: str) -> None:
        """Delete cache keys matching pattern"""
        if not self.redis_client:
            return
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
        except Exception as e:
            logger.warning(f"Cache pattern delete error: {e}")
    
    def _model_to_dict(self, model_instance: ModelType) -> Dict:
        """Convert SQLAlchemy model to dictionary"""
        return {c.name: getattr(model_instance, c.name) for c in model_instance.__table__.columns}
    
    def get(self, id: Any, use_cache: bool = True) -> Optional[ModelType]:
        """Get a single record by ID with caching"""
        cache_key = self._get_cache_key("id", id)
        
        # Try cache first
        if use_cache:
            cached_data = self._cache_get(cache_key)
            if cached_data:
                logger.debug(f"Cache hit for {cache_key}")
                # Note: This returns dict, not model instance
                # In production, you might want to reconstruct the model
                return cached_data
        
        try:
            instance = self.db.query(self.model).filter(self.model.id == id).first()
            if instance and use_cache:
                self._cache_set(cache_key, self._model_to_dict(instance))
            return instance
        except SQLAlchemyError as e:
            logger.error(f"Database error in get: {e}")
            raise
    
    def get_multi(self, skip: int = 0, limit: int = 100, use_cache: bool = True) -> List[ModelType]:
        """Get multiple records with pagination"""
        cache_key = self._get_cache_key("multi", f"{skip}:{limit}")
        
        if use_cache:
            cached_data = self._cache_get(cache_key)
            if cached_data:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_data
        
        try:
            instances = self.db.query(self.model).offset(skip).limit(limit).all()
            if use_cache:
                data = [self._model_to_dict(instance) for instance in instances]
                self._cache_set(cache_key, data, ttl=60)  # Shorter TTL for lists
            return instances
        except SQLAlchemyError as e:
            logger.error(f"Database error in get_multi: {e}")
            raise
    
    def create(self, obj_in: CreateSchemaType) -> ModelType:
        """Create a new record"""
        try:
            obj_data = obj_in.dict() if hasattr(obj_in, 'dict') else obj_in
            db_obj = self.model(**obj_data)
            self.db.add(db_obj)
            self.db.commit()
            self.db.refresh(db_obj)
            
            # Invalidate related cache
            self._cache_delete_pattern(f"{self.model.__tablename__}:*")
            
            return db_obj
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error in create: {e}")
            raise
    
    def update(self, db_obj: ModelType, obj_in: UpdateSchemaType) -> ModelType:
        """Update an existing record"""
        try:
            obj_data = obj_in.dict(exclude_unset=True) if hasattr(obj_in, 'dict') else obj_in
            
            for field, value in obj_data.items():
                if hasattr(db_obj, field):
                    setattr(db_obj, field, value)
            
            self.db.add(db_obj)
            self.db.commit()
            self.db.refresh(db_obj)
            
            # Invalidate cache for this object
            cache_key = self._get_cache_key("id", db_obj.id)
            self._cache_delete(cache_key)
            self._cache_delete_pattern(f"{self.model.__tablename__}:multi:*")
            
            return db_obj
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error in update: {e}")
            raise
    
    def delete(self, id: Any) -> Optional[ModelType]:
        """Delete a record by ID"""
        try:
            obj = self.db.query(self.model).filter(self.model.id == id).first()
            if obj:
                self.db.delete(obj)
                self.db.commit()
                
                # Invalidate cache
                cache_key = self._get_cache_key("id", id)
                self._cache_delete(cache_key)
                self._cache_delete_pattern(f"{self.model.__tablename__}:multi:*")
                
            return obj
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error in delete: {e}")
            raise
    
    def count(self) -> int:
        """Get total count of records"""
        cache_key = self._get_cache_key("count", "all")
        
        cached_count = self._cache_get(cache_key)
        if cached_count is not None:
            return cached_count
        
        try:
            count = self.db.query(self.model).count()
            self._cache_set(cache_key, count, ttl=60)  # Short TTL for counts
            return count
        except SQLAlchemyError as e:
            logger.error(f"Database error in count: {e}")
            raise
    
    def exists(self, id: Any) -> bool:
        """Check if record exists"""
        try:
            return self.db.query(self.model).filter(self.model.id == id).first() is not None
        except SQLAlchemyError as e:
            logger.error(f"Database error in exists: {e}")
            raise