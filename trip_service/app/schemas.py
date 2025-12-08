from pydantic import BaseModel
from datetime import datetime
from enum import Enum
from typing import Optional, List


class TripStatus(str, Enum):
    in_progress = "in_progress"
    finished = "finished"


class TripStart(BaseModel):
    booking_id: str
    user_id: str
    car_id: str


class TripFinish(BaseModel):
    distance_km: float
    duration_minutes: int
    parking_fines: float = 0.0
    promo_code: Optional[str] = None


class TripOut(BaseModel):
    id: str
    booking_id: str
    user_id: str
    car_id: str
    started_at: datetime
    finished_at: Optional[datetime]
    distance_km: Optional[float]
    duration_minutes: Optional[int]
    base_amount: Optional[float]
    discount_amount: Optional[float]
    final_amount: Optional[float]
    status: TripStatus

    model_config = {"from_attributes": True}


class TripList(BaseModel):
    total: int
    items: list[TripOut]
