from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from .database import get_db
from .auth import verify_token
from ..models.user import User, UserRole
from ..models.driver import Driver
from ..repositories.factory import RepositoryFactory, get_repositories
from ..repositories.driver import DriverRepository

# Security scheme
security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user"""
    token = credentials.credentials
    payload = verify_token(token)
    
    user_id = payload.get("user_id")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    repos = get_repositories(db)
    user = repos.user.get(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user

def get_admin_user(current_user: User = Depends(get_current_active_user)) -> User:
    """Get current user if they are an admin"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

def get_driver_user(current_user: User = Depends(get_current_active_user)) -> User:
    """Get current user if they are a driver"""
    if current_user.role != UserRole.DRIVER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Driver access required"
        )
    return current_user

def get_admin_or_driver_user(current_user: User = Depends(get_current_active_user)) -> User:
    """Get current user if they are admin or driver"""
    if current_user.role not in [UserRole.ADMIN, UserRole.DRIVER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or driver access required"
        )
    return current_user

# Alias for backward compatibility
get_current_admin_user = get_admin_user

# Optional authentication (for public endpoints that can benefit from user context)
def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get current user if authenticated, otherwise None"""
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        payload = verify_token(token)
        user_id = payload.get("user_id")
        
        if user_id is None:
            return None
        
        repos = get_repositories(db)
        user = repos.user.get(user_id)
        
        if user is None or not user.is_active:
            return None
        
        return user
    except:
        return None

def get_current_driver(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Driver:
    """Get current authenticated driver"""
    token = credentials.credentials
    payload = verify_token(token)
    
    # Check if this is a driver token
    token_type = payload.get("type")
    if token_type != "driver":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Driver authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    driver_id = payload.get("sub")
    if driver_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    driver_repo = DriverRepository(db)
    driver = driver_repo.get(int(driver_id))
    if driver is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Driver not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return driver