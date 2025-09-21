from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ....core.database import get_db
from ....core.auth import create_access_token, create_token_data
from ....core.config import settings
from ....core.dependencies import get_current_active_user, get_admin_user
from ....repositories.factory import get_repositories
from ....schemas.auth import (
    Token, UserCreate, UserResponse, UserLogin, 
    PasswordReset, PasswordResetConfirm, ChangePassword
)
from ....models.user import User

router = APIRouter()

@router.post("/register", response_model=UserResponse)
def register(
    user_create: UserCreate,
    db: Session = Depends(get_db)
) -> Any:
    """Register a new user"""
    repos = get_repositories(db)
    
    # Check if user already exists
    if repos.user.get_by_email(user_create.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    if user_create.phone and repos.user.get_by_phone(user_create.phone):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number already registered"
        )
    
    # Create user
    user = repos.user.create_user(user_create)
    return user

@router.post("/login", response_model=Token)
def login(
    user_credentials: UserLogin,
    db: Session = Depends(get_db)
) -> Any:
    """Login user and return access token"""
    repos = get_repositories(db)
    
    # Authenticate user
    user = repos.user.authenticate(user_credentials.email, user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token_data = create_token_data(user.id, user.email, user.role)
    access_token = create_access_token(token_data, expires_delta=access_token_expires)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": user
    }

@router.post("/login/form", response_model=Token)
def login_form(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
) -> Any:
    """Login using OAuth2 password form (for compatibility)"""
    repos = get_repositories(db)
    
    # Authenticate user
    user = repos.user.authenticate(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token_data = create_token_data(user.id, user.email, user.role)
    access_token = create_access_token(token_data, expires_delta=access_token_expires)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": user
    }

@router.get("/me", response_model=UserResponse)
def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Get current user information"""
    return current_user

@router.post("/password-reset", response_model=dict)
def request_password_reset(
    password_reset: PasswordReset,
    db: Session = Depends(get_db)
) -> Any:
    """Request password reset token"""
    repos = get_repositories(db)
    
    user = repos.user.get_by_email(password_reset.email)
    if not user:
        # Don't reveal if email exists or not
        return {"message": "If the email exists, a reset link has been sent"}
    
    # Generate reset token
    reset_token = repos.user.create_reset_token(user)
    
    # In a real application, you would send an email here
    # For demo purposes, we'll just return success
    if settings.DEMO_MODE:
        return {
            "message": "Password reset token generated",
            "reset_token": reset_token,  # Only in demo mode
            "demo_note": "In production, this would be sent via email"
        }
    
    return {"message": "If the email exists, a reset link has been sent"}

@router.post("/password-reset/confirm", response_model=dict)
def confirm_password_reset(
    password_reset_confirm: PasswordResetConfirm,
    db: Session = Depends(get_db)
) -> Any:
    """Confirm password reset with token"""
    repos = get_repositories(db)
    
    # Verify reset token
    user = repos.user.verify_reset_token(password_reset_confirm.token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    # Update password
    repos.user.update_password(user, password_reset_confirm.new_password)
    repos.user.clear_reset_token(user)
    
    return {"message": "Password updated successfully"}

@router.post("/change-password", response_model=dict)
def change_password(
    password_change: ChangePassword,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Change user password"""
    repos = get_repositories(db)
    
    # Verify current password
    user = repos.user.authenticate(current_user.email, password_change.current_password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )
    
    # Update password
    repos.user.update_password(user, password_change.new_password)
    
    return {"message": "Password changed successfully"}

@router.post("/users/{user_id}/activate", response_model=UserResponse)
def activate_user(
    user_id: int,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
) -> Any:
    """Activate a user account (admin only)"""
    repos = get_repositories(db)
    
    user = repos.user.get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user = repos.user.activate_user(user)
    return user

@router.post("/users/{user_id}/deactivate", response_model=UserResponse)
def deactivate_user(
    user_id: int,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
) -> Any:
    """Deactivate a user account (admin only)"""
    repos = get_repositories(db)
    
    user = repos.user.get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Don't allow deactivating yourself
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account"
        )
    
    user = repos.user.deactivate_user(user)
    return user