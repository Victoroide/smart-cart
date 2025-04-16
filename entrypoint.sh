set -a
. .env
set +a

¡python manage.py collectstatic --noinput

exec gunicorn base.wsgi:application --bind 0.0.0.0:8000