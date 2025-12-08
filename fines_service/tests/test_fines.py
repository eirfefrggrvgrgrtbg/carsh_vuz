import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# fines_service/tests/test_fines.py
from fastapi.testclient import TestClient
from app.main import app
client = TestClient(app)


def test_create_and_list_fines():
    payload = {
        "user_id": "user-fine-1",
        "trip_id": "trip-fine-1",
        "reason": "Парковка в запрещённом месте",
        "amount": 1500.0,
    }

    r = client.post("/api/fines", json=payload)
    assert r.status_code == 200
    fine = r.json()
    assert fine["user_id"] == payload["user_id"]
    fine_id = fine["id"]

    r2 = client.get(f"/api/fines/{fine_id}")
    assert r2.status_code == 200
    data2 = r2.json()
    assert data2["id"] == fine_id

    r3 = client.get("/api/fines", params={"user_id": "user-fine-1"})
    assert r3.status_code == 200
    data3 = r3.json()
    assert any(f["id"] == fine_id for f in data3)
