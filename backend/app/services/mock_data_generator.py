"""
Mock BMTC Data Generator Service

Generates realistic bus routes, stops, and vehicle movements based on actual Bengaluru geography.
Supports configurable scenarios for rush hour, delays, and breakdowns.
"""

import random
import math
import json
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import asyncio

# Bengaluru landmark coordinates for realistic route generation
BENGALURU_LANDMARKS = {
    "Majestic": (12.9767, 77.5713),
    "Whitefield": (12.9698, 77.7500),
    "Electronic City": (12.8456, 77.6603),
    "Koramangala": (12.9279, 77.6271),
    "Indiranagar": (12.9719, 77.6412),
    "Jayanagar": (12.9249, 77.5832),
    "Malleshwaram": (13.0031, 77.5731),
    "Rajajinagar": (12.9991, 77.5554),
    "Banashankari": (12.9081, 77.5753),
    "HSR Layout": (12.9082, 77.6476),
    "BTM Layout": (12.9165, 77.6101),
    "Silk Board": (12.9165, 77.6224),
    "Hebbal": (13.0358, 77.5970),
    "Yeshwantpur": (13.0284, 77.5540),
    "KR Puram": (13.0055, 77.6966),
    "Marathahalli": (12.9591, 77.6974),
    "Bellandur": (12.9258, 77.6815),
    "Sarjapur": (12.9010, 77.6874),
    "Bommanahalli": (12.9067, 77.6162),
    "JP Nagar": (12.9081, 77.5753)
}

class ScenarioType(Enum):
    NORMAL = "normal"
    RUSH_HOUR = "rush_hour"
    DELAYED = "delayed"
    BREAKDOWN = "breakdown"
    MAINTENANCE = "maintenance"

@dataclass
class BusMovementConfig:
    """Configuration for bus movement simulation"""
    base_speed: float = 25.0  # km/h
    rush_hour_speed: float = 15.0  # km/h
    delay_probability: float = 0.1
    breakdown_probability: float = 0.02
    update_interval: int = 30  # seconds
    max_deviation: float = 0.001  # degrees for GPS noise

@dataclass
class RoutePoint:
    """A point along a route with timing information"""
    latitude: float
    longitude: float
    stop_id: Optional[int] = None
    estimated_time: Optional[int] = None  # seconds from route start

