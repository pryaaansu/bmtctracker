from fastapi import APIRouter
from .endpoints import routes, stops, buses, subscriptions, websockets, auth, users, search, notifications, emergency, driver, admin, analytics, public, api_keys, websocket_public

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(routes.router, prefix="/routes", tags=["routes"])
api_router.include_router(stops.router, prefix="/stops", tags=["stops"])
api_router.include_router(buses.router, prefix="/buses", tags=["buses"])
api_router.include_router(subscriptions.router, prefix="/subscriptions", tags=["subscriptions"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(emergency.router, prefix="/emergency", tags=["emergency"])
api_router.include_router(driver.router, prefix="/driver", tags=["driver"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(public.router, prefix="/public", tags=["public-api"])
api_router.include_router(api_keys.router, prefix="/api-keys", tags=["api-keys"])
api_router.include_router(websocket_public.router, prefix="/ws", tags=["websocket-api"])
api_router.include_router(websockets.router, tags=["websockets"])