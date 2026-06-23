# Packwell — production image for Cloud Run.
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=config.settings

WORKDIR /app

# Python deps first for layer caching.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App source.
COPY . .

# Bake hashed static assets into the image (no DB needed for this step).
RUN python manage.py collectstatic --noinput

# Cloud Run provides $PORT (default 8080). entrypoint runs migrations then serves.
EXPOSE 8080
CMD ["./entrypoint.sh"]
