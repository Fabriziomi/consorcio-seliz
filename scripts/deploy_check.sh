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
    echo "[AVISO] No se encontro archivo .env. Creando a partir de .env.example..."
    cp .env.example .env
    echo "[OK] Archivo .env generado. Por favor revisa y ajusta las credenciales si es necesario."
else
    echo "[OK] Archivo .env detectado."
fi

if ! command -v docker &> /dev/null; then
    echo "[ERROR] Docker no esta instalado en este servidor."
    exit 1
fi
echo "[OK] Docker disponible: $(docker --version)"

echo ""
echo "[INFO] Levantando infraestructura completa con Docker Compose..."
docker compose up -d --build

echo ""
echo "[INFO] Esperando inicializacion de servicios (PostgreSQL, Redis, API, Frontend)..."
sleep 5

docker compose ps

echo ""
echo "================================================================="
echo "[OK] Despliegue completado con exito."
echo "   - API Gateway:    http://localhost:8000 (Docs: /docs)"
echo "   - Frontend Admin: http://localhost:3000"
echo "   - Evolution API:  http://localhost:8080"
echo "   - Usuario Inicial: admin@selizadministraciones.com.ar"
echo "   - Clave Inicial:   AdminSeliz2026!"
echo "================================================================="
