import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# car_service/tests/test_cars.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_create_get_and_update_car():
    payload = {
        "model": "Kia Rio",
        "plate_number": "A123BC777",
        "color": "white",
        "location": "Москва, центр",
        "status": "available",
    }

    r = client.post("/api/cars", json=payload)
    assert r.status_code == 200
    car = r.json()
    assert car["model"] == payload["model"]
    assert car["plate_number"] == payload["plate_number"]

    car_id = car["id"]

    # получить по id
    r2 = client.get(f"/api/cars/{car_id}")
    assert r2.status_code == 200
    data2 = r2.json()
    assert data2["id"] == car_id

    # изменить статус
    r3 = client.patch(f"/api/cars/{car_id}/status", json={"status": "in_trip"})
    assert r3.status_code == 200
    data3 = r3.json()
    assert data3["status"] == "in_trip"

    # список
    r4 = client.get("/api/cars", params={"status": "in_trip"})
    assert r4.status_code == 200
    data4 = r4.json()
    assert any(c["id"] == car_id for c in data4)
