FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/apps/api/src:/app/apps/chatbot/src

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar dependencias de API y Chatbot
COPY apps/api/requirements.txt ./apps/api/requirements.txt
COPY apps/chatbot/requirements.txt ./apps/chatbot/requirements.txt
RUN pip install --no-cache-dir -r ./apps/api/requirements.txt -r ./apps/chatbot/requirements.txt

# Copiar código fuente
COPY apps/api ./apps/api
COPY apps/chatbot ./apps/chatbot

WORKDIR /app/apps/api

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
