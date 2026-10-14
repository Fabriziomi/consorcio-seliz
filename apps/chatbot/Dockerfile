FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/apps/chatbot/src:/app/apps/api/src

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar dependencias de Chatbot y API
COPY apps/chatbot/requirements.txt ./apps/chatbot/requirements.txt
COPY apps/api/requirements.txt ./apps/api/requirements.txt
RUN pip install --no-cache-dir -r ./apps/chatbot/requirements.txt -r ./apps/api/requirements.txt

# Copiar código fuente
COPY apps/chatbot ./apps/chatbot
COPY apps/api ./apps/api

WORKDIR /app/apps/chatbot

CMD ["python", "src/main.py"]
