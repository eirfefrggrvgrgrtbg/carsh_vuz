from sqlalchemy.orm import Session
from datetime import datetime

from . import models, schemas

def create_booking(db: Session, payload: schemas.BookingCreate) -> models.Booking:
    booking = models.Booking(
        user_id=payload.user_id,
        car_id=payload.car_id,
        start_at=payload.start_at,
        end_at=payload.end_at,
        zone_id=payload.zone_id,
        status=models.BookingStatus.created,
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking


def cancel_booking(db: Session, booking_id: str):
    booking = db.query(models.Booking).filter(models.Booking.id == booking_id).first()
    if not booking:
        return None
    booking.status = models.BookingStatus.cancelled
    db.commit()
    db.refresh(booking)
    return booking


def extend_booking(db: Session, booking_id: str, new_end_at: datetime):
    booking = db.query(models.Booking).filter(models.Booking.id == booking_id).first()
    if not booking:
        return None
    booking.end_at = new_end_at
    booking.status = models.BookingStatus.extended
    db.commit()
    db.refresh(booking)
    return booking


def get_booking(db: Session, booking_id: str):
    return db.query(models.Booking).filter(models.Booking.id == booking_id).first()


def list_bookings(
    db: Session,
    user_id: str | None = None,
    status: schemas.BookingStatus | None = None,
    offset: int = 0,
    limit: int = 20,
):
    query = db.query(models.Booking)
    if user_id:
        query = query.filter(models.Booking.user_id == user_id)
    if status:
        query = query.filter(models.Booking.status == status)

    total = query.count()
    items = query.offset(offset).limit(limit).all()
    return total, items
