from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional
from uuid import uuid4
from datetime import datetime

app = FastAPI(title="Support Service")


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
