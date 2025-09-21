"""
Migration to add admin management tables
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.core.config import settings

def create_admin_tables():
    """Create admin management tables"""
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        # Create audit_logs table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INT PRIMARY KEY AUTO_INCREMENT,
                admin_id INT NOT NULL,
                action VARCHAR(100) NOT NULL,
                resource_type VARCHAR(50) NOT NULL,
                resource_id INT NULL,
                details JSON NULL,
                ip_address VARCHAR(45) NULL,
                user_agent TEXT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (admin_id) REFERENCES users(id) ON DELETE CASCADE,
                INDEX idx_admin_id (admin_id),
                INDEX idx_timestamp (timestamp),
                INDEX idx_resource (resource_type, resource_id)
            )
        """))
        
        # Create admin_roles table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS admin_roles (
                id INT PRIMARY KEY AUTO_INCREMENT,
                name VARCHAR(50) UNIQUE NOT NULL,
                description VARCHAR(200) NULL,
                permissions JSON NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_name (name),
                INDEX idx_active (is_active)
            )
        """))
        
        # Create admin_role_assignments table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS admin_role_assignments (
                id INT PRIMARY KEY AUTO_INCREMENT,
                user_id INT NOT NULL,
                role_id INT NOT NULL,
                assigned_by INT NOT NULL,
                assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (role_id) REFERENCES admin_roles(id) ON DELETE CASCADE,
                FOREIGN KEY (assigned_by) REFERENCES users(id) ON DELETE CASCADE,
                INDEX idx_user_id (user_id),
                INDEX idx_role_id (role_id),
                INDEX idx_active (is_active),
                UNIQUE KEY unique_active_assignment (user_id, role_id, is_active)
            )
        """))
        
        # Insert default admin roles
        conn.execute(text("""
            INSERT IGNORE INTO admin_roles (name, description, permissions) VALUES
            ('super_admin', 'Super Administrator with all permissions', 
             '["user_management", "role_management", "system_config", "audit_logs", "emergency_management", "route_management", "driver_management", "analytics"]'),
            ('user_admin', 'User Management Administrator', 
             '["user_management", "audit_logs"]'),
            ('operations_admin', 'Operations Administrator', 
             '["route_management", "driver_management", "emergency_management", "analytics"]'),
            ('support_admin', 'Support Administrator', 
             '["emergency_management", "audit_logs"]')
        """))
        
        conn.commit()
        print("Admin tables created successfully!")

if __name__ == "__main__":
    create_admin_tables()