import uuid
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Request, BackgroundTasks, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from core.logging import logger
from core.config import settings
from infrastructure.database import AsyncSessionLocal, get_db
from infrastructure.models import (
    ContactoModel,
    ConsorcioModel,
    ConsorcioAtributoDinamicoModel,
    TicketConsultaModel,
)
from domain.schemas import RolContacto, PrioridadTicket, EstadoTicket
from infrastructure.evolution_client import evolution_client
from infrastructure.chatwoot_client import chatwoot_client
from infrastructure.takeover_service import takeover_service
from infrastructure.debounce_service import debounce_service
from services.ticket_service import process_and_consolidate_ticket
from services.audio_transcriber import audio_transcriber
from engine.graph import decision_graph
from engine.state import ChatState

router = APIRouter()


async def execute_bot_pipeline(remote_jid: str, text: str, push_name: str = "Vecino"):
    """
    Ejecuta el pipeline de decisión LangGraph para un mensaje consolidado.
    Persiste tickets en la base de datos y despacha respuestas por WhatsApp y Chatwoot.
    """
    phone_clean = remote_jid.split("@")[0].replace("+", "").strip()
    phone_wa = f"+{phone_clean}"

    async with AsyncSessionLocal() as db:
        # 1. Buscar o registrar contacto en la base de datos
        res = await db.execute(select(ContactoModel).where(ContactoModel.telefono_wa == phone_wa))
        contacto = res.scalar_one_or_none()

        consorcio_id = None
        consorcio_nombre = None
        unidad_funcional = None
        consorcio_obj = None
        atributos_dinamicos = {}

        if not contacto:
            # Auto-registro como contacto no catalogado
            contacto = ContactoModel(
                id=f"cont-{str(uuid.uuid4())[:8]}",
                telefono_wa=phone_wa,
                nombre_completo=push_name,
                rol=RolContacto.OTRO,
            )
            db.add(contacto)
            await db.commit()
            await db.refresh(contacto)
            logger.info(f"[WEBHOOK_EVOLUTION] Nuevo contacto auto-registrado: {push_name} ({phone_wa})")
        else:
            consorcio_id = contacto.consorcio_id
            unidad_funcional = contacto.unidad_funcional
            if consorcio_id:
                c_res = await db.execute(select(ConsorcioModel).where(ConsorcioModel.id == consorcio_id))
                consorcio_obj = c_res.scalar_one_or_none()
                if consorcio_obj:
                    consorcio_nombre = consorcio_obj.nombre
                    dyn_res = await db.execute(
                        select(ConsorcioAtributoDinamicoModel).where(
                            ConsorcioAtributoDinamicoModel.consorcio_id == consorcio_id
                        )
                    )
                    atributos_dinamicos = {
                        attr.clave: {
                            "etiqueta": attr.etiqueta_visible,
                            "valor": attr.valor,
                            "es_publico": attr.es_publico_vecinos,
                        }
                        for attr in dyn_res.scalars().all()
                    }

        # 2. Configurar estado de LangGraph
        initial_state = ChatState(
            phone=phone_wa,
            user_name=contacto.nombre_completo or push_name,
            user_message=text,
            consorcio_id=consorcio_id,
            consorcio_nombre=consorcio_nombre,
            unidad_funcional=unidad_funcional,
            consorcio_cbu=consorcio_obj.cbu_bancario if consorcio_obj else None,
            consorcio_alias=consorcio_obj.alias_bancario if consorcio_obj else None,
            consorcio_cuit=consorcio_obj.cuit if consorcio_obj else None,
            consorcio_email_cobranzas=consorcio_obj.email_cobranzas if consorcio_obj else None,
            consorcio_telefono_guardia=consorcio_obj.telefono_porteria if consorcio_obj else None,
            consorcio_emergencia_ascensores=consorcio_obj.emergencia_ascensores if consorcio_obj else None,
            consorcio_emergencia_plomeria=consorcio_obj.emergencia_plomeria if consorcio_obj else None,
            consorcio_pautas_mudanza=consorcio_obj.pautas_mudanza if consorcio_obj else None,
            atributos_dinamicos=atributos_dinamicos,
        )

        # 3. Ejecutar el grafo de decisión
        graph_result = decision_graph.invoke(initial_state)
        intent = graph_result.get("intent")
        should_respond = graph_result.get("should_respond", False)
        response_text = graph_result.get("response_text")

        # 4. Gestión Inteligente de Tickets & Expedientes (Consolidación 24hs y Cero Duplicados)
        should_create_ticket = (
            (intent in ("EMERGENCIA", "FUERA_HORARIO_TICKET", "PAGO_REALIZADO", "CONSULTA_ATRIBUTO_RESTRINGIDO") or graph_result.get("tev1_decision") == "D")
            and not graph_result.get("is_pure_greeting", False)
            and not graph_result.get("is_noise", False)
            and not graph_result.get("is_cordial_close", False)
        )

        ticket_result = None
        if should_create_ticket:
            ticket_result = await process_and_consolidate_ticket(
                db=db,
                contacto=contacto,
                message=text,
                intent=intent,
                is_emergency=graph_result.get("is_emergency", False),
                created_off_hours=True,
                consorcio_id=consorcio_id,
                consorcio_nombre=consorcio_nombre,
            )

        # 5. Sincronización con Chatwoot
        chatwoot_conv_id = None
        if settings.CHATWOOT_API_ACCESS_TOKEN:
            try:
                cw_contact = await chatwoot_client.get_or_create_contact(phone_clean, push_name)
                if cw_contact:
                    chatwoot_conv_id = await chatwoot_client.get_or_create_conversation(cw_contact.get("id"))
                    if chatwoot_conv_id:
                        # Registrar mensaje entrante en Chatwoot
                        await chatwoot_client.send_message(chatwoot_conv_id, text, is_private=False, message_type="incoming")
                        
                        # CERO INFORMES DUPLICADOS: Solo emitir nota privada si se abrió un ticket nuevo o si escaló a crítico
                        if ticket_result:
                            t_id = ticket_result["id"]
                            exp_code = ticket_result.get("expediente_codigo")
                            exp_str = f" [Expediente #{exp_code}]" if exp_code else ""
                            
                            if ticket_result["accion"] == "NUEVO_TICKET_CREADO":
                                await chatwoot_client.create_private_note(
                                    chatwoot_conv_id,
                                    f"📋 Ticket registrado automáticamente #{t_id}{exp_str} (Intención: {intent})."
                                )
                            elif ticket_result.get("is_escalation"):
                                await chatwoot_client.create_private_note(
                                    chatwoot_conv_id,
                                    f"🚨 ATENCIÓN: El ticket #{t_id}{exp_str} fue escalado a PRIORIDAD CRÍTICA por nuevo mensaje del vecino."
                                )
            except Exception as e:
                logger.warning(f"[WEBHOOK_EVOLUTION] Error al sincronizar con Chatwoot: {e}")

        # 6. Despacho de respuesta por WhatsApp
        if should_respond and response_text:
            try:
                # Simular presencia "digitando..."
                await evolution_client.set_presence(remote_jid, presence="composing", delay_ms=1500)
                # Enviar mensaje
                sent = await evolution_client.send_text(remote_jid, response_text)
                if sent:
                    logger.info(f"[WEBHOOK_EVOLUTION] Respuesta enviada exitosamente a {remote_jid}")
                    # Reflejar en Chatwoot como mensaje saliente
                    if chatwoot_conv_id:
                        await chatwoot_client.send_message(chatwoot_conv_id, response_text, is_private=False)
            except Exception as e:
                logger.error(f"[WEBHOOK_EVOLUTION] Error al despachar respuesta WhatsApp: {e}")


async def process_incoming_message(payload: dict):
    """Procesamiento asíncrono del webhook de Evolution API v2."""
    event = payload.get("event")
    data = payload.get("data", {})

    if event != "messages.upsert":
        return

    key = data.get("key", {})
    remote_jid = key.get("remoteJid", "")
    from_me = key.get("fromMe", False)

    # Ignorar mensajes de grupos o broadcasts
    if "@g.us" in remote_jid or "status@broadcast" in remote_jid or not remote_jid:
        return

    push_name = data.get("pushName") or "Vecino"

    # Extracción de contenido de texto o audio (nota de voz WhatsApp)
    message_content = data.get("message", {})
    text = (
        message_content.get("conversation")
        or message_content.get("extendedTextMessage", {}).get("text")
        or ""
    ).strip()

    is_audio = "audioMessage" in message_content
    if not text and is_audio:
        logger.info(f"[WEBHOOK_EVOLUTION] Nota de voz recibida de {push_name} ({remote_jid}). Iniciando transcripción Whisper...")
        audio_b64 = message_content.get("base64")
        if not audio_b64:
            audio_b64 = await evolution_client.get_media_base64(message_content)

        if audio_b64:
            transcription = await audio_transcriber.transcribe_async(audio_b64)
            if transcription:
                text = transcription.strip()
                logger.info(f"[WEBHOOK_EVOLUTION] Audio transcripto exitosamente para {remote_jid}: '{text}'")

    if not text:
        if is_audio:
            logger.info(f"[WEBHOOK_EVOLUTION] Audio inaudible de {remote_jid}. Solicitando aclaración por texto.")
            prompt_text = "Hola, recibimos tu nota de voz pero no logramos escucharla con claridad. ¿Podrías escribirnos tu consulta brevemente por texto para que podamos ayudarte?"
            await evolution_client.send_text(remote_jid, prompt_text)
        return

    # CASO 1: Mensaje saliente de la administración física (Takeover Humano)
    if from_me:
        logger.info(f"[TAKEOVER_TRIGGER] Mensaje saliente de la administración para {remote_jid}. Activando bloqueo.")
        await takeover_service.set_takeover(remote_jid)
        return

    # CASO 2: Mensaje entrante de vecino -> Verificar si el Takeover Humano está activo
    is_takeover = await takeover_service.is_takeover_active(remote_jid)
    if is_takeover:
        logger.info(f"[TAKEOVER_ACTIVE] Mensaje entrante de {remote_jid} ignorado por el bot (atención humana en curso).")
        # Sincronizar en silencio a Chatwoot para que la administración lo visualice
        if settings.CHATWOOT_API_ACCESS_TOKEN:
            phone_clean = remote_jid.split("@")[0].replace("+", "").strip()
            cw_contact = await chatwoot_client.get_or_create_contact(phone_clean, push_name)
            if cw_contact:
                conv_id = await chatwoot_client.get_or_create_conversation(cw_contact.get("id"))
                if conv_id:
                    await chatwoot_client.send_message(conv_id, text, is_private=False, message_type="incoming")
        return

    # CASO 3: Mensaje entrante normal -> Consolidar en Debounce Buffer
    logger.info(f"[WEBHOOK_EVOLUTION] Mensaje entrante de {push_name} ({remote_jid}): '{text}'")
    await debounce_service.add_message(
        remote_jid,
        text,
        callback=lambda r_jid, c_text: execute_bot_pipeline(r_jid, c_text, push_name)
    )


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


@router.post("/webhook/chatwoot")
async def chatwoot_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Receptor de webhooks de Chatwoot.
    Cuando un operador humano escribe desde el panel de Chatwoot:
    1. Despacha el mensaje por WhatsApp al vecino vía Evolution API.
    2. Activa automáticamente el bloqueo de Takeover para pausar el bot.
    """
    try:
        payload = await request.json()
        event = payload.get("event")

        # Escuchar únicamente mensajes salientes de operadores humanos
        if event == "message_created" and payload.get("message_type") == "outgoing" and not payload.get("private"):
            content = payload.get("content", "").strip()
            conversation = payload.get("conversation", {})
            meta = conversation.get("meta", {})
            sender = meta.get("sender", {})
            phone_number = (
                sender.get("phone_number")
                or conversation.get("contact_inbox", {}).get("source_id")
                or sender.get("identifier")
            )

            if phone_number and content:
                clean_phone = phone_number.replace("+", "").strip()
                remote_jid = f"{clean_phone}@s.whatsapp.net"

                async def _send_and_takeover():
                    logger.info(f"[CHATWOOT_WEBHOOK] Operador humano respondió a {remote_jid}. Activando Takeover y enviando WhatsApp.")
                    await takeover_service.set_takeover(remote_jid)
                    await evolution_client.send_text(remote_jid, content)

                background_tasks.add_task(_send_and_takeover)

        return {"status": "received", "event": event}
    except Exception as e:
        logger.error(f"[CHATWOOT_WEBHOOK] Error al procesar webhook: {e}")
        return {"status": "error", "message": str(e)}


# --- Endpoints de Control de Takeover para el CRM ---
@router.get("/takeover/{phone}/status")
async def get_takeover_status(phone: str):
    """Consulta si el bot está silenciado para un número telefónico."""
    active = await takeover_service.is_takeover_active(phone)
    return {"phone": phone, "takeover_active": active}


@router.post("/takeover/{phone}/lock")
async def activate_takeover(phone: str, duration_seconds: int = 43200):
    """Activa el bloqueo de takeover manual desde el CRM para silenciar el bot."""
    await takeover_service.set_takeover(phone, duration_seconds=duration_seconds)
    return {"phone": phone, "takeover_active": True, "duration_seconds": duration_seconds}


@router.post("/takeover/{phone}/release")
async def release_takeover(phone: str):
    """Reactiva el bot para un número telefónico específico."""
    await takeover_service.release_takeover(phone)
    return {"phone": phone, "takeover_active": False}
