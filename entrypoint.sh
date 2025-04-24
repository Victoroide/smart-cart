#!/bin/bash
set -e

echo "=== Starting entrypoint.sh ==="

mkdir -p /app/static
mkdir -p /app/staticfiles
mkdir -p /app/mediafiles
mkdir -p /app/staticfiles/drf_spectacular_sidecar/swagger-ui-dist
echo "Directories created"

echo "Running collectstatic..."
python manage.py collectstatic --noinput
echo "Collectstatic completed"

if [ "$USE_S3" = "True" ]; then
    echo "Copying Spectacular static files for local serving..."
    python copy_spectacular_static.py
    echo "Spectacular static files copied"
fi

echo "Checking Django configuration..."
python manage.py check
echo "Check completed"

echo "Running migrations..."
python manage.py migrate --noinput
echo "Migrations completed"

echo "Starting gunicorn with enhanced diagnostics..."
exec gunicorn base.wsgi:application --log-level debug --workers 2 --timeout 120 --access-logfile - --error-logfile - --bind 0.0.0.0:$PORT