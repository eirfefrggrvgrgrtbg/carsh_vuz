FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Ставим нужные библиотеки (один раз для всего сервиса)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
        fastapi \
        uvicorn[standard] \
        sqlalchemy \
        pydantic \
        email-validator

# Кладём внутрь только код этого сервиса
COPY fines_service/app ./app

EXPOSE 8000

# Стартуем FastAPI
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
