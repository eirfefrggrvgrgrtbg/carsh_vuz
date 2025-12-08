import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# trip_service/tests/test_trips.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_start_finish_trip_and_get():
    # старт поездки
    payload_start = {
        "booking_id": "booking-test-1",
        "user_id": "user-trip-1",
        "car_id": "car-trip-1",
    }

    r = client.post("/api/trips/start", json=payload_start)
    assert r.status_code == 200
    trip = r.json()
    assert trip["booking_id"] == payload_start["booking_id"]
    assert trip["status"] == "in_progress"

    trip_id = trip["id"]

    # завершение поездки
    payload_finish = {
        "distance_km": 10.5,
        "duration_minutes": 25,
        "parking_fines": 50.0,
        "promo_code": "TESTPROMO",
    }

    r2 = client.post(f"/api/trips/{trip_id}/finish", json=payload_finish)
    assert r2.status_code == 200
    finished = r2.json()
    assert finished["status"] == "finished"
    assert finished["final_amount"] is not None
    assert finished["final_amount"] > 0

    # получение поездки
    r3 = client.get(f"/api/trips/{trip_id}")
    assert r3.status_code == 200
    data3 = r3.json()
    assert data3["id"] == trip_id

    # список поездок пользователя
    r4 = client.get("/api/trips", params={"user_id": "user-trip-1"})
    assert r4.status_code == 200
    data4 = r4.json()
    assert data4["total"] >= 1
    assert any(item["id"] == trip_id for item in data4["items"])
