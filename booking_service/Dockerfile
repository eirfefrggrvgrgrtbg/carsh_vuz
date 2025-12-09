# booking_service/Dockerfile
FROM python:3.11-slim

# Рабочая директория внутри контейнера
WORKDIR /app

# Копируем общий requirements.txt из корня репозитория
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код сервиса
COPY booking_service ./booking_service

# Чтобы Python видел корень проекта
ENV PYTHONPATH=/app

# Заходим внутрь сервиса
WORKDIR /app/booking_service

# Запуск FastAPI-приложения
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]
