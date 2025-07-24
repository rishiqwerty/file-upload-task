# celery_worker.Dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml poetry.lock ./
RUN pip install poetry && poetry install --no-root

COPY . .

CMD ["celery", "-A", "app.tasks", "worker", "--loglevel=info"]
