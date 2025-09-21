"""
Migration script to add users table
"""
from sqlalchemy import create_engine, text
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_users_table():
    """Add users table to the database"""
    try:
        engine = create_engine(settings.DATABASE_URL)
        
        # Create users table
        create_users_table_sql = """
        CREATE TABLE IF NOT EXISTS users (
            id INT PRIMARY KEY AUTO_INCREMENT,
            email VARCHAR(255) UNIQUE NOT NULL,
            phone VARCHAR(15) UNIQUE NULL,
            hashed_password VARCHAR(255) NOT NULL,
            full_name VARCHAR(100) NULL,
            role ENUM('passenger', 'driver', 'admin') DEFAULT 'passenger' NOT NULL,
            is_active BOOLEAN DEFAULT TRUE NOT NULL,
            is_verified BOOLEAN DEFAULT FALSE NOT NULL,
            reset_token VARCHAR(255) NULL,
            reset_token_expires DATETIME NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP NOT NULL,
            INDEX idx_email (email),
            INDEX idx_phone (phone),
            INDEX idx_role (role)
        );
        """
        
        with engine.connect() as conn:
            conn.execute(text(create_users_table_sql))
            conn.commit()
            logger.info("Users table created successfully!")
            
            # Insert default admin user
            insert_admin_sql = """
            INSERT IGNORE INTO users (email, hashed_password, full_name, role, is_active, is_verified)
            VALUES ('admin@bmtc.gov.in', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj3L3jzjIxHu', 'BMTC Administrator', 'admin', TRUE, TRUE);
            """
            # Password is 'admin123'
            
            conn.execute(text(insert_admin_sql))
            conn.commit()
            logger.info("Default admin user created!")
            
            # Insert sample driver users
            insert_drivers_sql = """
            INSERT IGNORE INTO users (email, phone, hashed_password, full_name, role, is_active, is_verified) VALUES
            ('driver1@bmtc.gov.in', '+919876543210', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj3L3jzjIxHu', 'Rajesh Kumar', 'driver', TRUE, TRUE),
            ('driver2@bmtc.gov.in', '+919876543211', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj3L3jzjIxHu', 'Suresh Babu', 'driver', TRUE, TRUE);
            """
            # Password is 'driver123' for both
            
            conn.execute(text(insert_drivers_sql))
            conn.commit()
            logger.info("Sample driver users created!")
            
            # Insert sample passenger user
            insert_passenger_sql = """
            INSERT IGNORE INTO users (email, phone, hashed_password, full_name, role, is_active, is_verified)
            VALUES ('passenger@example.com', '+919876543212', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj3L3jzjIxHu', 'Test Passenger', 'passenger', TRUE, TRUE);
            """
            # Password is 'passenger123'
            
            conn.execute(text(insert_passenger_sql))
            conn.commit()
            logger.info("Sample passenger user created!")
            
        return True
    except Exception as e:
        logger.error(f"Error creating users table: {e}")
        return False

if __name__ == "__main__":
    add_users_table()