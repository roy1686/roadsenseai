FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDOUNTWRITEBYTECODE=1 \
    PORT=8000

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . /app/

RUN mkdir -p /data/processed /data/raw/video_uploads /logs

EXPOSE 8000

CMD uvicorn app.main:app --app-dir backend/api --host 0.0.0.0 --port ${PORT:-8000}
