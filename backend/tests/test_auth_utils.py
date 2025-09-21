import pytest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.auth import (
    verify_password, 
    get_password_hash, 
    create_access_token, 
    verify_token,
    generate_reset_token,
    create_token_data
)
from app.models.user import UserRole
from datetime import timedelta
import jwt

class TestPasswordHashing:
    def test_password_hashing(self):
        """Test password hashing and verification"""
        password = "testpassword123"
        hashed = get_password_hash(password)
        
        # Hash should be different from original password
        assert hashed != password
        
        # Verification should work
        assert verify_password(password, hashed) is True
        
        # Wrong password should fail
        assert verify_password("wrongpassword", hashed) is False
    
    def test_different_hashes_for_same_password(self):
        """Test that same password generates different hashes (salt)"""
        password = "samepassword"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        # Hashes should be different due to salt
        assert hash1 != hash2
        
        # Both should verify correctly
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True

class TestJWTTokens:
    def test_create_and_verify_token(self):
        """Test JWT token creation and verification"""
        user_data = {
            "sub": "123",
            "email": "test@example.com",
            "role": "passenger",
            "user_id": 123
        }
        
        # Create token
        token = create_access_token(user_data)
        assert token is not None
        assert isinstance(token, str)
        
        # Verify token
        payload = verify_token(token)
        assert payload["sub"] == "123"
        assert payload["email"] == "test@example.com"
        assert payload["role"] == "passenger"
        assert payload["user_id"] == 123
        assert "exp" in payload
    
    def test_create_token_with_expiry(self):
        """Test token creation with custom expiry"""
        user_data = {"sub": "123", "email": "test@example.com"}
        expires_delta = timedelta(minutes=60)
        
        token = create_access_token(user_data, expires_delta)
        payload = verify_token(token)
        
        assert "exp" in payload
        # Token should be valid
        assert payload["sub"] == "123"
    
    def test_verify_invalid_token(self):
        """Test verification of invalid token"""
        with pytest.raises(Exception):  # Should raise HTTPException
            verify_token("invalid.token.here")
    
    def test_create_token_data(self):
        """Test token data creation helper"""
        token_data = create_token_data(123, "user@example.com", UserRole.DRIVER)
        
        assert token_data["sub"] == "123"
        assert token_data["email"] == "user@example.com"
        assert token_data["role"] == "driver"
        assert token_data["user_id"] == 123

class TestResetTokens:
    def test_generate_reset_token(self):
        """Test reset token generation"""
        token1 = generate_reset_token()
        token2 = generate_reset_token()
        
        # Tokens should be strings
        assert isinstance(token1, str)
        assert isinstance(token2, str)
        
        # Tokens should be different
        assert token1 != token2
        
        # Tokens should be of expected length (32 characters)
        assert len(token1) == 32
        assert len(token2) == 32
        
        # Tokens should only contain alphanumeric characters
        assert token1.isalnum()
        assert token2.isalnum()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])