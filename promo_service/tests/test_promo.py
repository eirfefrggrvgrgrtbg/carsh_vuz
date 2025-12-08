import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# promo_service/tests/test_promo.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_create_validate_and_apply_promo():
    # создаём промокод
    payload_create = {
        "code": "WELCOME10",
        "discount_percent": 10,
        "min_order_amount": 100.0,
        "max_uses": 5
    }

    r = client.post("/api/promocodes", json=payload_create)
    assert r.status_code == 200
    promo = r.json()
    assert promo["code"] == "WELCOME10"
    assert promo["discount_percent"] == 10

    # валидация
    payload_validate = {
        "promo_code": "WELCOME10",
        "user_id": "user-promo-1",
        "order_amount": 200.0
    }

    r2 = client.post("/api/promocodes/validate", json=payload_validate)
    assert r2.status_code == 200
    v = r2.json()
    assert v["valid"] is True
    assert v["discount_amount"] == 20.0

    # применение
    payload_apply = {
        "promo_code": "WELCOME10",
        "user_id": "user-promo-1",
        "order_amount": 200.0
    }

    r3 = client.post("/api/promocodes/apply", json=payload_apply)
    assert r3.status_code == 200
    a = r3.json()
    assert a["status"] == "applied"
    assert a["discount_applied"] == 20.0
    assert a["final_amount"] == 180.0
