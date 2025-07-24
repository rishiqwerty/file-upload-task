FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml .
COPY poetry.lock .
RUN pip install poetry && poetry install --no-dev
COPY . .
RUN mkdir -p file_upload/data/uploads

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8088"]