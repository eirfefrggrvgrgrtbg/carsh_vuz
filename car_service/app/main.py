from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Optional, List
from uuid import uuid4

app = FastAPI(title="Car Service")

# ====== Модели ======

class CarStatus(str):
    AVAILABLE = "available"
    RESERVED = "reserved"
    IN_TRIP = "in_trip"
    UNAVAILABLE = "unavailable"


class CarCreate(BaseModel):
    model: str
    plate_number: str
    color: str
    location: str
    status: str = CarStatus.AVAILABLE


class CarUpdateStatus(BaseModel):
    status: str


class CarOut(BaseModel):
    id: str
    model: str
    plate_number: str
    color: str
    location: str
    status: str


# ====== "База" в памяти ======

cars: Dict[str, Dict] = {}


# ====== Эндпоинты ======

@app.post("/api/cars", response_model=CarOut)
def create_car(payload: CarCreate):
    car_id = str(uuid4())
    # проверить, чтобы не дублировались номера
    for c in cars.values():
        if c["plate_number"] == payload.plate_number:
            raise HTTPException(status_code=400, detail="Car with this plate already exists")

    car = {
        "id": car_id,
        "model": payload.model,
        "plate_number": payload.plate_number,
        "color": payload.color,
        "location": payload.location,
        "status": payload.status,
    }
    cars[car_id] = car
    return CarOut(**car)


@app.get("/api/cars", response_model=List[CarOut])
def list_cars(status: Optional[str] = None):
    result = list(cars.values())
    if status:
        result = [c for c in result if c["status"] == status]
    return [CarOut(**c) for c in result]


@app.get("/api/cars/{car_id}", response_model=CarOut)
def get_car(car_id: str):
    car = cars.get(car_id)
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")
    return CarOut(**car)


@app.patch("/api/cars/{car_id}/status", response_model=CarOut)
def update_car_status(car_id: str, payload: CarUpdateStatus):
    car = cars.get(car_id)
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")

    car["status"] = payload.status
    return CarOut(**car)
