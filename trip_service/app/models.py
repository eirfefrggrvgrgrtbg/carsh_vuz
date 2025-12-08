from sqlalchemy import Column, String, DateTime, Float, Integer, Enum
from sqlalchemy.sql import func
import uuid
import enum

from .database import Base


class TripStatus(str, enum.Enum):
    in_progress = "in_progress"
    finished = "finished"


class Trip(Base):
    __tablename__ = "trips"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    booking_id = Column(String, nullable=False)
    user_id = Column(String, nullable=False)
    car_id = Column(String, nullable=False)

    started_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    finished_at = Column(DateTime(timezone=True), nullable=True)

    distance_km = Column(Float, nullable=True)
    duration_minutes = Column(Integer, nullable=True)

    base_amount = Column(Float, nullable=True)
    discount_amount = Column(Float, nullable=True)
    final_amount = Column(Float, nullable=True)

    status = Column(Enum(TripStatus), nullable=False, default=TripStatus.in_progress)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
