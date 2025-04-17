#!/bin/bash
set -e

echo "=== Starting entrypoint.sh ==="

# Create directories
mkdir -p /app/static
mkdir -p /app/staticfiles
mkdir -p /app/mediafiles
echo "Directories created"

# Collect static files
echo "Running collectstatic..."
python manage.py collectstatic --noinput
echo "Collectstatic completed"

# Check configuration
echo "Checking Django configuration..."
python manage.py check
echo "Check completed"

# Apply migrations
echo "Running migrations..."
python manage.py migrate --noinput
echo "Migrations completed"

# Start the server with enhanced diagnostics
echo "Starting gunicorn with enhanced diagnostics..."
exec gunicorn base.wsgi:application --log-level debug --workers 2 --timeout 120 --access-logfile - --error-logfile - --bind 0.0.0.0:$PORT