from sqlalchemy.orm import Session
from datetime import datetime

from . import models, schemas


def start_trip(db: Session, payload: schemas.TripStart) -> models.Trip:
    trip = models.Trip(
        booking_id=payload.booking_id,
        user_id=payload.user_id,
        car_id=payload.car_id,
        status=models.TripStatus.in_progress,
    )
    db.add(trip)
    db.commit()
    db.refresh(trip)
    return trip


def finish_trip(
    db: Session,
    trip_id: str,
    payload: schemas.TripFinish,
) -> models.Trip | None:
    trip = db.query(models.Trip).filter(models.Trip.id == trip_id).first()
    if not trip:
        return None

    trip.finished_at = datetime.utcnow()
    trip.distance_km = payload.distance_km
    trip.duration_minutes = payload.duration_minutes

    # простая формула тарифа: 10 руб/км + 5 руб/мин
    base = payload.distance_km * 10 + payload.duration_minutes * 5 + payload.parking_fines
    discount = 0.0
    if payload.promo_code:
        discount = base * 0.1  # 10%

    trip.base_amount = base
    trip.discount_amount = discount
    trip.final_amount = base - discount
    trip.status = models.TripStatus.finished

    db.commit()
    db.refresh(trip)
    return trip


def get_trip(db: Session, trip_id: str) -> models.Trip | None:
    return db.query(models.Trip).filter(models.Trip.id == trip_id).first()


def list_trips(
    db: Session,
    user_id: str | None = None,
    status: schemas.TripStatus | None = None,
    offset: int = 0,
    limit: int = 20,
):
    query = db.query(models.Trip)
    if user_id:
        query = query.filter(models.Trip.user_id == user_id)
    if status:
        query = query.filter(models.Trip.status == status)

    total = query.count()
    items = query.offset(offset).limit(limit).all()
    return total, items
