#!/bin/sh
# Apply any pending migrations, then start the app. Cloud Run sets $PORT.
set -e

python manage.py migrate --noinput

exec gunicorn config.wsgi:application \
    --bind "0.0.0.0:${PORT:-8080}" \
    --workers 2 \
    --threads 4 \
    --timeout 60
