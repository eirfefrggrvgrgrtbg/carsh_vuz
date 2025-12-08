# Берём официальный образ Python
FROM python:3.11-slim

# Внутри контейнера работаем из папки /code
WORKDIR /code

# Копируем файл с зависимостями и устанавливаем их
COPY app/requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir -r /code/requirements.txt

# Копируем код приложения внутрь контейнера
COPY app /code/app

# На всякий случай выставим рабочую папку /code
WORKDIR /code

# Команда, которая стартует FastAPI
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8004"]
