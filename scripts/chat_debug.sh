#!/usr/bin/env bash
# ==============================================================================
# Script de Simulación de Conversación Local (HTTP Debug) — Consorcio Seliz
# ==============================================================================
# Uso:
#   ./scripts/chat_debug.sh "Hola, cuál es el CBU para pagar expensas?"
#   ./scripts/chat_debug.sh -s HUMAN_OFFICE_HOURS "Hola, están atendiendo?"
#   ./scripts/chat_debug.sh -m "Urgente, hay olor a gas en el palier"
# ==============================================================================

PHONE="+5491144558899"
NAME="Carlos Méndez"
SCHEDULE=""
MESSAGE=""
API_URL="http://localhost:8000/api/v1/debug/chat"

# Parse arguments
while [[ "$#" -gt 0 ]]; do
    case "$1" in
        -p|--phone)
            PHONE="$2"
            shift 2
            ;;
        -n|--name)
            NAME="$2"
            shift 2
            ;;
        -s|--schedule)
            SCHEDULE="$2"
            shift 2
            ;;
        -m|--message)
            MESSAGE="$2"
            shift 2
            ;;
        -h|--help)
            echo "Uso: $0 [opciones] \"mensaje a enviar\""
            echo ""
            echo "Opciones:"
            echo "  -m, --message TEXT      Texto del mensaje a simular"
            echo "  -p, --phone PHONE       Teléfono emisor (por defecto: +5491144558899)"
            echo "  -n, --name NAME         Nombre del vecino (por defecto: Carlos Méndez)"
            echo "  -s, --schedule SCHED    Forzar horario: BOT_ACTIVE_OFF_HOURS | HUMAN_OFFICE_HOURS | QUIET_HOURS"
            echo "  -h, --help              Muestra esta ayuda"
            exit 0
            ;;
        *)
            if [ -z "$MESSAGE" ]; then
                MESSAGE="$1"
            else
                MESSAGE="$MESSAGE $1"
            fi
            shift
            ;;
    esac
done

if [ -z "$MESSAGE" ]; then
    echo "Error: Debes ingresar un mensaje para la prueba."
    echo "Ejemplo: ./scripts/chat_debug.sh \"Hola, cuál es el CBU?\""
    exit 1
fi

# Verificar si el servidor local está activo
if ! curl -s --connect-timeout 1 http://localhost:8000/health > /dev/null 2>&1; then
    echo "[!] La API no parece estar corriendo en http://localhost:8000"
    echo "    Inicia la API en otra terminal ejecutando: ./scripts/start_dev.sh api"
    echo ""
    echo "    Intentando enviar la petición de todos modos..."
fi

# Construir payload JSON
if [ -n "$SCHEDULE" ]; then
    JSON_PAYLOAD=$(cat <<EOF
{
  "message": $(python -c "import json, sys; print(json.dumps(sys.argv[1]))" "$MESSAGE"),
  "phone": "$PHONE",
  "user_name": "$NAME",
  "override_schedule": "$SCHEDULE"
}
EOF
)
else
    JSON_PAYLOAD=$(cat <<EOF
{
  "message": $(python -c "import json, sys; print(json.dumps(sys.argv[1]))" "$MESSAGE"),
  "phone": "$PHONE",
  "user_name": "$NAME"
}
EOF
)
fi

echo ">> Enviando mensaje a la API (POST $API_URL)..."
echo "----------------------------------------------------------------------"

RESPONSE=$(curl -s -X POST "$API_URL" \
    -H "Content-Type: application/json" \
    -d "$JSON_PAYLOAD")

if command -v jq > /dev/null 2>&1; then
    echo "$RESPONSE" | jq .
else
    echo "$RESPONSE" | python -m json.tool
fi
echo "----------------------------------------------------------------------"
