from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime, timedelta
from .base import BaseRepository
from ..models.user import User, UserRole
from ..schemas.auth import UserCreate, UserUpdate
from ..core.auth import get_password_hash, verify_password, generate_reset_token

class UserRepository(BaseRepository[User, UserCreate, UserUpdate]):
    def __init__(self, db: Session):
        super().__init__(User, db)
    
    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return self.db.query(User).filter(User.email == email).first()
    
    def get_by_phone(self, phone: str) -> Optional[User]:
        """Get user by phone number"""
        return self.db.query(User).filter(User.phone == phone).first()
    
    def create_user(self, user_create: UserCreate) -> User:
        """Create a new user with hashed password"""
        hashed_password = get_password_hash(user_create.password)
        db_user = User(
            email=user_create.email,
            phone=user_create.phone,
            hashed_password=hashed_password,
            full_name=user_create.full_name,
            role=user_create.role,
            is_active=True,
            is_verified=False
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user
    
    def authenticate(self, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password"""
        user = self.get_by_email(email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        if not user.is_active:
            return None
        return user
    
    def update_password(self, user: User, new_password: str) -> User:
        """Update user password"""
        user.hashed_password = get_password_hash(new_password)
        user.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def create_reset_token(self, user: User) -> str:
        """Create password reset token for user"""
        reset_token = generate_reset_token()
        user.reset_token = reset_token
        user.reset_token_expires = datetime.utcnow() + timedelta(hours=1)  # Token expires in 1 hour
        user.updated_at = datetime.utcnow()
        self.db.commit()
        return reset_token
    
    def verify_reset_token(self, token: str) -> Optional[User]:
        """Verify password reset token and return user if valid"""
        user = self.db.query(User).filter(
            and_(
                User.reset_token == token,
                User.reset_token_expires > datetime.utcnow()
            )
        ).first()
        return user
    
    def clear_reset_token(self, user: User) -> User:
        """Clear password reset token after use"""
        user.reset_token = None
        user.reset_token_expires = None
        user.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def get_by_role(self, role: UserRole) -> List[User]:
        """Get all users by role"""
        return self.db.query(User).filter(User.role == role).all()
    
    def activate_user(self, user: User) -> User:
        """Activate user account"""
        user.is_active = True
        user.is_verified = True
        user.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def deactivate_user(self, user: User) -> User:
        """Deactivate user account"""
        user.is_active = False
        user.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(user)
        return user