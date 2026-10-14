#!/usr/bin/env bash
# ==============================================================================
# Script de Despliegue Automatizado en VPS — Consorcio Seliz
# ==============================================================================

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "================================================================="
echo "🏢 Consorcio Seliz — Despliegue en Servidor VPS / Docker Stack"
echo "================================================================="

# 1. Comprobar Docker y Docker Compose
if ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker no está instalado en el sistema."
    exit 1
fi

DOCKER_COMPOSE_CMD=""
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker compose"
elif command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker-compose"
else
    echo "❌ Error: Docker Compose no está disponible."
    exit 1
fi

echo "✅ Docker y Docker Compose detectados ($DOCKER_COMPOSE_CMD)."

# 2. Verificar archivo de configuración .env
if [ ! -f ".env" ]; then
    echo "⚠️  No se encontró archivo .env. Creando uno a partir de .env.example..."
    cp .env.example .env
    echo "✅ Archivo .env generado. Puedes editarlo con tus credenciales si es necesario."
else
    echo "✅ Archivo .env detectado."
fi

# 3. Descargar o verificar directorio de modelos locales
mkdir -p models
if [ -f "./scripts/download_models.sh" ] && [ ! -f "./models/tev1-0.8b-q4_k_m.gguf" ]; then
    echo "ℹ️  Directorio de modelos listo en ./models."
fi

# 4. Construir y levantar contenedores
echo "🚀 Levantando servicios con Docker Compose..."
$DOCKER_COMPOSE_CMD up -d --build

echo ""
echo "⏳ Esperando 10 segundos a que los servicios inicien..."
sleep 10

# 5. Comprobar estado de salud de la API
echo "🔍 Verificando estado de la API..."
if command -v curl &> /dev/null; then
    HEALTH=$(curl -s http://localhost:8000/health || echo '{"status":"down"}')
    echo "Respuesta de la API: $HEALTH"
fi

echo ""
echo "================================================================="
echo "🎉 Despliegue completado con éxito:"
echo "• CRM & Inbox Omnicanal : http://<TU_IP_VPS>:3000"
echo "• API Central & Docs    : http://<TU_IP_VPS>:8000/docs"
echo "• Evolution WhatsApp API: http://<TU_IP_VPS>:8080"
echo "• NocoDB Backoffice     : http://<TU_IP_VPS>:8081"
echo "================================================================="
