"""
OpenAPI/Swagger documentation configuration for the public API
"""

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from typing import Dict, Any

def create_public_api_docs(app: FastAPI) -> Dict[str, Any]:
    """Create OpenAPI documentation for the public API"""
    
    openapi_schema = get_openapi(
        title="BMTC Transport Tracker Public API",
        version="1.0.0",
        description="""
        # BMTC Transport Tracker Public API
        
        This API provides real-time access to Bengaluru Metropolitan Transport Corporation (BMTC) 
        bus tracking data, routes, stops, and live location information.
        
        ## Authentication
        
        All API endpoints require authentication using an API key. Include your API key in the 
        Authorization header:
        
        ```
        Authorization: Bearer your_api_key_here
        ```
        
        ## Rate Limiting
        
        API requests are rate limited based on your API key configuration:
        - Default: 60 requests per minute, 1000 per hour, 10000 per day
        - Rate limits can be customized per API key
        
        ## WebSocket Support
        
        For real-time updates, use our WebSocket endpoints:
        - `/ws/locations` - Real-time vehicle location updates
        - `/ws/trips` - Real-time trip status updates
        
        ## Response Format
        
        All API responses follow this format:
        ```json
        {
            "success": true,
            "data": { ... },
            "message": "Optional message",
            "timestamp": "2024-01-01T00:00:00Z",
            "request_id": "optional-request-id"
        }
        ```
        
        ## Error Handling
        
        Errors are returned with appropriate HTTP status codes and error details:
        - 400: Bad Request
        - 401: Unauthorized (invalid API key)
        - 403: Forbidden (insufficient permissions)
        - 404: Not Found
        - 429: Too Many Requests (rate limit exceeded)
        - 500: Internal Server Error
        
        ## Data Models
        
        ### Bus
        - `id`: Unique bus identifier
        - `vehicle_number`: Public vehicle number (e.g., "KA-01-AB-1234")
        - `status`: Current status (active, inactive, maintenance)
        - `current_location`: Real-time location data
        - `current_trip`: Active trip information
        
        ### Route
        - `id`: Unique route identifier
        - `name`: Route name
        - `route_number`: Public route number (e.g., "335E")
        - `is_active`: Whether route is currently active
        - `stops`: List of stops on this route
        
        ### Stop
        - `id`: Unique stop identifier
        - `name`: Stop name
        - `name_kannada`: Stop name in Kannada
        - `latitude`: GPS latitude
        - `longitude`: GPS longitude
        - `is_active`: Whether stop is currently active
        - `routes`: List of routes serving this stop
        
        ### Location
        - `vehicle_id`: ID of the vehicle
        - `latitude`: GPS latitude
        - `longitude`: GPS longitude
        - `speed`: Speed in km/h
        - `bearing`: Direction in degrees
        - `recorded_at`: Timestamp of location update
        - `is_recent`: Whether location is recent (within 5 minutes)
        
        ## Getting Started
        
        1. **Get an API Key**: Contact BMTC to obtain an API key
        2. **Test the API**: Use the `/public/health` endpoint to verify your setup
        3. **Explore Data**: Start with `/public/routes` to see available routes
        4. **Real-time Updates**: Connect to WebSocket endpoints for live data
        
        ## Support
        
        For API support and questions:
        - Email: api-support@bmtc.com
        - Documentation: https://docs.bmtc.com/api
        - Status Page: https://status.bmtc.com
        """,
        routes=app.routes,
    )
    
    # Add custom OpenAPI extensions
    openapi_schema["info"]["x-logo"] = {
        "url": "https://bmtc.com/logo.png",
        "altText": "BMTC Logo"
    }
    
    # Add server information
    openapi_schema["servers"] = [
        {
            "url": "https://api.bmtc.com/v1",
            "description": "Production server"
        },
        {
            "url": "https://staging-api.bmtc.com/v1",
            "description": "Staging server"
        },
        {
            "url": "http://localhost:8000/api/v1",
            "description": "Development server"
        }
    ]
    
    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "ApiKeyAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "API Key",
            "description": "Enter your API key in the format: Bearer your_api_key_here"
        }
    }
    
    # Add global security requirement
    openapi_schema["security"] = [{"ApiKeyAuth": []}]
    
    # Add tags metadata
    openapi_schema["tags"] = [
        {
            "name": "public-api",
            "description": "Public API endpoints for accessing BMTC data",
            "externalDocs": {
                "description": "Find out more about the public API",
                "url": "https://docs.bmtc.com/api"
            }
        },
        {
            "name": "api-keys",
            "description": "API key management (admin only)",
            "externalDocs": {
                "description": "API key documentation",
                "url": "https://docs.bmtc.com/api/keys"
            }
        },
        {
            "name": "websocket-api",
            "description": "WebSocket endpoints for real-time data",
            "externalDocs": {
                "description": "WebSocket documentation",
                "url": "https://docs.bmtc.com/api/websockets"
            }
        }
    ]
    
    # Add examples for common responses
    openapi_schema["components"]["examples"] = {
        "BusResponse": {
            "summary": "Bus with location and trip data",
            "value": {
                "id": 123,
                "vehicle_number": "KA-01-AB-1234",
                "status": "active",
                "current_location": {
                    "latitude": 12.9716,
                    "longitude": 77.5946,
                    "speed": 25.5,
                    "bearing": 45.0,
                    "recorded_at": "2024-01-01T12:00:00Z",
                    "is_recent": True
                },
                "current_trip": {
                    "id": 456,
                    "route_id": 789,
                    "route_number": "335E",
                    "route_name": "Majestic to Electronic City",
                    "start_time": "2024-01-01T11:30:00Z"
                },
                "last_updated": "2024-01-01T12:00:00Z"
            }
        },
        "RouteResponse": {
            "summary": "Route with stops information",
            "value": {
                "id": 789,
                "name": "Majestic to Electronic City",
                "route_number": "335E",
                "is_active": True,
                "stops": [
                    {
                        "id": 1,
                        "name": "Majestic Bus Stand",
                        "name_kannada": "ಮಜೆಸ್ಟಿಕ್ ಬಸ್ ಸ್ಟಾಂಡ್",
                        "latitude": 12.9716,
                        "longitude": 77.5946,
                        "sequence": 1
                    },
                    {
                        "id": 2,
                        "name": "Electronic City",
                        "name_kannada": "ಎಲೆಕ್ಟ್ರಾನಿಕ್ ಸಿಟಿ",
                        "latitude": 12.8456,
                        "longitude": 77.6603,
                        "sequence": 2
                    }
                ],
                "active_trips": [
                    {
                        "id": 456,
                        "vehicle_number": "KA-01-AB-1234",
                        "start_time": "2024-01-01T11:30:00Z"
                    }
                ],
                "total_stops": 2,
                "active_trips_count": 1
            }
        },
        "LocationResponse": {
            "summary": "Real-time location update",
            "value": {
                "vehicle_id": 123,
                "latitude": 12.9716,
                "longitude": 77.5946,
                "speed": 25.5,
                "bearing": 45.0,
                "recorded_at": "2024-01-01T12:00:00Z",
                "is_recent": True
            }
        },
        "ErrorResponse": {
            "summary": "Error response example",
            "value": {
                "success": False,
                "error": {
                    "code": "RATE_LIMIT_EXCEEDED",
                    "message": "Rate limit exceeded. Try again in 60 seconds.",
                    "details": {
                        "retry_after": 60,
                        "limit": 60,
                        "window": "minute"
                    }
                },
                "timestamp": "2024-01-01T12:00:00Z",
                "request_id": "req_123456789"
            }
        }
    }
    
    # Add WebSocket documentation
    openapi_schema["paths"]["/ws/locations"] = {
        "get": {
            "tags": ["websocket-api"],
            "summary": "WebSocket endpoint for real-time location updates",
            "description": """
            Connect to this WebSocket endpoint to receive real-time vehicle location updates.
            
            **Authentication**: Include your API key as a query parameter: `?api_key=your_key`
            
            **Message Types**:
            - `subscribe`: Subscribe to specific vehicles or routes
            - `pong`: Respond to ping messages
            - `get_status`: Get connection status
            
            **Subscription Format**:
            ```json
            {
                "type": "subscribe",
                "data": {
                    "vehicle_ids": [123, 456],
                    "route_ids": [789],
                    "all_vehicles": false,
                    "all_routes": false
                }
            }
            ```
            
            **Location Update Format**:
            ```json
            {
                "type": "location_update",
                "data": {
                    "vehicle_id": 123,
                    "vehicle_number": "KA-01-AB-1234",
                    "latitude": 12.9716,
                    "longitude": 77.5946,
                    "speed": 25.5,
                    "bearing": 45.0,
                    "recorded_at": "2024-01-01T12:00:00Z",
                    "is_recent": true,
                    "trip_id": 456,
                    "route_id": 789
                },
                "timestamp": "2024-01-01T12:00:00Z"
            }
            ```
            """,
            "parameters": [
                {
                    "name": "api_key",
                    "in": "query",
                    "required": True,
                    "schema": {"type": "string"},
                    "description": "API key for authentication"
                }
            ],
            "responses": {
                "101": {
                    "description": "WebSocket connection established"
                },
                "400": {
                    "description": "Bad request or invalid API key"
                }
            }
        }
    }
    
    return openapi_schema

