FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Копирование и установка зависимостей Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn

# Копирование исходного кода
COPY . .

# Создание пользователя без прав root
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Команда для запуска
CMD python manage.py migrate && \
    python manage.py create_currencies && \
    python manage.py create_indexes && \
    python manage.py get_fixings_alltime && \
    gunicorn market_vision_backend.wsgi:application --bind 0.0.0.0:8000 --workers 3 --log-level debug --access-logfile - --error-logfile - 