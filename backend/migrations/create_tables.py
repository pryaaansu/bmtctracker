"""
Database migration script to create all tables
"""
from sqlalchemy import create_engine
from app.core.config import settings
from app.models import Base
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_tables():
    """Create all database tables"""
    try:
        engine = create_engine(settings.DATABASE_URL)
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully!")
        return True
    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        return False

def drop_tables():
    """Drop all database tables (use with caution!)"""
    try:
        engine = create_engine(settings.DATABASE_URL)
        logger.info("Dropping database tables...")
        Base.metadata.drop_all(bind=engine)
        logger.info("Database tables dropped successfully!")
        return True
    except Exception as e:
        logger.error(f"Error dropping tables: {e}")
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "drop":
        drop_tables()
    else:
        create_tables()