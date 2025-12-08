from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from enum import Enum

class BookingStatus(str, Enum):
    created = "created"
    cancelled = "cancelled"
    extended = "extended"
    active = "active"
    expired = "expired"


class BookingCreate(BaseModel):
    user_id: str
    car_id: str
    start_at: datetime
    end_at: datetime
    zone_id: str


class BookingExtend(BaseModel):
    new_end_at: datetime


class BookingOut(BaseModel):
    id: str
    user_id: str
    car_id: str
    start_at: datetime
    end_at: datetime
    zone_id: str
    status: BookingStatus

    model_config = {"from_attributes": True}


class BookingList(BaseModel):
    total: int
    items: list[BookingOut]
