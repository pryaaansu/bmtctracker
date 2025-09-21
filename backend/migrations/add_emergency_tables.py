"""
Add emergency tables migration
"""

from sqlalchemy import text
from ..app.core.database import engine

def upgrade():
    """Create emergency-related tables"""
    
    # Emergency incidents table
    create_emergency_incidents = """
    CREATE TABLE IF NOT EXISTS emergency_incidents (
        id INT PRIMARY KEY AUTO_INCREMENT,
        type ENUM('medical', 'safety', 'harassment', 'accident', 'other') NOT NULL,
        description TEXT,
        latitude DECIMAL(10, 8),
        longitude DECIMAL(11, 8),
        status ENUM('reported', 'acknowledged', 'in_progress', 'resolved', 'closed') DEFAULT 'reported',
        user_id INT,
        phone_number VARCHAR(15),
        user_agent TEXT,
        ip_address VARCHAR(45),
        reported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        acknowledged_at TIMESTAMP NULL,
        resolved_at TIMESTAMP NULL,
        assigned_admin_id INT,
        admin_notes TEXT,
        emergency_call_made BOOLEAN DEFAULT FALSE,
        emergency_call_time TIMESTAMP NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
        FOREIGN KEY (assigned_admin_id) REFERENCES users(id) ON DELETE SET NULL,
        INDEX idx_emergency_status (status),
        INDEX idx_emergency_type (type),
        INDEX idx_emergency_location (latitude, longitude),
        INDEX idx_emergency_reported_at (reported_at)
    );
    """
    
    # Emergency broadcasts table
    create_emergency_broadcasts = """
    CREATE TABLE IF NOT EXISTS emergency_broadcasts (
        id INT PRIMARY KEY AUTO_INCREMENT,
        title VARCHAR(200) NOT NULL,
        message TEXT NOT NULL,
        route_id INT,
        stop_id INT,
        sent_by_admin_id INT NOT NULL,
        sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        total_recipients INT DEFAULT 0,
        successful_deliveries INT DEFAULT 0,
        failed_deliveries INT DEFAULT 0,
        send_sms BOOLEAN DEFAULT TRUE,
        send_push BOOLEAN DEFAULT TRUE,
        send_whatsapp BOOLEAN DEFAULT FALSE,
        
        FOREIGN KEY (route_id) REFERENCES routes(id) ON DELETE SET NULL,
        FOREIGN KEY (stop_id) REFERENCES stops(id) ON DELETE SET NULL,
        FOREIGN KEY (sent_by_admin_id) REFERENCES users(id) ON DELETE CASCADE,
        INDEX idx_broadcast_sent_at (sent_at),
        INDEX idx_broadcast_route (route_id),
        INDEX idx_broadcast_stop (stop_id)
    );
    """
    
    # Emergency contacts table
    create_emergency_contacts = """
    CREATE TABLE IF NOT EXISTS emergency_contacts (
        id INT PRIMARY KEY AUTO_INCREMENT,
        name VARCHAR(100) NOT NULL,
        phone_number VARCHAR(15) NOT NULL,
        type VARCHAR(50) NOT NULL,
        is_active BOOLEAN DEFAULT TRUE,
        priority INT DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        
        INDEX idx_emergency_contact_type (type),
        INDEX idx_emergency_contact_priority (priority),
        INDEX idx_emergency_contact_active (is_active)
    );
    """
    
    # Insert default emergency contacts
    insert_default_contacts = """
    INSERT IGNORE INTO emergency_contacts (name, phone_number, type, priority) VALUES
    ('Police Emergency', '100', 'police', 1),
    ('Ambulance Emergency', '108', 'ambulance', 1),
    ('Fire Emergency', '101', 'fire', 1),
    ('Women Helpline', '1091', 'helpline', 2),
    ('Child Helpline', '1098', 'helpline', 2),
    ('BMTC Control Room', '+91-80-22381111', 'transport', 3);
    """
    
    with engine.connect() as connection:
        connection.execute(text(create_emergency_incidents))
        connection.execute(text(create_emergency_broadcasts))
        connection.execute(text(create_emergency_contacts))
        connection.execute(text(insert_default_contacts))
        connection.commit()
        
    print("Emergency tables created successfully")

def downgrade():
    """Drop emergency-related tables"""
    
    drop_tables = """
    DROP TABLE IF EXISTS emergency_broadcasts;
    DROP TABLE IF EXISTS emergency_incidents;
    DROP TABLE IF EXISTS emergency_contacts;
    """
    
    with engine.connect() as connection:
        connection.execute(text(drop_tables))
        connection.commit()
        
    print("Emergency tables dropped successfully")

if __name__ == "__main__":
    upgrade()