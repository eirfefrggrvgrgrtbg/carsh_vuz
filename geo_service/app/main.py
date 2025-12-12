import time
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Dict, List
from uuid import uuid4
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST, REGISTRY

app = FastAPI(title="Geo Service")

# ====== Prometheus Metrics ======
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["service", "method", "endpoint", "status_code"],
)

REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["service", "method", "endpoint"],
)

ACTIVE_REQUESTS = Gauge(
    "http_active_requests",
    "Active HTTP requests",
    ["service"],
)

SERVICE_NAME = "geo_service"

@app.middleware("http")
async def metrics_middleware(request, call_next):
    start = time.time()
    method = request.method
    endpoint = request.url.path
    ACTIVE_REQUESTS.labels(service=SERVICE_NAME).inc()
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    finally:
        duration = time.time() - start
        REQUEST_DURATION.labels(service=SERVICE_NAME, method=method, endpoint=endpoint).observe(duration)
        REQUEST_COUNT.labels(service=SERVICE_NAME, method=method, endpoint=endpoint, status_code=str(status_code)).inc()
        ACTIVE_REQUESTS.labels(service=SERVICE_NAME).dec()

@app.get("/metrics")
def metrics():
    return Response(generate_latest(REGISTRY), media_type=CONTENT_TYPE_LATEST)

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
