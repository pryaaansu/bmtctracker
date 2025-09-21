"""
Simple configuration for testing without external dependencies
"""
import os

class SimpleSettings:
    """Simple settings class for testing"""
    
    def __init__(self):
        # Database
        self.DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://root:password@localhost:3306/bmtc_tracker")
        self.DATABASE_ECHO = os.getenv("DATABASE_ECHO", "False").lower() == "true"
        
        # Redis
        self.REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        
        # Security
        self.SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
        self.ALGORITHM = "HS256"
        self.ACCESS_TOKEN_EXPIRE_MINUTES = 30
        
        # CORS
        self.ALLOWED_HOSTS = ["http://localhost:3000", "http://127.0.0.1:3000"]
        
        # External APIs
        self.TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
        self.TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
        self.EXOTEL_API_KEY = os.getenv("EXOTEL_API_KEY", "")
        self.EXOTEL_API_TOKEN = os.getenv("EXOTEL_API_TOKEN", "")
        
        # Demo Mode
        self.DEMO_MODE = os.getenv("DEMO_MODE", "True").lower() == "true"
        
        # Logging
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Create a simple settings instance
simple_settings = SimpleSettings()