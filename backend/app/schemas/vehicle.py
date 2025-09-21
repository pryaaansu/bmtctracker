from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from ..models.vehicle import VehicleStatus

class VehicleBase(BaseModel):
    vehicle_number: str
    capacity: int
    status: VehicleStatus = VehicleStatus.ACTIVE

class VehicleCreate(VehicleBase):
    pass

class VehicleUpdate(BaseModel):
    vehicle_number: Optional[str] = None
    capacity: Optional[int] = None
    status: Optional[VehicleStatus] = None

class VehicleResponse(VehicleBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True