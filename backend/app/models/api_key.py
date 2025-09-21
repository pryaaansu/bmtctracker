from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, func
from sqlalchemy.orm import relationship
from ..core.database import Base
from datetime import datetime, timedelta
from typing import Optional
import secrets
import hashlib

class APIKey(Base):
    """API Key model for public API access"""
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    key_name = Column(String(100), nullable=False)  # Human-readable name for the key
    key_hash = Column(String(64), nullable=False, unique=True)  # SHA-256 hash of the key
    key_prefix = Column(String(8), nullable=False)  # First 8 characters for identification
    
    # Access control
    is_active = Column(Boolean, default=True)
    permissions = Column(Text, nullable=True)  # JSON string of allowed endpoints
    
    # Rate limiting
    requests_per_minute = Column(Integer, default=60)
    requests_per_hour = Column(Integer, default=1000)
    requests_per_day = Column(Integer, default=10000)
    
    # Usage tracking
    total_requests = Column(Integer, default=0)
    last_used = Column(DateTime(timezone=True), nullable=True)
    
    # Expiration
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    created_by = Column(Integer, nullable=True)  # User ID who created the key
    description = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    @staticmethod
    def generate_key() -> tuple[str, str]:
        """Generate a new API key and return (key, hash)"""
        # Generate a secure random key
        key = f"bmtc_{secrets.token_urlsafe(32)}"
        
        # Create hash for storage
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        
        # Get prefix for identification
        key_prefix = key[:8]
        
        return key, key_hash, key_prefix

    def is_valid(self) -> bool:
        """Check if the API key is valid and not expired"""
        if not self.is_active:
            return False
        
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return False
        
        return True

    def has_permission(self, endpoint: str) -> bool:
        """Check if the API key has permission to access a specific endpoint"""
        if not self.permissions:
            return True  # No restrictions if permissions not set
        
        try:
            import json
            allowed_endpoints = json.loads(self.permissions)
            return endpoint in allowed_endpoints
        except (json.JSONDecodeError, TypeError):
            return True  # Allow access if permissions are malformed

    def can_make_request(self, current_requests: dict) -> bool:
        """Check if the API key can make a request based on rate limits"""
        now = datetime.utcnow()
        
        # Check minute limit
        minute_key = now.strftime("%Y-%m-%d-%H-%M")
        if current_requests.get(f"minute_{minute_key}", 0) >= self.requests_per_minute:
            return False
        
        # Check hour limit
        hour_key = now.strftime("%Y-%m-%d-%H")
        if current_requests.get(f"hour_{hour_key}", 0) >= self.requests_per_hour:
            return False
        
        # Check day limit
        day_key = now.strftime("%Y-%m-%d")
        if current_requests.get(f"day_{day_key}", 0) >= self.requests_per_day:
            return False
        
        return True

    def record_request(self, current_requests: dict) -> dict:
        """Record a request and return updated request counts"""
        now = datetime.utcnow()
        
        # Update counters
        minute_key = f"minute_{now.strftime('%Y-%m-%d-%H-%M')}"
        hour_key = f"hour_{now.strftime('%Y-%m-%d-%H')}"
        day_key = f"day_{now.strftime('%Y-%m-%d')}"
        
        current_requests[minute_key] = current_requests.get(minute_key, 0) + 1
        current_requests[hour_key] = current_requests.get(hour_key, 0) + 1
        current_requests[day_key] = current_requests.get(day_key, 0) + 1
        
        # Update database fields
        self.total_requests += 1
        self.last_used = now
        
        return current_requests

class APIUsageLog(Base):
    """Log API usage for monitoring and analytics"""
    __tablename__ = "api_usage_logs"

    id = Column(Integer, primary_key=True, index=True)
    api_key_id = Column(Integer, nullable=False)
    endpoint = Column(String(200), nullable=False)
    method = Column(String(10), nullable=False)
    status_code = Column(Integer, nullable=False)
    response_time_ms = Column(Integer, nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(Text, nullable=True)
    
    # Request details
    request_size_bytes = Column(Integer, nullable=True)
    response_size_bytes = Column(Integer, nullable=True)
    
    # Error tracking
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    api_key = relationship("APIKey", foreign_keys=[api_key_id])

class APIRateLimit(Base):
    """Rate limiting configuration and current state"""
    __tablename__ = "api_rate_limits"

    id = Column(Integer, primary_key=True, index=True)
    api_key_id = Column(Integer, nullable=False)
    
    # Time window
    window_type = Column(String(20), nullable=False)  # 'minute', 'hour', 'day'
    window_start = Column(DateTime(timezone=True), nullable=False)
    window_end = Column(DateTime(timezone=True), nullable=False)
    
    # Current usage
    request_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    api_key = relationship("APIKey", foreign_keys=[api_key_id])

