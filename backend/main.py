from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from datetime import datetime
import asyncio

from app.core.config import settings
from app.api.v1.api import api_router
from app.api.v1.docs import add_api_documentation
from app.core.database import engine
from app.models import Base
from app.services.location_tracking_service import location_service
from app.services.websocket_manager import websocket_manager
from app.services.eta_calculation_service import eta_service
from app.services.eta_cache_service import eta_cache_service
from app.services.notification_engine import notification_engine
from app.services.geofence_service import geofence_service
from app.services.notification_scheduler import notification_scheduler

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="BMTC Transport Tracker API",
    description="Real-time public transport tracking system for BMTC Bengaluru",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")

# Add comprehensive API documentation
add_api_documentation(app)

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    try:
        await location_service.initialize()
        await websocket_manager.initialize()
        await eta_service.initialize()
        await eta_cache_service.initialize()
        await notification_engine.initialize()
        await notification_engine.start_workers(num_workers=3)
        await notification_scheduler.initialize()
        await notification_scheduler.start_scheduler()
        print("✅ All services initialized successfully")
        print("  - Location tracking service")
        print("  - WebSocket manager")
        print("  - ETA calculation service")
        print("  - ETA cache service")
        print("  - Notification engine with 3 workers")
        print("  - Geofence service")
        print("  - Notification scheduler")
    except Exception as e:
        print(f"❌ Error initializing services: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup services on shutdown"""
    try:
        await notification_scheduler.cleanup()
        await notification_engine.cleanup()
        await websocket_manager.cleanup()
        print("✅ Services cleaned up")
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")

@app.get("/")
async def root():
    return {
        "message": "BMTC Transport Tracker API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )