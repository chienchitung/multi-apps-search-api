FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=8000
ENV HOST=0.0.0.0

CMD uvicorn main:app --host ${HOST} --port ${PORT} 