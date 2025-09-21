"""
Migration to add API key and usage tracking tables
"""

from sqlalchemy import create_engine, text
from app.core.database import get_database_url
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migration():
    """Run the API tables migration"""
    try:
        # Create engine
        engine = create_engine(get_database_url())
        
        with engine.connect() as conn:
            # Start transaction
            trans = conn.begin()
            
            try:
                # Create api_keys table
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS api_keys (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        key_name VARCHAR(100) NOT NULL,
                        key_hash VARCHAR(64) NOT NULL UNIQUE,
                        key_prefix VARCHAR(8) NOT NULL,
                        is_active BOOLEAN DEFAULT TRUE,
                        permissions TEXT,
                        requests_per_minute INT DEFAULT 60,
                        requests_per_hour INT DEFAULT 1000,
                        requests_per_day INT DEFAULT 10000,
                        total_requests INT DEFAULT 0,
                        last_used TIMESTAMP NULL,
                        expires_at TIMESTAMP NULL,
                        created_by INT NULL,
                        description TEXT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        INDEX idx_key_hash (key_hash),
                        INDEX idx_key_prefix (key_prefix),
                        INDEX idx_is_active (is_active),
                        INDEX idx_expires_at (expires_at)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """))
                logger.info("Created api_keys table")
                
                # Create api_usage_logs table
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS api_usage_logs (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        api_key_id INT NOT NULL,
                        endpoint VARCHAR(200) NOT NULL,
                        method VARCHAR(10) NOT NULL,
                        status_code INT NOT NULL,
                        response_time_ms INT NULL,
                        ip_address VARCHAR(45) NULL,
                        user_agent TEXT NULL,
                        request_size_bytes INT NULL,
                        response_size_bytes INT NULL,
                        error_message TEXT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        INDEX idx_api_key_id (api_key_id),
                        INDEX idx_endpoint (endpoint),
                        INDEX idx_status_code (status_code),
                        INDEX idx_created_at (created_at),
                        INDEX idx_api_key_created (api_key_id, created_at),
                        FOREIGN KEY (api_key_id) REFERENCES api_keys(id) ON DELETE CASCADE
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """))
                logger.info("Created api_usage_logs table")
                
                # Create api_rate_limits table
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS api_rate_limits (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        api_key_id INT NOT NULL,
                        window_type VARCHAR(20) NOT NULL,
                        window_start TIMESTAMP NOT NULL,
                        window_end TIMESTAMP NOT NULL,
                        request_count INT DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        INDEX idx_api_key_window (api_key_id, window_type, window_start),
                        INDEX idx_window_type (window_type),
                        INDEX idx_window_start (window_start),
                        FOREIGN KEY (api_key_id) REFERENCES api_keys(id) ON DELETE CASCADE
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """))
                logger.info("Created api_rate_limits table")
                
                # Create indexes for better performance
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_api_keys_active_expires 
                    ON api_keys(is_active, expires_at)
                """))
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_usage_logs_api_key_created 
                    ON api_usage_logs(api_key_id, created_at)
                """))
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_usage_logs_endpoint_created 
                    ON api_usage_logs(endpoint, created_at)
                """))
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_rate_limits_api_key_type 
                    ON api_rate_limits(api_key_id, window_type)
                """))
                logger.info("Created performance indexes")
                
                # Insert a default API key for testing (optional)
                # Note: In production, this should be done through the admin interface
                conn.execute(text("""
                    INSERT IGNORE INTO api_keys (
                        key_name, key_hash, key_prefix, is_active, 
                        requests_per_minute, requests_per_hour, requests_per_day,
                        description, created_by
                    ) VALUES (
                        'Default Test Key',
                        'a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3',
                        'bmtc_te',
                        TRUE,
                        100,
                        1000,
                        10000,
                        'Default API key for testing and development',
                        1
                    )
                """))
                logger.info("Inserted default test API key")
                
                # Commit transaction
                trans.commit()
                logger.info("API tables migration completed successfully")
                
            except Exception as e:
                # Rollback on error
                trans.rollback()
                logger.error(f"Error during migration: {e}")
                raise
                
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise

if __name__ == "__main__":
    run_migration()

