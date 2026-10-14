#!/usr/bin/env bash
# ==============================================================================
# Script de Inicio Rápido de Desarrollo Local — Consorcio Seliz
# ==============================================================================

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "=== Consorcio Seliz — Entorno de Desarrollo Local ==="
echo "1. Frontend  : Vite + React (http://localhost:3000)"
echo "2. API Core  : FastAPI (http://localhost:8000/docs)"
echo "3. Chatbot   : LangGraph Engine (Simulador / Worker)"
echo "======================================================"

case "$1" in
    api)
        echo "Iniciando API Core en http://localhost:8000..."
        source .venv/bin/activate
        PYTHONPATH=apps/api/src:apps/chatbot/src uvicorn main:app --host 0.0.0.0 --port 8000 --reload
        ;;
    frontend)
        echo "Iniciando Frontend en http://localhost:3000..."
        cd apps/frontend && npm run dev
        ;;
    chatbot)
        echo "Ejecutando pruebas y simulación de mensajes del Chatbot..."
        source .venv/bin/activate
        PYTHONPATH=apps/chatbot/src:apps/api/src python apps/chatbot/src/main.py
        ;;
    test)
        echo "Ejecutando suite completa de tests automatizados..."
        source .venv/bin/activate
        echo "--- Tests de apps/api ---"
        PYTHONPATH=apps/api/src:apps/chatbot/src pytest apps/api/tests
        echo "--- Tests de apps/chatbot ---"
        PYTHONPATH=apps/chatbot/src pytest apps/chatbot/tests
        ;;
    *)
        echo "Uso: ./scripts/start_dev.sh [api | frontend | chatbot | test]"
        exit 1
        ;;
esac
