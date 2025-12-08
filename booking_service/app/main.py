from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from . import database, models, schemas, crud

# создаём таблицы при старте
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Booking Service")


@app.post("/api/bookings", response_model=schemas.BookingOut)
def create_booking(
    payload: schemas.BookingCreate,
    db: Session = Depends(database.get_db),
):
    booking = crud.create_booking(db, payload)
    return booking


@app.post("/api/bookings/{booking_id}/cancel", response_model=schemas.BookingOut)
def cancel_booking(
    booking_id: str,
    db: Session = Depends(database.get_db),
):
    booking = crud.cancel_booking(db, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking


@app.post("/api/bookings/{booking_id}/extend", response_model=schemas.BookingOut)
def extend_booking(
    booking_id: str,
    payload: schemas.BookingExtend,
    db: Session = Depends(database.get_db),
):
    booking = crud.extend_booking(db, booking_id, payload.new_end_at)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking


@app.get("/api/bookings/{booking_id}", response_model=schemas.BookingOut)
def get_booking(
    booking_id: str,
    db: Session = Depends(database.get_db),
):
    booking = crud.get_booking(db, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking


@app.get("/api/bookings", response_model=schemas.BookingList)
def list_bookings(
    user_id: Optional[str] = None,
    status: Optional[schemas.BookingStatus] = None,
    offset: int = 0,
    limit: int = 20,
    db: Session = Depends(database.get_db),
):
    total, items = crud.list_bookings(db, user_id, status, offset, limit)

    # 👇 явное преобразование ORM → BookingOut
    items_out = [schemas.BookingOut.model_validate(b) for b in items]

    return schemas.BookingList(total=total, items=items_out)
