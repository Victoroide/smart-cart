#!/bin/bash
set -a
. .env
set +a
python manage.py collectstatic --noinput