# app/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict
from uuid import uuid4

app = FastAPI(title="User Service")

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
