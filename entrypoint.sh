set -e

mkdir -p /app/static

mkdir -p /app/staticfiles

python manage.py collectstatic --noinput

python manage.py migrate --noinput

exec gunicorn base.wsgi:application --bind 0.0.0.0:$PORT