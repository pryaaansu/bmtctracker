from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ....core.database import get_db
from ....core.dependencies import get_current_active_user, get_admin_user
from ....repositories.factory import get_repositories
from ....schemas.auth import UserResponse, UserUpdate
from ....models.user import User, UserRole

router = APIRouter()

@router.get("/profile", response_model=UserResponse)
def get_user_profile(
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Get current user profile"""
    return current_user

@router.put("/profile", response_model=UserResponse)
def update_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Update current user profile"""
    repos = get_repositories(db)
    
    # Check if email is being changed and if it's already taken
    if user_update.email and user_update.email != current_user.email:
        existing_user = repos.user.get_by_email(user_update.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    # Check if phone is being changed and if it's already taken
    if user_update.phone and user_update.phone != current_user.phone:
        existing_user = repos.user.get_by_phone(user_update.phone)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone number already registered"
            )
    
    # Update user
    updated_user = repos.user.update(current_user.id, user_update)
    return updated_user

@router.delete("/profile")
def delete_user_profile(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Delete current user profile (soft delete by deactivating)"""
    repos = get_repositories(db)
    
    # Deactivate user instead of hard delete
    repos.user.deactivate_user(current_user)
    
    return {"message": "Profile deactivated successfully"}

# Admin endpoints for user management
@router.get("/", response_model=List[UserResponse])
def list_users(
    skip: int = 0,
    limit: int = 100,
    role: UserRole = None,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
) -> Any:
    """List all users (admin only)"""
    repos = get_repositories(db)
    
    if role:
        users = repos.user.get_by_role(role)
    else:
        users = repos.user.get_multi(skip=skip, limit=limit)
    
    return users

@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get user by ID (admin only)"""
    repos = get_repositories(db)
    
    user = repos.user.get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user

@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
) -> Any:
    """Update user by ID (admin only)"""
    repos = get_repositories(db)
    
    user = repos.user.get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check for email conflicts
    if user_update.email and user_update.email != user.email:
        existing_user = repos.user.get_by_email(user_update.email)
        if existing_user and existing_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    # Check for phone conflicts
    if user_update.phone and user_update.phone != user.phone:
        existing_user = repos.user.get_by_phone(user_update.phone)
        if existing_user and existing_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone number already registered"
            )
    
    updated_user = repos.user.update(user_id, user_update)
    return updated_user

@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
) -> Any:
    """Delete user by ID (admin only)"""
    repos = get_repositories(db)
    
    user = repos.user.get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Don't allow deleting yourself
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    # Soft delete by deactivating
    repos.user.deactivate_user(user)
    
    return {"message": "User deleted successfully"}

@router.get("/role/{role}", response_model=List[UserResponse])
def get_users_by_role(
    role: UserRole,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get users by role (admin only)"""
    repos = get_repositories(db)
    
    users = repos.user.get_by_role(role)
    return users