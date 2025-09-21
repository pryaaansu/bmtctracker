from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal
from typing import Optional

class StopBase(BaseModel):
    route_id: int
    name: str
    name_kannada: Optional[str] = None
    latitude: Decimal
    longitude: Decimal
    stop_order: int

class StopCreate(StopBase):
    pass

class StopUpdate(BaseModel):
    route_id: Optional[int] = None
    name: Optional[str] = None
    name_kannada: Optional[str] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    stop_order: Optional[int] = None

class StopResponse(StopBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True