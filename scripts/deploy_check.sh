#!/bin/bash
set -e

# ==============================================================================
# Script de Verificación y Puesta en Marcha para Producción
# Sistema: Consorcio Seliz — Dra. Ivana Seliz
# ==============================================================================

echo "================================================================="
echo "   Verificación Pre-Vuelo para Producción — Consorcio Seliz     "
echo "================================================================="

# 1. Verificar archivo de entorno .env
if [ ! -f .env ]; then
    echo "⚠️  No se encontró archivo .env. Creando a partir de .env.example..."
    cp .env.example .env
    echo "✅ Archivo .env generado. Por favor revisa y ajusta las credenciales si es necesario."
else
    echo "✅ Archivo .env detectado."
fi

# 2. Verificar modelo local LLM Qwen 2.5 3B
MODEL_FILE="models/qwen2.5-3b-instruct-q4_k_m.gguf"
if [ ! -f "$MODEL_FILE" ]; then
    echo "❌ ERROR: No se encontró el modelo $MODEL_FILE"
    echo "   Descárgalo con: huggingface-cli download Qwen/Qwen2.5-3B-Instruct-GGUF qwen2.5-3b-instruct-q4_k_m.gguf --local-dir models"
    exit 1
else
    MODEL_SIZE=$(ls -lh "$MODEL_FILE" | awk '{print $5}')
    echo "✅ Modelo Qwen 2.5 3B presente ($MODEL_SIZE)."
fi

# 3. Verificar herramientas de contenedor
if ! command -v docker &> /dev/null; then
    echo "❌ ERROR: Docker no está instalado en este servidor."
    exit 1
fi
echo "✅ Docker disponible: $(docker --version)"

# 4. Compilación y arranque
echo ""
echo "🚀 Levantando infraestructura completa con Docker Compose..."
docker compose up -d --build

echo ""
echo "⏳ Esperando inicialización de servicios (PostgreSQL, Redis, API, Frontend)..."
sleep 5

docker compose ps

echo ""
echo "================================================================="
echo "✅ Despliegue completado con éxito."
echo "   - API Gateway:    http://localhost:8000 (Docs: /docs)"
echo "   - Frontend Admin: http://localhost:3000"
echo "   - NocoDB CRM:     http://localhost:8081"
echo "   - Evolution API:  http://localhost:8080"
echo "   - Usuario Inicial: admin@selizadministraciones.com.ar"
echo "   - Clave Inicial:   AdminSeliz2026!"
echo "================================================================="