def add_api_documentation(app: FastAPI):
    """Add comprehensive API documentation to the FastAPI app"""
    
    # Override the default OpenAPI schema
    def custom_openapi():
        return create_public_api_docs(app)
    
    app.openapi = custom_openapi
    
    # Add additional documentation endpoints
    @app.get("/api/v1/docs/status", tags=["documentation"])
    async def api_status():
        """Get API status and documentation information"""
        return {
            "api_version": "1.0.0",
            "documentation_url": "/api/docs",
            "openapi_spec_url": "/api/openapi.json",
            "websocket_endpoints": [
                "/api/v1/ws/locations",
                "/api/v1/ws/trips"
            ],
            "rate_limits": {
                "default": {
                    "requests_per_minute": 60,
                    "requests_per_hour": 1000,
                    "requests_per_day": 10000
                }
            },
            "supported_formats": ["json"],
            "websocket_supported": True,
            "real_time_updates": True
        }
    
    @app.get("/api/v1/docs/examples", tags=["documentation"])
    async def api_examples():
        """Get API usage examples"""
        return {
            "curl_examples": {
                "get_buses": "curl -H 'Authorization: Bearer YOUR_API_KEY' https://api.bmtc.com/v1/public/buses",
                "get_routes": "curl -H 'Authorization: Bearer YOUR_API_KEY' https://api.bmtc.com/v1/public/routes",
                "get_locations": "curl -H 'Authorization: Bearer YOUR_API_KEY' 'https://api.bmtc.com/v1/public/realtime/locations?recent_only=true'"
            },
            "javascript_examples": {
                "fetch_buses": """
fetch('https://api.bmtc.com/v1/public/buses', {
    headers: {
        'Authorization': 'Bearer YOUR_API_KEY',
        'Content-Type': 'application/json'
    }
})
.then(response => response.json())
.then(data => console.log(data));
                """,
                "websocket_connection": """
const ws = new WebSocket('wss://api.bmtc.com/v1/ws/locations?api_key=YOUR_API_KEY');

ws.onopen = function() {
    // Subscribe to specific vehicles
    ws.send(JSON.stringify({
        type: 'subscribe',
        data: {
            vehicle_ids: [123, 456],
            all_vehicles: false
        }
    }));
};

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    if (data.type === 'location_update') {
        console.log('Location update:', data.data);
    }
};
                """
            },
            "python_examples": {
                "requests_library": """
import requests

headers = {
    'Authorization': 'Bearer YOUR_API_KEY',
    'Content-Type': 'application/json'
}

response = requests.get('https://api.bmtc.com/v1/public/buses', headers=headers)
data = response.json()
print(data)
                """,
                "websocket_client": """
import asyncio
import websockets
import json

async def listen_locations():
    uri = "wss://api.bmtc.com/v1/ws/locations?api_key=YOUR_API_KEY"
    async with websockets.connect(uri) as websocket:
        # Subscribe to all vehicles
        await websocket.send(json.dumps({
            "type": "subscribe",
            "data": {"all_vehicles": True}
        }))
        
        async for message in websocket:
            data = json.loads(message)
            if data["type"] == "location_update":
                print(f"Location: {data['data']}")

asyncio.run(listen_locations())
                """
            }
        }
    }

