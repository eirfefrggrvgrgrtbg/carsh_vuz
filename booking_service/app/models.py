from sqlalchemy import Column, String, DateTime, Enum
from sqlalchemy.sql import func
import uuid
import enum

from .database import Base

class BookingStatus(str, enum.Enum):
    created = "created"
    cancelled = "cancelled"
    extended = "extended"
    active = "active"
    expired = "expired"


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False)
    car_id = Column(String, nullable=False)
    start_at = Column(DateTime(timezone=True), nullable=False)
    end_at = Column(DateTime(timezone=True), nullable=False)
    zone_id = Column(String, nullable=False)
    status = Column(Enum(BookingStatus), nullable=False, default=BookingStatus.created)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
