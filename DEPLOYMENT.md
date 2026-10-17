# Guía de Despliegue en VPS & Operación — Consorcio Seliz

Este documento detalla la puesta en marcha, arquitectura de contenedores y operación en producción del ecosistema inteligente para la administración de consorcios de la **Dra. Ivana Seliz**.

---

## 1. Arquitectura y Puertos de Producción

| Servicio | Contenedor | Puerto Interno | Puerto Expuesto | Función Principal |
| :--- | :--- | :--- | :--- | :--- |
| **Frontend Dashboard** | `consorcio_frontend` | 3000 | `3000` | Inbox Omnicanal, Tickets, Expedientes, Consorcios y Borradores IA |
| **API Central** | `consorcio_api` | 8000 | `8000` | FastAPI Gateway, endpoints REST, orquestación y webhooks |
| **Chatbot Engine** | `consorcio_chatbot_engine` | - | Interno | ConversationFSM, Tev1 Router, Jev / Gemini 2.5 Flash, Groq Whisper |
| **Evolution API v2** | `consorcio_evolution_api` | 8080 | `8080` | Pasarela oficial de WhatsApp, webhooks y multi-dispositivo |
| **PostgreSQL 15** | `consorcio_postgres` | 5432 | `5432` | Base de datos relacional para Consorcios, Contactos, Tickets y Expedientes |
| **Redis 7** | `consorcio_redis` | 6379 | `6379` | Buffer debounce, colas y Takeover humano (12 hs TTL) |

---

## 2. Requisitos Previos en el Servidor VPS

- **Sistema Operativo:** Ubuntu 22.04 LTS o Debian 12 (o contenedor LXC en Proxmox).
- **Recursos Recomendados:**
  - 8 a 16 GB de RAM.
  - 4 a 6 núcleos vCPU (para inferencia IA en CPU).
  - 40 GB de almacenamiento SSD.
- **Software Base:**
  ```bash
  sudo apt-get update && sudo apt-get install -y git curl docker.io docker-compose-v2
  sudo systemctl enable --now docker
  ```

---

## 3. Despliegue Rápido (Paso a Paso)

### Paso 1: Clonar el repositorio
```bash
git clone https://github.com/Fabriziomi/consorcio-seliz.git
cd consorcio-seliz
```

### Paso 2: Configurar Variables de Entorno
Copiar el archivo de plantilla:
```bash
cp .env.example .env
```
Ajustar los valores clave en `.env`:
- `EVOLUTION_API_KEY`: Clave secreta para la API de WhatsApp.
- `HTTP_CLIENT_TIMEOUT`: Configurado por defecto en `90.0` segundos para evitar cortes por latencia en el VPS.
- `VITE_API_URL`: Dirección IP pública o dominio del VPS (ej. `http://tu-vps.ip:8000`).

### Paso 3: Ejecutar el Script de Despliegue Automatizado
```bash
./scripts/deploy_vps.sh
```
El script levantará todos los contenedores y sembrará automáticamente los consorcios base (*Torre Corrientes y Lavalle*, *Callao 2334*), atributos dinámicos protegidos, contactos y tickets.

---

## 4. Vinculación de WhatsApp (Evolution API v2)

1. Abrir en el navegador: `http://<TU_IP_VPS>:8080`
2. Crear la instancia con el nombre configurado en `.env` (por defecto `ivana_seliz_whatsapp`):
   ```bash
   curl -X POST http://localhost:8080/instance/create \
     -H "apikey: consorcio_api_token_secret" \
     -H "Content-Type: application/json" \
     -d '{
       "instanceName": "ivana_seliz_whatsapp",
       "token": "consorcio_api_token_secret",
       "qrcode": true
     }'
   ```
3. Configurar el Webhook de Evolution API apuntando al backend:
   - **URL:** `http://consorcio_api:8000/api/v1/webhook/evolution`
   - **Eventos:** `MESSAGES_UPSERT`

4. Escanear el código QR con el número de WhatsApp oficial de Dra. Ivana Seliz.

---

## 5. Panel Administrativo Directo y Webhooks Externos (Opcional)

El sistema incluye su propio panel administrativo en `apps/frontend` (disponible en `http://<TU_IP_VPS>:3000`), el cual gestiona en tiempo real conversaciones, expedientes, tickets, consorcios y contactos directamente mediante la API central sin necesidad de instalar o mantener Chatwoot ni NocoDB.

Opcionalmente, si se desea conectar un webhook externo de operador:
1. En el sistema externo, configurar el webhook a:
   - **URL:** `http://<TU_IP_VPS>:8000/api/v1/webhook/chatwoot`
   - **Eventos suscritos:** `Message Created` (mensajes salientes de operador)
2. Cuando el operador responda, el mensaje se despacha por WhatsApp y activa automáticamente el **Takeover Humano** por 12 horas.

---

## 6. Monitoreo y Comandos Útiles

- **Ver estado y logs de los servicios:**
  ```bash
  docker compose ps
  docker compose logs -f api
  docker compose logs -f chatbot-engine
  ```

- **Ejecutar tests en el servidor:**
  ```bash
  docker compose exec api pytest /app/apps/api/tests
  ```

- **Reiniciar servicios tras una actualización:**
  ```bash
  git pull origin main
  docker compose up -d --build
  ```
