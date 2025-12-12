import time
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import Optional
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST, REGISTRY

from . import database, models, schemas, crud

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Trip Service")

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

SERVICE_NAME = "trip_service"

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
