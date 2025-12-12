import time
from datetime import datetime, timedelta
from typing import Dict, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST, REGISTRY


app = FastAPI(title="Promo Service")

# ====== Prometheus Metrics ======
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["service", "method", "endpoint", "status_code"],
)

REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["service", "method", "endpoint"],
)

ACTIVE_REQUESTS = Gauge(
    "http_active_requests",
    "Active HTTP requests",
    ["service"],
)

SERVICE_NAME = "promo_service"

@app.middleware("http")
async def metrics_middleware(request, call_next):
    start = time.time()
    method = request.method
    endpoint = request.url.path
    ACTIVE_REQUESTS.labels(service=SERVICE_NAME).inc()
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    finally:
        duration = time.time() - start
        REQUEST_DURATION.labels(service=SERVICE_NAME, method=method, endpoint=endpoint).observe(duration)
        REQUEST_COUNT.labels(service=SERVICE_NAME, method=method, endpoint=endpoint, status_code=str(status_code)).inc()
        ACTIVE_REQUESTS.labels(service=SERVICE_NAME).dec()

@app.get("/metrics")
def metrics():
    return Response(generate_latest(REGISTRY), media_type=CONTENT_TYPE_LATEST)

# ====== Модели ======

class PromoCreate(BaseModel):
    code: str
    discount_percent: float  # 0–100
    expires_at: Optional[datetime] = None
    min_order_amount: float = 0.0
    max_uses: int = 100


class PromoInfo(BaseModel):
    code: str
    discount_percent: float
    expires_at: Optional[datetime]
    min_order_amount: float
    max_uses: int
    used_count: int


class PromoValidateRequest(BaseModel):
    promo_code: str
    user_id: str
    order_amount: float


class PromoValidateResponse(BaseModel):
    valid: bool
    promo_code: str
    discount_amount: float
    discount_percent: float
    message: str


class PromoApplyRequest(BaseModel):
    promo_code: str
    user_id: str
    order_amount: float


class PromoApplyResponse(BaseModel):
    status: str
    promo_code: str
    discount_applied: float
    final_amount: float
    usage_count: int
    max_usages: int


# ====== "База" в памяти ======

promocodes: Dict[str, Dict] = {}


def _calculate_discount(promo: Dict, order_amount: float) -> float:
    return round(order_amount * promo["discount_percent"] / 100.0, 2)


# ====== Эндпоинты ======

@app.post("/api/promocodes", response_model=PromoInfo)
def create_promocode(payload: PromoCreate):
    """
    Создание промокода (условно админская операция).
    Если expires_at не задан, сделаем по дефолту +30 дней.
    """
    code = payload.code.upper()
    if code in promocodes:
        raise HTTPException(status_code=400, detail="Promo code already exists")

    expires_at = payload.expires_at or (datetime.utcnow() + timedelta(days=30))

    promo = {
        "code": code,
        "discount_percent": payload.discount_percent,
        "expires_at": expires_at,
        "min_order_amount": payload.min_order_amount,
        "max_uses": payload.max_uses,
        "used_count": 0,
    }
    promocodes[code] = promo
    return PromoInfo(**promo)


@app.post("/api/promocodes/validate", response_model=PromoValidateResponse)
def validate_promocode(payload: PromoValidateRequest):
    code = payload.promo_code.upper()
    order_amount = payload.order_amount

    promo = promocodes.get(code)
    if not promo:
        return PromoValidateResponse(
            valid=False,
            promo_code=code,
            discount_amount=0.0,
            discount_percent=0.0,
            message="Промокод не найден",
        )

    # --- фикс с датами ---
    now = datetime.utcnow()
    expires_at = promo["expires_at"]
    if expires_at is not None:
        # если дата с таймзоной – отбрасываем tzinfo, сравниваем как "наивные"
        if expires_at.tzinfo is not None:
            expires_at = expires_at.replace(tzinfo=None)

        if expires_at < now:
            return PromoValidateResponse(
                valid=False,
                promo_code=code,
                discount_amount=0.0,
                discount_percent=promo["discount_percent"],
                message="Промокод истёк",
            )
    # ----------------------

    if promo["used_count"] >= promo["max_uses"]:
        return PromoValidateResponse(
            valid=False,
            promo_code=code,
            discount_amount=0.0,
            discount_percent=promo["discount_percent"],
            message="Достигнут лимит использований",
        )

    if order_amount < promo["min_order_amount"]:
        return PromoValidateResponse(
            valid=False,
            promo_code=code,
            discount_amount=0.0,
            discount_percent=promo["discount_percent"],
            message="Сумма заказа меньше минимальной для промокода",
        )

    discount = _calculate_discount(promo, order_amount)

    return PromoValidateResponse(
        valid=True,
        promo_code=code,
        discount_amount=discount,
        discount_percent=promo["discount_percent"],
        message="Промокод применим",
    )



@app.post("/api/promocodes/apply", response_model=PromoApplyResponse)
def apply_promocode(payload: PromoApplyRequest):
    code = payload.promo_code.upper()
    order_amount = payload.order_amount

    promo = promocodes.get(code)
    if not promo:
        raise HTTPException(status_code=404, detail="Promo code not found")

    now = datetime.utcnow()
    expires_at = promo["expires_at"]
    if expires_at is not None:
        if expires_at.tzinfo is not None:
            expires_at = expires_at.replace(tzinfo=None)

        if expires_at < now:
            raise HTTPException(status_code=400, detail="Promo code expired")

    if promo["used_count"] >= promo["max_uses"]:
        raise HTTPException(status_code=400, detail="Promo code usage limit reached")

    if order_amount < promo["min_order_amount"]:
        raise HTTPException(
            status_code=400,
            detail="Order amount is less than minimal for this promo code",
        )

    discount = _calculate_discount(promo, order_amount)
    final_amount = round(order_amount - discount, 2)

    promo["used_count"] += 1

    return PromoApplyResponse(
        status="applied",
        promo_code=code,
        discount_applied=discount,
        final_amount=final_amount,
        usage_count=promo["used_count"],
        max_usages=promo["max_uses"],
    )
