from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import hashlib
import json
import redis
from fastapi import HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends, Request

from ..models.api_key import APIKey, APIUsageLog, APIRateLimit
from ..core.config import settings

# Redis client for rate limiting (optional, falls back to in-memory)
try:
    redis_client = redis.Redis(
        host=getattr(settings, 'REDIS_HOST', 'localhost'),
        port=getattr(settings, 'REDIS_PORT', 6379),
        db=getattr(settings, 'REDIS_DB', 0),
        decode_responses=True
    )
    redis_client.ping()  # Test connection
    REDIS_AVAILABLE = True
except:
    REDIS_AVAILABLE = False
    # In-memory storage for rate limiting
    _rate_limit_cache = {}

class APIAuthService:
    """Service for API key authentication and rate limiting"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def authenticate_api_key(self, api_key: str) -> Optional[APIKey]:
        """Authenticate an API key and return the key object if valid"""
        if not api_key:
            return None
        
        # Hash the provided key
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        # Find the API key
        api_key_obj = self.db.query(APIKey).filter(
            and_(
                APIKey.key_hash == key_hash,
                APIKey.is_active == True
            )
        ).first()
        
        if not api_key_obj or not api_key_obj.is_valid():
            return None
        
        return api_key_obj
    
    def check_rate_limit(self, api_key: APIKey, endpoint: str) -> Dict[str, Any]:
        """Check if the API key can make a request based on rate limits"""
        now = datetime.utcnow()
        
        # Get current usage from cache or database
        current_usage = self._get_current_usage(api_key.id)
        
        # Check if key can make request
        if not api_key.can_make_request(current_usage):
            return {
                'allowed': False,
                'reason': 'rate_limit_exceeded',
                'retry_after': self._get_retry_after(api_key, current_usage)
            }
        
        # Check permissions
        if not api_key.has_permission(endpoint):
            return {
                'allowed': False,
                'reason': 'permission_denied',
                'retry_after': None
            }
        
        # Record the request
        updated_usage = api_key.record_request(current_usage)
        self._update_usage_cache(api_key.id, updated_usage)
        
        # Update database
        self.db.commit()
        
        return {
            'allowed': True,
            'reason': None,
            'retry_after': None,
            'usage': updated_usage
        }
    
    def log_api_usage(
        self,
        api_key_id: int,
        endpoint: str,
        method: str,
        status_code: int,
        response_time_ms: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_size_bytes: Optional[int] = None,
        response_size_bytes: Optional[int] = None,
        error_message: Optional[str] = None
    ):
        """Log API usage for monitoring and analytics"""
        usage_log = APIUsageLog(
            api_key_id=api_key_id,
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            response_time_ms=response_time_ms,
            ip_address=ip_address,
            user_agent=user_agent,
            request_size_bytes=request_size_bytes,
            response_size_bytes=response_size_bytes,
            error_message=error_message
        )
        
        self.db.add(usage_log)
        self.db.commit()
    
    def create_api_key(
        self,
        key_name: str,
        permissions: Optional[list] = None,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        requests_per_day: int = 10000,
        expires_in_days: Optional[int] = None,
        created_by: Optional[int] = None,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new API key"""
        # Generate key
        key, key_hash, key_prefix = APIKey.generate_key()
        
        # Set expiration
        expires_at = None
        if expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
        
        # Create API key object
        api_key_obj = APIKey(
            key_name=key_name,
            key_hash=key_hash,
            key_prefix=key_prefix,
            permissions=json.dumps(permissions) if permissions else None,
            requests_per_minute=requests_per_minute,
            requests_per_hour=requests_per_hour,
            requests_per_day=requests_per_day,
            expires_at=expires_at,
            created_by=created_by,
            description=description
        )
        
        self.db.add(api_key_obj)
        self.db.commit()
        self.db.refresh(api_key_obj)
        
        return {
            'id': api_key_obj.id,
            'key': key,  # Only returned once
            'key_name': api_key_obj.key_name,
            'key_prefix': api_key_obj.key_prefix,
            'permissions': permissions,
            'rate_limits': {
                'requests_per_minute': requests_per_minute,
                'requests_per_hour': requests_per_hour,
                'requests_per_day': requests_per_day
            },
            'expires_at': expires_at.isoformat() if expires_at else None,
            'created_at': api_key_obj.created_at.isoformat()
        }
    
    def revoke_api_key(self, api_key_id: int) -> bool:
        """Revoke an API key"""
        api_key = self.db.query(APIKey).filter(APIKey.id == api_key_id).first()
        if not api_key:
            return False
        
        api_key.is_active = False
        self.db.commit()
        return True
    
    def get_api_key_stats(self, api_key_id: int, days: int = 30) -> Dict[str, Any]:
        """Get usage statistics for an API key"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get usage logs
        usage_logs = self.db.query(APIUsageLog).filter(
            and_(
                APIUsageLog.api_key_id == api_key_id,
                APIUsageLog.created_at >= start_date,
                APIUsageLog.created_at <= end_date
            )
        ).all()
        
        # Calculate statistics
        total_requests = len(usage_logs)
        successful_requests = len([log for log in usage_logs if 200 <= log.status_code < 300])
        error_requests = len([log for log in usage_logs if log.status_code >= 400])
        
        # Average response time
        response_times = [log.response_time_ms for log in usage_logs if log.response_time_ms]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        # Most used endpoints
        endpoint_usage = {}
        for log in usage_logs:
            endpoint_usage[log.endpoint] = endpoint_usage.get(log.endpoint, 0) + 1
        
        most_used_endpoints = sorted(
            endpoint_usage.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        return {
            'total_requests': total_requests,
            'successful_requests': successful_requests,
            'error_requests': error_requests,
            'success_rate': (successful_requests / total_requests * 100) if total_requests > 0 else 0,
            'average_response_time_ms': round(avg_response_time, 2),
            'most_used_endpoints': most_used_endpoints,
            'period_days': days
        }
    
    def _get_current_usage(self, api_key_id: int) -> Dict[str, int]:
        """Get current usage from cache or database"""
        if REDIS_AVAILABLE:
            # Use Redis for distributed rate limiting
            cache_key = f"api_usage:{api_key_id}"
            cached_data = redis_client.hgetall(cache_key)
            return {k: int(v) for k, v in cached_data.items()}
        else:
            # Use in-memory cache
            return _rate_limit_cache.get(api_key_id, {})
    
    def _update_usage_cache(self, api_key_id: int, usage: Dict[str, int]):
        """Update usage cache"""
        if REDIS_AVAILABLE:
            cache_key = f"api_usage:{api_key_id}"
            redis_client.hset(cache_key, mapping=usage)
            redis_client.expire(cache_key, 86400)  # Expire after 24 hours
        else:
            _rate_limit_cache[api_key_id] = usage
    
    def _get_retry_after(self, api_key: APIKey, current_usage: Dict[str, int]) -> int:
        """Calculate retry after seconds for rate limited requests"""
        now = datetime.utcnow()
        
        # Check minute limit
        minute_key = f"minute_{now.strftime('%Y-%m-%d-%H-%M')}"
        if current_usage.get(minute_key, 0) >= api_key.requests_per_minute:
            return 60  # Wait until next minute
        
        # Check hour limit
        hour_key = f"hour_{now.strftime('%Y-%m-%d-%H')}"
        if current_usage.get(hour_key, 0) >= api_key.requests_per_hour:
            return 3600  # Wait until next hour
        
        # Check day limit
        day_key = f"day_{now.strftime('%Y-%m-%d')}"
        if current_usage.get(day_key, 0) >= api_key.requests_per_day:
            return 86400  # Wait until next day
        
        return 0

# FastAPI dependency for API key authentication
security = HTTPBearer()

async def get_api_key(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> APIKey:
    """FastAPI dependency to authenticate API key"""
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required"
        )
    
    auth_service = APIAuthService(db)
    api_key = auth_service.authenticate_api_key(credentials.credentials)
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    return api_key

async def check_rate_limit(
    request: Request,
    api_key: APIKey = Depends(get_api_key),
    db: Session = Depends(get_db)
) -> APIKey:
    """FastAPI dependency to check rate limits"""
    auth_service = APIAuthService(db)
    endpoint = f"{request.method} {request.url.path}"
    
    rate_limit_result = auth_service.check_rate_limit(api_key, endpoint)
    
    if not rate_limit_result['allowed']:
        if rate_limit_result['reason'] == 'rate_limit_exceeded':
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
                headers={"Retry-After": str(rate_limit_result['retry_after'])}
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied"
            )
    
    return api_key

