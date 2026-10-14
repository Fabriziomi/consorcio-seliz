from fastapi import APIRouter, Request, BackgroundTasks
from core.logging import logger
from core.config import settings
from infrastructure.evolution_client import evolution_client
from infrastructure.chatwoot_client import chatwoot_client
import json

router = APIRouter()


async def process_incoming_message(payload: dict):
    """Procesamiento asíncrono del mensaje recibido de WhatsApp."""
    event = payload.get("event")
    data = payload.get("data", {})
    
    if event != "messages.upsert":
        return

    key = data.get("key", {})
    remote_jid = key.get("remoteJid", "")
    from_me = key.get("fromMe", False)

    # Ignorar mensajes de grupos o broadcasts
    if "@g.us" in remote_jid or "status@broadcast" in remote_jid:
        return

    # Si es mensaje saliente de Ivana desde su teléfono físico (Takeover)
    if from_me:
        logger.info(f"[TAKEOVER_CHECK] Mensaje saliente de Ivana detectado para {remote_jid}. Silenciando bot.")
        return

    # Extraer texto del mensaje
    message_content = data.get("message", {})
    text = (
        message_content.get("conversation")
        or message_content.get("extendedTextMessage", {}).get("text")
        or ""
    )

    push_name = data.get("pushName", "Vecino")
    logger.info(f"[WEBHOOK_EVOLUTION] Mensaje entrante de {push_name} ({remote_jid}): '{text}'")

    # 1. Enviar a Chatwoot (Intermediario) si está habilitado
    if settings.CHATWOOT_API_ACCESS_TOKEN:
        phone_clean = remote_jid.split("@")[0]
        contact = await chatwoot_client.get_or_create_contact(phone_clean, push_name)
        logger.debug(f"[CHATWOOT_SYNC] Contacto sincronizado en Chatwoot: {contact}")


@router.post("/webhook/evolution")
async def evolution_webhook(request: Request, background_tasks: BackgroundTasks):
    """Receptor oficial de webhooks de Evolution API v2."""
    try:
        payload = await request.json()
        background_tasks.add_task(process_incoming_message, payload)
        return {"status": "received", "event": payload.get("event")}
    except Exception as e:
        logger.error(f"[WEBHOOK_EVOLUTION] Error al decodificar webhook: {e}")
        return {"status": "error", "message": str(e)}
