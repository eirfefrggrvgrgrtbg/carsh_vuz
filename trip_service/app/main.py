from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from . import database, models, schemas, crud

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Trip Service")


@app.post("/api/trips/start", response_model=schemas.TripOut)
def start_trip(
    payload: schemas.TripStart,
    db: Session = Depends(database.get_db),
):
    trip = crud.start_trip(db, payload)
    return trip


@app.post("/api/trips/{trip_id}/finish", response_model=schemas.TripOut)
def finish_trip(
    trip_id: str,
    payload: schemas.TripFinish,
    db: Session = Depends(database.get_db),
):
    trip = crud.finish_trip(db, trip_id, payload)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip


@app.get("/api/trips/{trip_id}", response_model=schemas.TripOut)
def get_trip(
    trip_id: str,
    db: Session = Depends(database.get_db),
):
    trip = crud.get_trip(db, trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip


@app.get("/api/trips", response_model=schemas.TripList)
def list_trips(
    user_id: Optional[str] = None,
    status: Optional[schemas.TripStatus] = None,
    offset: int = 0,
    limit: int = 20,
    db: Session = Depends(database.get_db),
):
    total, items = crud.list_trips(db, user_id, status, offset, limit)
    return schemas.TripList(total=total, items=items)
