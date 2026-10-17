#!/usr/bin/env bash
# ==============================================================================
# Script de Despliegue Automatizado en VPS — Consorcio Seliz
# ==============================================================================

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "================================================================="
echo "Consorcio Seliz — Despliegue en Servidor VPS / Docker Stack"
echo "================================================================="

if ! command -v docker &> /dev/null; then
    echo "[ERROR] Docker no esta instalado en el sistema."
    exit 1
fi

DOCKER_COMPOSE_CMD=""
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker compose"
elif command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker-compose"
else
    echo "[ERROR] Docker Compose no esta disponible."
    exit 1
fi

echo "[OK] Docker y Docker Compose detectados ($DOCKER_COMPOSE_CMD)."

if [ ! -f ".env" ]; then
    echo "[AVISO] No se encontro archivo .env. Creando uno a partir de .env.example..."
    cp .env.example .env
    echo "[OK] Archivo .env generado. Puedes editarlo con tus credenciales si es necesario."
else
    echo "[OK] Archivo .env detectado."
fi

mkdir -p models

echo "[INFO] Levantando servicios con Docker Compose..."
$DOCKER_COMPOSE_CMD up -d --build

echo ""
echo "[INFO] Esperando 10 segundos a que los servicios inicien..."
sleep 10

echo "[INFO] Verificando estado de la API..."
if command -v curl &> /dev/null; then
    HEALTH=$(curl -s http://localhost:8000/health || echo '{"status":"down"}')
    echo "Respuesta de la API: $HEALTH"
fi

echo ""
echo "================================================================="
echo "[OK] Despliegue completado con exito:"
echo "- Dashboard Administrativo : http://<TU_IP_VPS>:3000"
echo "- API Central & Docs       : http://<TU_IP_VPS>:8000/docs"
echo "- Evolution WhatsApp API   : http://<TU_IP_VPS>:8080"
echo "================================================================="
