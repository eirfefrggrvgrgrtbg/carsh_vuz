import time
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Dict, List, Optional
from uuid import uuid4
from datetime import datetime
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST, REGISTRY

app = FastAPI(title="Fines Service")

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

SERVICE_NAME = "fines_service"

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


class FineCreate(BaseModel):
    user_id: str
    trip_id: str
    reason: str
    amount: float


class FineOut(BaseModel):
    id: str
    user_id: str
    trip_id: str
    reason: str
    amount: float
    created_at: datetime


fines: Dict[str, Dict] = {}


@app.post("/api/fines", response_model=FineOut)
def create_fine(payload: FineCreate):
    fine_id = str(uuid4())
    fine = {
        "id": fine_id,
        "user_id": payload.user_id,
        "trip_id": payload.trip_id,
        "reason": payload.reason,
        "amount": payload.amount,
        "created_at": datetime.utcnow(),
    }
    fines[fine_id] = fine
    return FineOut(**fine)


@app.get("/api/fines/{fine_id}", response_model=FineOut)
def get_fine(fine_id: str):
    fine = fines.get(fine_id)
    if not fine:
        raise HTTPException(status_code=404, detail="Fine not found")
    return FineOut(**fine)


@app.get("/api/fines", response_model=List[FineOut])
def list_fines(user_id: Optional[str] = None):
    result = list(fines.values())
    if user_id:
        result = [f for f in result if f["user_id"] == user_id]
    return [FineOut(**f) for f in result]