class MockDataGenerator:
    """Generates realistic BMTC route and bus movement data"""
    
    def __init__(self, config: BusMovementConfig = None):
        self.config = config or BusMovementConfig()
        self.routes_data = {}
        self.active_buses = {}
        self.scenario_weights = {
            ScenarioType.NORMAL: 0.7,
            ScenarioType.RUSH_HOUR: 0.15,
            ScenarioType.DELAYED: 0.1,
            ScenarioType.BREAKDOWN: 0.03,
            ScenarioType.MAINTENANCE: 0.02
        }
    
    def generate_realistic_routes(self, num_routes: int = 20) -> List[Dict]:
        """Generate realistic BMTC routes based on Bengaluru geography"""
        routes = []
        route_templates = self._get_route_templates()
        
        for i in range(num_routes):
            template = random.choice(route_templates)
            route = self._create_route_from_template(template, i + 1)
            routes.append(route)
            self.routes_data[route['route_number']] = route
        
        return routes
    
    def _get_route_templates(self) -> List[Dict]:
        """Define realistic route templates based on actual BMTC patterns"""
        return [
            {
                "name": "Majestic - Whitefield",
                "landmarks": ["Majestic", "Indiranagar", "Marathahalli", "Whitefield"],
                "type": "long_distance"
            },
            {
                "name": "Majestic - Electronic City",
                "landmarks": ["Majestic", "Jayanagar", "BTM Layout", "Silk Board", "Electronic City"],
                "type": "long_distance"
            },
            {
                "name": "Koramangala - Hebbal",
                "landmarks": ["Koramangala", "Indiranagar", "Malleshwaram", "Hebbal"],
                "type": "cross_city"
            },
            {
                "name": "Banashankari - Yeshwantpur",
                "landmarks": ["Banashankari", "Jayanagar", "Majestic", "Rajajinagar", "Yeshwantpur"],
                "type": "cross_city"
            },
            {
                "name": "HSR Layout - KR Puram",
                "landmarks": ["HSR Layout", "Koramangala", "Indiranagar", "KR Puram"],
                "type": "medium_distance"
            },
            {
                "name": "JP Nagar - Malleshwaram",
                "landmarks": ["JP Nagar", "Jayanagar", "Majestic", "Malleshwaram"],
                "type": "medium_distance"
            }
        ]
    
    def _create_route_from_template(self, template: Dict, route_num: int) -> Dict:
        """Create a detailed route from a template"""
        landmarks = template["landmarks"]
        route_points = []
        stops = []
        
        # Generate intermediate points between landmarks
        for i in range(len(landmarks) - 1):
            start_coord = BENGALURU_LANDMARKS[landmarks[i]]
            end_coord = BENGALURU_LANDMARKS[landmarks[i + 1]]
            
            # Add start landmark as stop
            if i == 0:
                stops.append({
                    "name": landmarks[i],
                    "name_kannada": self._get_kannada_name(landmarks[i]),
                    "latitude": start_coord[0],
                    "longitude": start_coord[1],
                    "stop_order": len(stops)
                })
                route_points.append(RoutePoint(start_coord[0], start_coord[1], len(stops) - 1))
            
            # Generate intermediate points
            intermediate_points = self._generate_intermediate_points(start_coord, end_coord, 3, 8)
            for point in intermediate_points:
                route_points.append(RoutePoint(point[0], point[1]))
            
            # Add end landmark as stop
            stops.append({
                "name": landmarks[i + 1],
                "name_kannada": self._get_kannada_name(landmarks[i + 1]),
                "latitude": end_coord[0],
                "longitude": end_coord[1],
                "stop_order": len(stops)
            })
            route_points.append(RoutePoint(end_coord[0], end_coord[1], len(stops) - 1))
        
        # Generate route geometry
        coordinates = [[point.longitude, point.latitude] for point in route_points]
        geojson = {
            "type": "LineString",
            "coordinates": coordinates
        }
        
        # Generate encoded polyline (simplified)
        polyline = self._encode_polyline(route_points)
        
        return {
            "name": template["name"],
            "route_number": f"{route_num:03d}",
            "geojson": json.dumps(geojson),
            "polyline": polyline,
            "is_active": True,
            "stops": stops,
            "route_points": route_points,
            "type": template["type"]
        }
    
    def _generate_intermediate_points(self, start: Tuple[float, float], 
                                    end: Tuple[float, float], 
                                    min_points: int, max_points: int) -> List[Tuple[float, float]]:
        """Generate realistic intermediate points between two coordinates"""
        num_points = random.randint(min_points, max_points)
        points = []
        
        for i in range(1, num_points + 1):
            # Linear interpolation with some random deviation
            ratio = i / (num_points + 1)
            lat = start[0] + (end[0] - start[0]) * ratio
            lng = start[1] + (end[1] - start[1]) * ratio
            
            # Add realistic road-like deviation
            deviation = random.uniform(-0.002, 0.002)
            lat += deviation
            lng += deviation
            
            points.append((lat, lng))
        
        return points
    
    def _get_kannada_name(self, english_name: str) -> str:
        """Get Kannada translation for landmark names"""
        kannada_names = {
            "Majestic": "ಮೆಜೆಸ್ಟಿಕ್",
            "Whitefield": "ವೈಟ್‌ಫೀಲ್ಡ್",
            "Electronic City": "ಎಲೆಕ್ಟ್ರಾನಿಕ್ ಸಿಟಿ",
            "Koramangala": "ಕೊರಮಂಗಲ",
            "Indiranagar": "ಇಂದಿರಾನಗರ",
            "Jayanagar": "ಜಯನಗರ",
            "Malleshwaram": "ಮಲ್ಲೇಶ್ವರಂ",
            "Rajajinagar": "ರಾಜಾಜಿನಗರ",
            "Banashankari": "ಬನಶಂಕರಿ",
            "HSR Layout": "ಎಚ್‌ಎಸ್‌ಆರ್ ಲೇಔಟ್",
            "BTM Layout": "ಬಿಟಿಎಂ ಲೇಔಟ್",
            "Silk Board": "ಸಿಲ್ಕ್ ಬೋರ್ಡ್",
            "Hebbal": "ಹೆಬ್ಬಾಳ",
            "Yeshwantpur": "ಯಶವಂತಪುರ",
            "KR Puram": "ಕೆ.ಆರ್. ಪುರಂ",
            "Marathahalli": "ಮಾರಾಠಹಳ್ಳಿ",
            "Bellandur": "ಬೆಳಲಂದೂರು",
            "Sarjapur": "ಸರ್ಜಾಪುರ",
            "Bommanahalli": "ಬೊಮ್ಮನಹಳ್ಳಿ",
            "JP Nagar": "ಜೆ.ಪಿ. ನಗರ"
        }
        return kannada_names.get(english_name, english_name)
    
    def _encode_polyline(self, points: List[RoutePoint]) -> str:
        """Simple polyline encoding (simplified version)"""
        # In a real implementation, you'd use the Google polyline algorithm
        # For now, return a simplified representation
        coords = []
        for point in points:
            coords.extend([point.latitude, point.longitude])
        return ",".join(f"{coord:.6f}" for coord in coords)
    
    def generate_bus_movements(self, route_number: str, vehicle_id: int, 
                             scenario: ScenarioType = None) -> Dict:
        """Generate realistic bus movement data for a specific route"""
        if route_number not in self.routes_data:
            raise ValueError(f"Route {route_number} not found")
        
        route = self.routes_data[route_number]
        scenario = scenario or self._get_random_scenario()
        
        # Initialize bus state if not exists
        if vehicle_id not in self.active_buses:
            self.active_buses[vehicle_id] = {
                "route_number": route_number,
                "current_point_index": 0,
                "progress": 0.0,  # Progress between current and next point
                "scenario": scenario,
                "last_update": datetime.now(),
                "speed": self._get_scenario_speed(scenario),
                "bearing": 0,
                "occupancy": random.randint(10, 80)  # Percentage
            }
        
        bus_state = self.active_buses[vehicle_id]
        current_time = datetime.now()
        time_delta = (current_time - bus_state["last_update"]).total_seconds()
        
        # Update bus position based on scenario
        new_position = self._update_bus_position(bus_state, route, time_delta, scenario)
        
        # Add GPS noise for realism
        new_position = self._add_gps_noise(new_position)
        
        # Update bus state
        bus_state["last_update"] = current_time
        
        return {
            "vehicle_id": vehicle_id,
            "latitude": new_position["latitude"],
            "longitude": new_position["longitude"],
            "speed": new_position["speed"],
            "bearing": new_position["bearing"],
            "scenario": scenario.value,
            "occupancy": bus_state["occupancy"],
            "route_number": route_number,
            "recorded_at": current_time.isoformat()
        }
    
    def _get_random_scenario(self) -> ScenarioType:
        """Get a random scenario based on weighted probabilities"""
        scenarios = list(self.scenario_weights.keys())
        weights = list(self.scenario_weights.values())
        return random.choices(scenarios, weights=weights)[0]
    
    def _get_scenario_speed(self, scenario: ScenarioType) -> float:
        """Get speed based on scenario type"""
        base_speed = self.config.base_speed
        
        if scenario == ScenarioType.RUSH_HOUR:
            return self.config.rush_hour_speed
        elif scenario == ScenarioType.DELAYED:
            return base_speed * 0.6
        elif scenario == ScenarioType.BREAKDOWN:
            return 0.0
        elif scenario == ScenarioType.MAINTENANCE:
            return 0.0
        else:
            return base_speed + random.uniform(-5, 5)  # Normal variation
    
    def _update_bus_position(self, bus_state: Dict, route: Dict, 
                           time_delta: float, scenario: ScenarioType) -> Dict:
        """Update bus position along the route"""
        route_points = route["route_points"]
        current_index = bus_state["current_point_index"]
        progress = bus_state["progress"]
        
        if current_index >= len(route_points) - 1:
            # Bus completed route, reset to beginning
            bus_state["current_point_index"] = 0
            bus_state["progress"] = 0.0
            current_index = 0
            progress = 0.0
        
        current_point = route_points[current_index]
        next_point = route_points[min(current_index + 1, len(route_points) - 1)]
        
        # Calculate distance and bearing
        distance = self._haversine_distance(
            (current_point.latitude, current_point.longitude),
            (next_point.latitude, next_point.longitude)
        )
        
        bearing = self._calculate_bearing(
            (current_point.latitude, current_point.longitude),
            (next_point.latitude, next_point.longitude)
        )
        
        # Calculate movement based on speed and time
        speed_ms = bus_state["speed"] * 1000 / 3600  # Convert km/h to m/s
        distance_moved = speed_ms * time_delta  # meters
        
        if distance > 0:
            progress_increment = distance_moved / distance
            new_progress = progress + progress_increment
            
            if new_progress >= 1.0:
                # Move to next segment
                bus_state["current_point_index"] = current_index + 1
                bus_state["progress"] = new_progress - 1.0
                new_progress = 0.0
                current_index += 1
                
                if current_index < len(route_points) - 1:
                    current_point = route_points[current_index]
                    next_point = route_points[current_index + 1]
            else:
                bus_state["progress"] = new_progress
        else:
            new_progress = progress
        
        # Interpolate position
        lat = current_point.latitude + (next_point.latitude - current_point.latitude) * new_progress
        lng = current_point.longitude + (next_point.longitude - current_point.longitude) * new_progress
        
        # Update occupancy based on stops
        if current_point.stop_id is not None and new_progress < 0.1:
            # Near a stop, simulate passenger boarding/alighting
            occupancy_change = random.randint(-15, 20)
            bus_state["occupancy"] = max(0, min(100, bus_state["occupancy"] + occupancy_change))
        
        return {
            "latitude": lat,
            "longitude": lng,
            "speed": bus_state["speed"],
            "bearing": bearing
        }
    
    def _haversine_distance(self, coord1: Tuple[float, float], 
                          coord2: Tuple[float, float]) -> float:
        """Calculate distance between two coordinates in meters"""
        R = 6371000  # Earth's radius in meters
        
        lat1, lon1 = math.radians(coord1[0]), math.radians(coord1[1])
        lat2, lon2 = math.radians(coord2[0]), math.radians(coord2[1])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c
    
    def _calculate_bearing(self, coord1: Tuple[float, float], 
                         coord2: Tuple[float, float]) -> float:
        """Calculate bearing between two coordinates in degrees"""
        lat1, lon1 = math.radians(coord1[0]), math.radians(coord1[1])
        lat2, lon2 = math.radians(coord2[0]), math.radians(coord2[1])
        
        dlon = lon2 - lon1
        
        y = math.sin(dlon) * math.cos(lat2)
        x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
        
        bearing = math.atan2(y, x)
        bearing = math.degrees(bearing)
        bearing = (bearing + 360) % 360
        
        return bearing
    
    def _add_gps_noise(self, position: Dict) -> Dict:
        """Add realistic GPS noise to position data"""
        noise_lat = random.uniform(-self.config.max_deviation, self.config.max_deviation)
        noise_lng = random.uniform(-self.config.max_deviation, self.config.max_deviation)
        
        position["latitude"] += noise_lat
        position["longitude"] += noise_lng
        
        return position
    
    def get_route_info(self, route_number: str) -> Optional[Dict]:
        """Get route information"""
        return self.routes_data.get(route_number)
    
    def get_active_buses(self) -> Dict:
        """Get all active bus states"""
        return self.active_buses.copy()
    
    def set_bus_scenario(self, vehicle_id: int, scenario: ScenarioType):
        """Manually set scenario for a specific bus (for demo purposes)"""
        if vehicle_id in self.active_buses:
            self.active_buses[vehicle_id]["scenario"] = scenario
            self.active_buses[vehicle_id]["speed"] = self._get_scenario_speed(scenario)
    
    def simulate_rush_hour(self, enable: bool = True):
        """Enable/disable rush hour simulation for all buses"""
        scenario = ScenarioType.RUSH_HOUR if enable else ScenarioType.NORMAL
        for vehicle_id in self.active_buses:
            self.set_bus_scenario(vehicle_id, scenario)
    
    def simulate_breakdown(self, vehicle_id: int):
        """Simulate breakdown for a specific bus"""
        self.set_bus_scenario(vehicle_id, ScenarioType.BREAKDOWN)
    
    def reset_bus(self, vehicle_id: int):
        """Reset bus to normal operation"""
        self.set_bus_scenario(vehicle_id, ScenarioType.NORMAL)