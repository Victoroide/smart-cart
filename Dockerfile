FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PORT=8000

WORKDIR /app

RUN apt-get update \
    && apt-get install -y gcc libpq-dev dos2unix wget gnupg lsb-release \
    && rm -rf /var/lib/apt/lists/*

RUN sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list' && \
    wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add - && \
    apt-get update && \
    apt-get install -y postgresql-client-17

COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY . .

RUN mkdir -p /app/static /app/staticfiles /app/mediafiles
RUN mkdir -p /app/staticfiles/drf_spectacular_sidecar/swagger-ui-dist

RUN dos2unix entrypoint.sh && chmod +x entrypoint.sh

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]