"""
Migration to add driver portal related tables
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.core.database import engine

def upgrade():
    """Add driver portal tables"""
    
    # Create occupancy_reports table
    occupancy_reports_sql = """
    CREATE TABLE IF NOT EXISTS occupancy_reports (
        id INT PRIMARY KEY AUTO_INCREMENT,
        vehicle_id INT NOT NULL,
        driver_id INT NOT NULL,
        occupancy_level ENUM('empty', 'low', 'medium', 'high', 'full') NOT NULL,
        passenger_count INT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (vehicle_id) REFERENCES vehicles(id) ON DELETE CASCADE,
        FOREIGN KEY (driver_id) REFERENCES drivers(id) ON DELETE CASCADE,
        INDEX idx_vehicle_timestamp (vehicle_id, timestamp),
        INDEX idx_driver_timestamp (driver_id, timestamp)
    );
    """
    
    # Create issues table
    issues_sql = """
    CREATE TABLE IF NOT EXISTS issues (
        id INT PRIMARY KEY AUTO_INCREMENT,
        category ENUM('mechanical', 'traffic', 'passenger', 'route', 'emergency', 'other') NOT NULL,
        priority ENUM('low', 'medium', 'high', 'critical') NOT NULL,
        title VARCHAR(200) NOT NULL,
        description TEXT NOT NULL,
        location_lat DECIMAL(10, 8) NULL,
        location_lng DECIMAL(11, 8) NULL,
        vehicle_id INT NULL,
        route_id INT NULL,
        reported_by INT NOT NULL,
        status ENUM('open', 'in_progress', 'resolved', 'closed') DEFAULT 'open',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        resolved_at TIMESTAMP NULL,
        resolved_by INT NULL,
        FOREIGN KEY (vehicle_id) REFERENCES vehicles(id) ON DELETE SET NULL,
        FOREIGN KEY (route_id) REFERENCES routes(id) ON DELETE SET NULL,
        FOREIGN KEY (reported_by) REFERENCES drivers(id) ON DELETE CASCADE,
        FOREIGN KEY (resolved_by) REFERENCES drivers(id) ON DELETE SET NULL,
        INDEX idx_reported_by (reported_by),
        INDEX idx_status_priority (status, priority),
        INDEX idx_created_at (created_at)
    );
    """
    
    # Create shift_schedules table
    shift_schedules_sql = """
    CREATE TABLE IF NOT EXISTS shift_schedules (
        id INT PRIMARY KEY AUTO_INCREMENT,
        driver_id INT NOT NULL,
        vehicle_id INT NOT NULL,
        route_id INT NOT NULL,
        start_time TIMESTAMP NOT NULL,
        end_time TIMESTAMP NOT NULL,
        status ENUM('scheduled', 'active', 'completed', 'cancelled') DEFAULT 'scheduled',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (driver_id) REFERENCES drivers(id) ON DELETE CASCADE,
        FOREIGN KEY (vehicle_id) REFERENCES vehicles(id) ON DELETE CASCADE,
        FOREIGN KEY (route_id) REFERENCES routes(id) ON DELETE CASCADE,
        INDEX idx_driver_start_time (driver_id, start_time),
        INDEX idx_vehicle_start_time (vehicle_id, start_time)
    );
    """
    
    with engine.connect() as connection:
        connection.execute(text(occupancy_reports_sql))
        connection.execute(text(issues_sql))
        connection.execute(text(shift_schedules_sql))
        connection.commit()
        print("✅ Driver portal tables created successfully")

def downgrade():
    """Remove driver portal tables"""
    
    drop_tables_sql = """
    DROP TABLE IF EXISTS shift_schedules;
    DROP TABLE IF EXISTS issues;
    DROP TABLE IF EXISTS occupancy_reports;
    """
    
    with engine.connect() as connection:
        connection.execute(text(drop_tables_sql))
        connection.commit()
        print("✅ Driver portal tables removed successfully")

if __name__ == "__main__":
    upgrade()