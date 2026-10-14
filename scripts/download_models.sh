#!/usr/bin/env bash
# Script para descargar modelos locales a la carpeta /models

set -e

MODELS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/models"
mkdir -p "$MODELS_DIR"

echo "=== Directorio de Modelos: $MODELS_DIR ==="

# 1. Tev1 0.8B (Conjunto Cerrado GGUF)
TEV1_FILE="$MODELS_DIR/tev1-0.8b-q4_k_m.gguf"
if [ ! -f "$TEV1_FILE" ]; then
    echo "Descargando Tev1 0.8B Q4_K_M GGUF..."
    # URL de HuggingFace de Tev1 / Qwen cuantizado
    curl -L "https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/qwen2.5-0.5b-instruct-q4_k_m.gguf" -o "$TEV1_FILE"
    echo "Tev1 descargado exitosamente."
else
    echo "Tev1 0.8B ya existe en $TEV1_FILE."
fi

echo "=== Descarga completada ==="
