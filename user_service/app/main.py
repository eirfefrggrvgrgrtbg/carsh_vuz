# app/main.py
import os
import time
import uuid
import socket
import logging
from fastapi import FastAPI, Request
from starlette.responses import Response
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict
from uuid import uuid4
SERVICE_NAME = os.getenv("SERVICE_NAME", "unknown-service")
INSTANCE_ID = os.getenv("INSTANCE_ID", socket.gethostname())

# --- Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s service=%(service)s instance=%(instance)s request_id=%(request_id)s %(message)s",
)
logger = logging.getLogger("app")

class ContextFilter(logging.Filter):
    def __init__(self):
        super().__init__()
        self.request_id = "-"

    def set_request_id(self, rid: str):
        self.request_id = rid

    def filter(self, record):
        record.service = SERVICE_NAME
        record.instance = INSTANCE_ID
        record.request_id = getattr(self, "request_id", "-")
        return True

ctx_filter = ContextFilter()
logger.addFilter(ctx_filter)

# --- Prometheus metrics ---
HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["service", "method", "path", "status"],
)
HTTP_REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["service", "method", "path"],
)
HTTP_INPROGRESS = Gauge(
    "http_inprogress_requests",
    "In-progress HTTP requests",
    ["service"],
)

app = FastAPI(title="User Service")

@app.middleware("http")
async def observability_middleware(request: Request, call_next):
    rid = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    ctx_filter.set_request_id(rid)

    start = time.time()
    method = request.method
    path = request.url.path

    HTTP_INPROGRESS.labels(service=SERVICE_NAME).inc()
    status_code = 500

    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    finally:
        duration = time.time() - start
        HTTP_INPROGRESS.labels(service=SERVICE_NAME).dec()

        HTTP_REQUESTS_TOTAL.labels(
            service=SERVICE_NAME, method=method, path=path, status=str(status_code)
        ).inc()
        HTTP_REQUEST_DURATION.labels(
            service=SERVICE_NAME, method=method, path=path
        ).observe(duration)

        logger.info(f"{method} {path} -> {status_code} duration={duration:.4f}s")

# ====== Pydantic-схемы ======

class UserRegisterRequest(BaseModel):
    phone: str
    email: EmailStr
    full_name: str
    driver_license: str
    password: str

class UserLoginRequest(BaseModel):
    phone_or_email: str
    password: str

class UserResponse(BaseModel):
    id: str
    phone: str
    email: EmailStr
    full_name: str
    status: str
    driver_license: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

# ====== "База" в памяти ======

users_by_id: Dict[str, dict] = {}
users_by_login: Dict[str, str] = {}  # phone/email -> user_id


# ====== Эндпоинты ======
@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.post("/api/users/register", response_model=UserResponse)
def register_user(payload: UserRegisterRequest):
    # Проверяем, что логин не занят
    if payload.phone in users_by_login or payload.email in users_by_login:
        raise HTTPException(status_code=400, detail="User already exists")

    user_id = str(uuid4())
    user_data = {
        "id": user_id,
        "phone": payload.phone,
        "email": payload.email,
        "full_name": payload.full_name,
        "driver_license": payload.driver_license,
        "password": payload.password,  # в реальности нужно хэшировать
        "status": "pending_verification",
    }

    users_by_id[user_id] = user_data
    users_by_login[payload.phone] = user_id
    users_by_login[payload.email] = user_id

    return UserResponse(**user_data)


@app.post("/api/users/login", response_model=TokenResponse)
def login_user(payload: UserLoginRequest):
    user_id = users_by_login.get(payload.phone_or_email)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user = users_by_id[user_id]
    if user["password"] != payload.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # "Фейковый" токен
    token = f"fake-token-for-{user_id}"

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse(**user),
    )


@app.get("/api/users/{user_id}", response_model=UserResponse)
def get_user(user_id: str):
    user = users_by_id.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse(**user)
