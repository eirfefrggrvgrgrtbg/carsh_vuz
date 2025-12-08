import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_create_update_and_list_tickets():
    payload = {
        "user_id": "user-support-1",
        "subject": "Не открывается машина",
        "message": "Приложение пишет ошибку при открытии двери.",
    }

    r = client.post("/api/support/tickets", json=payload)
    assert r.status_code == 200
    ticket = r.json()
    assert ticket["user_id"] == payload["user_id"]
    assert ticket["status"] == "open"

    ticket_id = ticket["id"]

    # изменение статуса
    r2 = client.patch(
        f"/api/support/tickets/{ticket_id}/status",
        json={"status": "in_progress"},
    )
    assert r2.status_code == 200
    t2 = r2.json()
    assert t2["status"] == "in_progress"

    # список по user_id и статусу
    r3 = client.get(
        "/api/support/tickets",
        params={"user_id": "user-support-1", "status": "in_progress"},
    )
    assert r3.status_code == 200
    data3 = r3.json()
    assert any(t["id"] == ticket_id for t in data3)
