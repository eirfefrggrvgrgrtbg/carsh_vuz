from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List
from uuid import uuid4

app = FastAPI(title="Geo Service")

# ====== Модели ======

class ZoneCreate(BaseModel):
    name: str
    city: str
    # для простоты – просто текстовое описание/массив координатов строкой
    polygon: str


class ZoneOut(BaseModel):
    id: str
    name: str
    city: str
    polygon: str


zones: Dict[str, Dict] = {}


@app.post("/api/zones", response_model=ZoneOut)
def create_zone(payload: ZoneCreate):
    zone_id = str(uuid4())
    zone = {
        "id": zone_id,
        "name": payload.name,
        "city": payload.city,
        "polygon": payload.polygon,
    }
    zones[zone_id] = zone
    return ZoneOut(**zone)


@app.get("/api/zones", response_model=List[ZoneOut])
def list_zones():
    return [ZoneOut(**z) for z in zones.values()]


@app.get("/api/zones/{zone_id}", response_model=ZoneOut)
def get_zone(zone_id: str):
    zone = zones.get(zone_id)
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    return ZoneOut(**zone)
