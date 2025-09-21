-- BMTC Transport Tracker Database Initialization
-- This script creates the initial database schema and seed data

USE bmtc_tracker;

-- Insert sample routes
INSERT INTO routes (name, route_number, geojson, polyline, is_active) VALUES
('Majestic - Electronic City', '335E', '{"type":"LineString","coordinates":[[77.5946,12.9716],[77.6648,12.8456]]}', 'encoded_polyline_data_1', TRUE),
('Majestic - Whitefield', '500D', '{"type":"LineString","coordinates":[[77.5946,12.9716],[77.7499,12.9698]]}', 'encoded_polyline_data_2', TRUE),
('Banashankari - Hebbal', '201', '{"type":"LineString","coordinates":[[77.5568,12.9249],[77.5946,13.0358]]}', 'encoded_polyline_data_3', TRUE);

-- Insert sample vehicles
INSERT INTO vehicles (vehicle_number, capacity, status) VALUES
('KA01-1234', 40, 'active'),
('KA01-5678', 40, 'active'),
('KA01-9012', 35, 'active'),
('KA01-3456', 40, 'maintenance'),
('KA01-7890', 35, 'active');

-- Insert sample drivers
INSERT INTO drivers (name, phone, license_number, assigned_vehicle_id, status) VALUES
('Rajesh Kumar', '+919876543210', 'KA0120230001', 1, 'active'),
('Suresh Babu', '+919876543211', 'KA0120230002', 2, 'active'),
('Mahesh Gowda', '+919876543212', 'KA0120230003', 3, 'active'),
('Ramesh Reddy', '+919876543213', 4, 'inactive'),
('Ganesh Rao', '+919876543214', 'KA0120230005', 5, 'active');

-- Insert sample stops for Route 1 (Majestic - Electronic City)
INSERT INTO stops (route_id, name, name_kannada, latitude, longitude, stop_order) VALUES
(1, 'Majestic Bus Station', 'ಮೆಜೆಸ್ಟಿಕ್ ಬಸ್ ನಿಲ್ದಾಣ', 12.9716, 77.5946, 1),
(1, 'Town Hall', 'ಟೌನ್ ಹಾಲ್', 12.9667, 77.5964, 2),
(1, 'Corporation Circle', 'ಕಾರ್ಪೊರೇಷನ್ ಸರ್ಕಲ್', 12.9611, 77.6017, 3),
(1, 'Lalbagh West Gate', 'ಲಾಲ್ಬಾಗ್ ಪಶ್ಚಿಮ ಗೇಟ್', 12.9507, 77.5848, 4),
(1, 'Jayanagar 4th Block', 'ಜಯನಗರ 4ನೇ ಬ್ಲಾಕ್', 12.9279, 77.5937, 5),
(1, 'BTM Layout', 'ಬಿಟಿಎಂ ಲೇಔಟ್', 12.9165, 77.6101, 6),
(1, 'Silk Board', 'ಸಿಲ್ಕ್ ಬೋರ್ಡ್', 12.9077, 77.6226, 7),
(1, 'Electronic City', 'ಎಲೆಕ್ಟ್ರಾನಿಕ್ ಸಿಟಿ', 12.8456, 77.6648, 8);

-- Insert sample stops for Route 2 (Majestic - Whitefield)
INSERT INTO stops (route_id, name, name_kannada, latitude, longitude, stop_order) VALUES
(2, 'Majestic Bus Station', 'ಮೆಜೆಸ್ಟಿಕ್ ಬಸ್ ನಿಲ್ದಾಣ', 12.9716, 77.5946, 1),
(2, 'Shivaji Nagar', 'ಶಿವಾಜಿ ನಗರ', 12.9895, 77.6006, 2),
(2, 'Cantonment Railway Station', 'ಕ್ಯಾಂಟೋನ್ಮೆಂಟ್ ರೈಲ್ವೇ ನಿಲ್ದಾಣ', 12.9845, 77.6108, 3),
(2, 'MG Road', 'ಎಂಜಿ ರೋಡ್', 12.9759, 77.6063, 4),
(2, 'Indiranagar', 'ಇಂದಿರಾನಗರ', 12.9719, 77.6412, 5),
(2, 'Marathahalli', 'ಮರಾಠಹಳ್ಳಿ', 12.9591, 77.6974, 6),
(2, 'Brookefield', 'ಬ್ರೂಕ್‌ಫೀಲ್ಡ್', 12.9698, 77.7138, 7),
(2, 'Whitefield', 'ವೈಟ್‌ಫೀಲ್ಡ್', 12.9698, 77.7499, 8);

-- Insert sample trips
INSERT INTO trips (vehicle_id, route_id, driver_id, start_time, status) VALUES
(1, 1, 1, NOW() - INTERVAL 30 MINUTE, 'active'),
(2, 2, 2, NOW() - INTERVAL 45 MINUTE, 'active'),
(3, 1, 3, NOW() - INTERVAL 15 MINUTE, 'active');

-- Insert sample vehicle locations
INSERT INTO vehicle_locations (vehicle_id, latitude, longitude, speed, bearing, recorded_at) VALUES
(1, 12.9279, 77.5937, 25.5, 180, NOW() - INTERVAL 1 MINUTE),
(2, 12.9591, 77.6974, 30.2, 90, NOW() - INTERVAL 2 MINUTE),
(3, 12.9507, 77.5848, 15.8, 270, NOW() - INTERVAL 30 SECOND);

-- Insert sample subscriptions
INSERT INTO subscriptions (phone, stop_id, channel, eta_threshold, is_active) VALUES
('+919876543210', 5, 'sms', 5, TRUE),
('+919876543211', 6, 'whatsapp', 3, TRUE),
('+919876543212', 7, 'voice', 10, TRUE);

-- Create indexes for better performance
CREATE INDEX idx_vehicle_locations_vehicle_time ON vehicle_locations(vehicle_id, recorded_at DESC);
CREATE INDEX idx_stops_location ON stops(latitude, longitude);
CREATE INDEX idx_subscriptions_active ON subscriptions(is_active, stop_id);

-- Insert admin user (for future authentication)
-- Password: admin123 (hashed)
-- INSERT INTO users (email, hashed_password, role, is_active) VALUES
-- ('admin@bmtc.gov.in', '$2b$12$hash_here', 'admin', TRUE);