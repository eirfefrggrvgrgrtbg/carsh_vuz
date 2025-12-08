import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# geo_service/tests/test_geo.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_create_and_list_zones():
    payload = {
        "name": "Центральная зона",
        "city": "Москва",
        "polygon": "[(55.75,37.6),(55.76,37.7)]"
    }

    r = client.post("/api/zones", json=payload)
    assert r.status_code == 200
    zone = r.json()
    assert zone["name"] == payload["name"]
    zone_id = zone["id"]

    r2 = client.get(f"/api/zones/{zone_id}")
    assert r2.status_code == 200
    data2 = r2.json()
    assert data2["id"] == zone_id

    r3 = client.get("/api/zones")
    assert r3.status_code == 200
    data3 = r3.json()
    assert any(z["id"] == zone_id for z in data3)
