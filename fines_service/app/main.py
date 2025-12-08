from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional
from uuid import uuid4
from datetime import datetime

app = FastAPI(title="Fines Service")


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
