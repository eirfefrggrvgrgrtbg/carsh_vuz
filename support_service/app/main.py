import time
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Dict, List, Optional
from uuid import uuid4
from datetime import datetime
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST, REGISTRY

app = FastAPI(title="Support Service")

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

SERVICE_NAME = "support_service"

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


class TicketStatus(str):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    CLOSED = "closed"


class TicketCreate(BaseModel):
    user_id: str
    subject: str
    message: str


class TicketUpdateStatus(BaseModel):
    status: str


class TicketOut(BaseModel):
    id: str
    user_id: str
    subject: str
    message: str
    status: str
    created_at: datetime


tickets: Dict[str, Dict] = {}


@app.post("/api/support/tickets", response_model=TicketOut)
def create_ticket(payload: TicketCreate):
    ticket_id = str(uuid4())
    ticket = {
        "id": ticket_id,
        "user_id": payload.user_id,
        "subject": payload.subject,
        "message": payload.message,
        "status": TicketStatus.OPEN,
        "created_at": datetime.utcnow(),
    }
    tickets[ticket_id] = ticket
    return TicketOut(**ticket)


@app.get("/api/support/tickets/{ticket_id}", response_model=TicketOut)
def get_ticket(ticket_id: str):
    ticket = tickets.get(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return TicketOut(**ticket)


@app.get("/api/support/tickets", response_model=List[TicketOut])
def list_tickets(user_id: Optional[str] = None, status: Optional[str] = None):
    result = list(tickets.values())
    if user_id:
        result = [t for t in result if t["user_id"] == user_id]
    if status:
        result = [t for t in result if t["status"] == status]
    return [TicketOut(**t) for t in result]


@app.patch("/api/support/tickets/{ticket_id}/status", response_model=TicketOut)
def update_ticket_status(ticket_id: str, payload: TicketUpdateStatus):
    ticket = tickets.get(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    ticket["status"] = payload.status
    return TicketOut(**ticket)
