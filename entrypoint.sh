#!/bin/bash
set -e

echo "=== Starting entrypoint.sh ==="

mkdir -p /static
mkdir -p /staticfiles
mkdir -p /mediafiles
mkdir -p /staticfiles/drf_spectacular_sidecar/swagger-ui-dist

echo "Running Django management commands..."

echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

echo "Applying database migrations..."
python manage.py migrate --noinput

echo "Extracting Spectacular static files (if applicable)..."
python extract_spectacular_static.py || echo "extract_spectacular_static.py not found or failed, continuing..."

echo "Starting Gunicorn server..."
exec gunicorn base.wsgi:application \
    --name ficct-ecommerce-app \
    --bind 0.0.0.0:$PORT \
    --workers 2 \
    --timeout 120 \
    --log-level debug \
    --access-logfile '-' \
    --error-logfile '-'