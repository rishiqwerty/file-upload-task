FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p file_upload/data/uploads

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8088"]