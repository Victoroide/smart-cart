#!/bin/bash
set -a
. .env
set +a

echo "Collecting static files..."
python manage.py collectstatic --noinput

if [ "$USE_S3" = "True" ]; then
    echo "Copying Spectacular static files for local serving..."
    python copy_spectacular_static.py
fi

echo "Static files collection completed"