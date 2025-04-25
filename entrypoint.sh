#!/bin/bash
set -e

echo "=== Starting entrypoint.sh ==="

mkdir -p /app/static
mkdir -p /app/staticfiles
mkdir -p /app/mediafiles
mkdir -p /app/staticfiles/drf_spectacular_sidecar/swagger-ui-dist
echo "Directories created"

echo "Extracting Spectacular static files..."
python extract_spectacular_static.py
echo "Spectacular files extracted"

echo "Running collectstatic..."
python manage.py collectstatic --noinput
echo "Collectstatic completed"

exec gunicorn base.wsgi:application --log-level debug --workers 2 --timeout 120 --access-logfile - --error-logfile - --bind 0.0.0.0:$PORT