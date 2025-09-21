from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class RouteBase(BaseModel):
    name: str
    route_number: str
    geojson: str
    polyline: str
    is_active: bool = True

class RouteCreate(RouteBase):
    pass

class RouteUpdate(BaseModel):
    name: Optional[str] = None
    route_number: Optional[str] = None
    geojson: Optional[str] = None
    polyline: Optional[str] = None
    is_active: Optional[bool] = None

class RouteResponse(RouteBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True