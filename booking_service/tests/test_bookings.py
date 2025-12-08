import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from app.main import app
from datetime import datetime, timedelta

client = TestClient(app)


def test_create_and_get_booking():
    start_at = datetime.utcnow()
    end_at = start_at + timedelta(minutes=30)

    payload = {
        "user_id": "user-test-1",
        "car_id": "car-test-1",
        "start_at": start_at.isoformat(),
        "end_at": end_at.isoformat(),
        "zone_id": "zone-1",
    }

    r = client.post("/api/bookings", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["user_id"] == payload["user_id"]
    assert data["car_id"] == payload["car_id"]
    assert data["zone_id"] == payload["zone_id"]
    assert data["status"] == "created"

    booking_id = data["id"]

    r2 = client.get(f"/api/bookings/{booking_id}")
    assert r2.status_code == 200
    data2 = r2.json()
    assert data2["id"] == booking_id


def test_extend_and_list_bookings():
    start_at = datetime.utcnow()
    end_at = start_at + timedelta(minutes=20)

    payload = {
        "user_id": "user-test-2",
        "car_id": "car-test-2",
        "start_at": start_at.isoformat(),
        "end_at": end_at.isoformat(),
        "zone_id": "zone-2",
    }

    r = client.post("/api/bookings", json=payload)
    assert r.status_code == 200
    booking = r.json()
    booking_id = booking["id"]

    # продление
    new_end = end_at + timedelta(minutes=10)
    r2 = client.post(
        f"/api/bookings/{booking_id}/extend",
        json={"new_end_at": new_end.isoformat()},
    )
    assert r2.status_code == 200
    data2 = r2.json()
    assert data2["status"] == "extended"

    # список по user_id
    r3 = client.get("/api/bookings", params={"user_id": "user-test-2"})
    assert r3.status_code == 200
    data3 = r3.json()
    assert data3["total"] >= 1
    assert any(item["id"] == booking_id for item in data3["items"])
