"""
Migration to add analytics tables for trip history and performance analytics
"""

from sqlalchemy import create_engine, text
from app.core.database import get_database_url
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migration():
    """Run the analytics tables migration"""
    try:
        # Create engine
        engine = create_engine(get_database_url())
        
        with engine.connect() as conn:
            # Start transaction
            trans = conn.begin()
            
            try:
                # Create trip_analytics table
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS trip_analytics (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        trip_id INT NOT NULL UNIQUE,
                        scheduled_duration_minutes FLOAT,
                        actual_duration_minutes FLOAT,
                        delay_minutes FLOAT DEFAULT 0.0,
                        on_time_percentage FLOAT,
                        total_distance_km FLOAT,
                        average_speed_kmh FLOAT,
                        fuel_efficiency_estimate FLOAT,
                        total_passengers INT DEFAULT 0,
                        peak_occupancy_percentage FLOAT DEFAULT 0.0,
                        average_occupancy_percentage FLOAT DEFAULT 0.0,
                        co2_saved_kg FLOAT DEFAULT 0.0,
                        stops_completed INT DEFAULT 0,
                        stops_skipped INT DEFAULT 0,
                        weather_conditions VARCHAR(50),
                        traffic_conditions VARCHAR(50),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        FOREIGN KEY (trip_id) REFERENCES trips(id) ON DELETE CASCADE
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """))
                logger.info("Created trip_analytics table")
                
                # Create route_performance table
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS route_performance (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        route_id INT NOT NULL,
                        date DATE NOT NULL,
                        total_trips INT DEFAULT 0,
                        completed_trips INT DEFAULT 0,
                        cancelled_trips INT DEFAULT 0,
                        average_delay_minutes FLOAT DEFAULT 0.0,
                        on_time_percentage FLOAT DEFAULT 0.0,
                        reliability_score FLOAT DEFAULT 0.0,
                        total_passengers INT DEFAULT 0,
                        average_occupancy FLOAT DEFAULT 0.0,
                        peak_hour_occupancy FLOAT DEFAULT 0.0,
                        total_co2_saved_kg FLOAT DEFAULT 0.0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (route_id) REFERENCES routes(id) ON DELETE CASCADE,
                        UNIQUE KEY unique_route_date (route_id, date)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """))
                logger.info("Created route_performance table")
                
                # Create system_metrics table
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS system_metrics (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        date DATE NOT NULL UNIQUE,
                        total_vehicles INT DEFAULT 0,
                        active_vehicles INT DEFAULT 0,
                        vehicles_in_maintenance INT DEFAULT 0,
                        total_routes INT DEFAULT 0,
                        active_routes INT DEFAULT 0,
                        total_trips_scheduled INT DEFAULT 0,
                        total_trips_completed INT DEFAULT 0,
                        system_on_time_percentage FLOAT DEFAULT 0.0,
                        average_delay_minutes FLOAT DEFAULT 0.0,
                        service_reliability FLOAT DEFAULT 0.0,
                        total_passengers INT DEFAULT 0,
                        average_system_occupancy FLOAT DEFAULT 0.0,
                        total_co2_saved_kg FLOAT DEFAULT 0.0,
                        equivalent_cars_off_road INT DEFAULT 0,
                        fuel_consumption_estimate FLOAT DEFAULT 0.0,
                        cost_per_passenger FLOAT DEFAULT 0.0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """))
                logger.info("Created system_metrics table")
                
                # Create predictive_analytics table
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS predictive_analytics (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        route_id INT,
                        prediction_type VARCHAR(50) NOT NULL,
                        prediction_date TIMESTAMP NOT NULL,
                        predicted_value FLOAT NOT NULL,
                        confidence_interval_lower FLOAT,
                        confidence_interval_upper FLOAT,
                        confidence_score FLOAT DEFAULT 0.0,
                        model_version VARCHAR(50),
                        features_used JSON,
                        actual_value FLOAT,
                        prediction_error FLOAT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (route_id) REFERENCES routes(id) ON DELETE CASCADE,
                        INDEX idx_prediction_type_date (prediction_type, prediction_date),
                        INDEX idx_route_prediction (route_id, prediction_type)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """))
                logger.info("Created predictive_analytics table")
                
                # Create indexes for better performance
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_trip_analytics_trip_id ON trip_analytics(trip_id)
                """))
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_route_performance_route_date ON route_performance(route_id, date)
                """))
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_system_metrics_date ON system_metrics(date)
                """))
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_predictive_analytics_route_type ON predictive_analytics(route_id, prediction_type)
                """))
                logger.info("Created performance indexes")
                
                # Commit transaction
                trans.commit()
                logger.info("Analytics tables migration completed successfully")
                
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

