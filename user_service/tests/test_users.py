import sys
import os
import importlib.util

# Добавляем путь к user_service
user_service_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Загружаем модуль напрямую из файла, минуя кэш sys.modules
spec = importlib.util.spec_from_file_location(
    "user_app_main", 
    os.path.join(user_service_path, "app", "main.py")
)
user_app_main = importlib.util.module_from_spec(spec)
spec.loader.exec_module(user_app_main)

from fastapi.testclient import TestClient

app = user_app_main.app
client = TestClient(app)


def test_register_and_get_user():
    payload = {
        "phone": "+79990000001",
        "email": "test1@example.com",
        "full_name": "Test User 1",
        "driver_license": "7700123456",
        "password": "secret123",
    }

    # регистрация
    r = client.post("/api/users/register", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["phone"] == payload["phone"]
    assert data["email"] == payload["email"]
    assert data["full_name"] == payload["full_name"]
    assert data["status"] == "pending_verification"

    user_id = data["id"]

    # получение профиля
    r2 = client.get(f"/api/users/{user_id}")
    assert r2.status_code == 200
    data2 = r2.json()
    assert data2["id"] == user_id
    assert data2["driver_license"] == payload["driver_license"]


def test_login_wrong_credentials():
    # логин с несуществующим логином
    r = client.post(
        "/api/users/login",
        json={"phone_or_email": "no_such_user", "password": "123"},
    )
    assert r.status_code == 401
