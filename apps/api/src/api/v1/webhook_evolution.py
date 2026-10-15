import uuid
from datetime import datetime, timezone
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
    ConversacionModel,
    MensajeModel,
    FaqAprobadaModel,
)
from domain.schemas import (
    RolContacto,
    PrioridadTicket,
    EstadoTicket,
    EstadoConversacion,
    TipoMensaje,
    EnviadoPor,
)
from infrastructure.evolution_client import evolution_client
from infrastructure.chatwoot_client import chatwoot_client
from infrastructure.takeover_service import takeover_service
from infrastructure.debounce_service import debounce_service
from services.ticket_service import (
    process_and_consolidate_ticket,
    extract_consorcio_clue,
    extract_unit_clue,
)
from services.audio_transcriber import audio_transcriber
from services.rag_engine import rag_engine
from engine.graph import decision_graph
from engine.state import ChatState
from core.websocket_manager import ws_manager

router = APIRouter()


async def get_or_create_conversacion(db: AsyncSession, contacto: ContactoModel) -> ConversacionModel:
    """Busca o crea una conversación abierta para el contacto."""
    res = await db.execute(
        select(ConversacionModel).where(ConversacionModel.contacto_id == contacto.id)
    )
    conv = res.scalar_one_or_none()
    if not conv:
        conv = ConversacionModel(
            id=f"conv-{str(uuid.uuid4())[:8]}",
            contacto_id=contacto.id,
            consorcio_id=contacto.consorcio_id,
            estado=EstadoConversacion.OPEN,
            bot_activo=True,
            etiquetas=[],
        )
        db.add(conv)
        await db.commit()
        await db.refresh(conv)
    else:
        if conv.estado == EstadoConversacion.RESOLVED:
            conv.estado = EstadoConversacion.OPEN
        if contacto.consorcio_id and not conv.consorcio_id:
            conv.consorcio_id = contacto.consorcio_id
        await db.commit()
        await db.refresh(conv)
    return conv


async def record_message(
    db: AsyncSession,
    conversacion_id: str,
    contenido: str,
    tipo: TipoMensaje,
    enviado_por: EnviadoPor,
    privado: bool = False,
    whatsapp_message_id: Optional[str] = None,
    media_url: Optional[str] = None,
    media_tipo: Optional[str] = None,
) -> MensajeModel:
    """Persiste un mensaje en el hilo conversacional y actualiza el timestamp de la conversación."""
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    msg = MensajeModel(
        id=f"msg-{str(uuid.uuid4())[:8]}",
        conversacion_id=conversacion_id,
        tipo=tipo,
        contenido=contenido,
        privado=privado,
        enviado_por=enviado_por,
        whatsapp_message_id=whatsapp_message_id,
        media_url=media_url,
        media_tipo=media_tipo,
        leido=False if tipo == TipoMensaje.INCOMING else True,
        creado_el=now,
    )
    db.add(msg)
    c_res = await db.execute(select(ConversacionModel).where(ConversacionModel.id == conversacion_id))
    conv = c_res.scalar_one_or_none()
    if conv:
        conv.ultimo_mensaje_el = now
    await db.commit()
    await db.refresh(msg)

    # Notificar a los clientes WebSocket en tiempo real
    try:
        await ws_manager.broadcast(
            "new_message",
            {
                "conversacion_id": conversacion_id,
                "mensaje": {
                    "id": msg.id,
                    "conversacion_id": msg.conversacion_id,
                    "tipo": msg.tipo.value if hasattr(msg.tipo, "value") else str(msg.tipo),
                    "contenido": msg.contenido,
                    "privado": msg.privado,
                    "enviado_por": msg.enviado_por.value if hasattr(msg.enviado_por, "value") else str(msg.enviado_por),
                    "agente_id": msg.agente_id,
                    "whatsapp_message_id": msg.whatsapp_message_id,
                    "media_url": msg.media_url,
                    "media_tipo": msg.media_tipo,
                    "leido": msg.leido,
                    "creado_el": msg.creado_el.isoformat() if msg.creado_el else None,
                },
            },
        )
    except Exception as e:
        logger.warning(f"[WS] No se pudo emitir broadcast de mensaje: {e}")

    return msg


async def execute_bot_pipeline(remote_jid: str, text: str, push_name: str = "Vecino"):
    """
    Ejecuta el pipeline de decisión LangGraph para un mensaje consolidado.
    Persiste tickets, respuestas y notas internas en la base de datos y despacha por WhatsApp.
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

        # Obtener o crear conversación activa
        conversacion = await get_or_create_conversacion(db, contacto)

        # 2. Extracción previa al grafo: si el contacto no tiene consorcio o unidad, extraer del mensaje
        all_consorcios_res = await db.execute(select(ConsorcioModel).where(ConsorcioModel.activo == True))
        all_consorcios = all_consorcios_res.scalars().all()

        if not consorcio_id:
            detected_c = extract_consorcio_clue(text, all_consorcios)
            if detected_c:
                consorcio_id = detected_c.id
                consorcio_obj = detected_c
                consorcio_nombre = detected_c.nombre
                contacto.consorcio_id = consorcio_id
                await db.commit()
                await db.refresh(contacto)
                logger.info(f"[WEBHOOK_EVOLUTION] Consorcio pre-identificado del mensaje: {consorcio_nombre}")

        if not unidad_funcional:
            detected_u = extract_unit_clue(text)
            if detected_u:
                unidad_funcional = detected_u
                contacto.unidad_funcional = detected_u
                await db.commit()
                await db.refresh(contacto)
                logger.info(f"[WEBHOOK_EVOLUTION] Unidad funcional pre-identificada del mensaje: {unidad_funcional}")

        # Cargar atributos dinámicos del consorcio si ahora está identificado
        if consorcio_id and not atributos_dinamicos:
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

        # 3. Memoria conversacional multi-turno: buscar intención pendiente en mensajes previos
        pending_intent = None
        last_msgs_res = await db.execute(
            select(MensajeModel)
            .where(MensajeModel.conversacion_id == conversacion.id)
            .order_by(MensajeModel.creado_el.desc())
            .limit(3)
        )
        recent_msgs = last_msgs_res.scalars().all()
        for m in recent_msgs:
            if m.enviado_por in (EnviadoPor.BOT, EnviadoPor.AGENTE):
                if "para poder facilitarte los datos de cuenta bancaria" in m.contenido or "SOLICITAR_CONSORCIO_PAGO" in m.contenido:
                    pending_intent = "SOLICITAR_CONSORCIO_PAGO"
                    break
                elif "identificar tu reclamo y coordinarlo a primera hora" in m.contenido or "FUERA_HORARIO_SOLICITAR_EDIFICIO" in m.contenido:
                    pending_intent = "FUERA_HORARIO_SOLICITAR_EDIFICIO"
                    break

        # 4. Sincronizar FAQs activas de la BD con el motor RAG
        faqs_res = await db.execute(select(FaqAprobadaModel).where(FaqAprobadaModel.activo == True))
        db_faqs = faqs_res.scalars().all()
        if db_faqs:
            rag_engine.load_db_faqs(db_faqs)

        # 5. Configurar estado de LangGraph
        initial_state = ChatState(
            phone=phone_wa,
            user_name=contacto.nombre_completo or push_name,
            user_message=text,
            pending_intent=pending_intent,
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

        # 6. Ejecutar el grafo de decisión
        graph_result = decision_graph.invoke(initial_state)
        intent = graph_result.get("intent")
        should_respond = graph_result.get("should_respond", False)
        response_text = graph_result.get("response_text")

        # 7. Gestión de Tickets & Expedientes
        should_create_ticket = (
            (intent in ("EMERGENCIA", "FUERA_HORARIO_TICKET", "FUERA_HORARIO_SOLICITAR_EDIFICIO", "FUERA_HORARIO_CONFIRMACION_EDIFICIO", "PAGO_REALIZADO", "CONSULTA_ATRIBUTO_RESTRINGIDO") or graph_result.get("tev1_decision") == "D")
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
            if ticket_result:
                t_id = ticket_result["id"]
                exp_code = ticket_result.get("expediente_codigo")
                exp_str = f" [Expediente #{exp_code}]" if exp_code else ""
                nota_texto = (
                    f"📋 Ticket registrado automáticamente #{t_id}{exp_str} (Intención: {intent})."
                    if ticket_result["accion"] == "NUEVO_TICKET_CREADO"
                    else f"🚨 ATENCIÓN: El ticket #{t_id}{exp_str} fue escalado a PRIORIDAD CRÍTICA por nuevo mensaje del vecino."
                )
                await record_message(
                    db=db,
                    conversacion_id=conversacion.id,
                    contenido=nota_texto,
                    tipo=TipoMensaje.ACTIVITY,
                    enviado_por=EnviadoPor.BOT,
                    privado=True,
                )

        # 5. Despacho y registro de respuesta del bot por WhatsApp
        if should_respond and response_text:
            await record_message(
                db=db,
                conversacion_id=conversacion.id,
                contenido=response_text,
                tipo=TipoMensaje.OUTGOING,
                enviado_por=EnviadoPor.BOT,
                privado=False,
            )
            try:
                await evolution_client.set_presence(remote_jid, presence="composing", delay_ms=1500)
                sent = await evolution_client.send_text(remote_jid, response_text)
                if sent:
                    logger.info(f"[WEBHOOK_EVOLUTION] Respuesta enviada exitosamente a {remote_jid}")
                else:
                    logger.warning(f"[WEBHOOK_EVOLUTION] Evolution API no disponible o no entregó a {remote_jid}")
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
    message_id = key.get("id")

    # Ignorar mensajes de grupos o broadcasts
    if "@g.us" in remote_jid or "status@broadcast" in remote_jid or not remote_jid:
        return

    push_name = data.get("pushName") or "Vecino"
    phone_clean = remote_jid.split("@")[0].replace("+", "").strip()
    phone_wa = f"+{phone_clean}"

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

    # Persistencia en BD de Contacto y Conversación
    async with AsyncSessionLocal() as db:
        c_res = await db.execute(select(ContactoModel).where(ContactoModel.telefono_wa == phone_wa))
        contacto = c_res.scalar_one_or_none()
        if not contacto:
            contacto = ContactoModel(
                id=f"cont-{str(uuid.uuid4())[:8]}",
                telefono_wa=phone_wa,
                nombre_completo=push_name,
                rol=RolContacto.OTRO,
            )
            db.add(contacto)
            await db.commit()
            await db.refresh(contacto)

        conversacion = await get_or_create_conversacion(db, contacto)

        # CASO 1: Mensaje saliente de la administración física o WhatsApp Web (Takeover Humano)
        if from_me:
            logger.info(f"[TAKEOVER_TRIGGER] Mensaje saliente de la administración para {remote_jid}. Registrando y activando bloqueo.")
            await record_message(
                db=db,
                conversacion_id=conversacion.id,
                contenido=text,
                tipo=TipoMensaje.OUTGOING,
                enviado_por=EnviadoPor.AGENTE,
                whatsapp_message_id=message_id,
            )
            conversacion.bot_activo = False
            await db.commit()
            await takeover_service.set_takeover(remote_jid)
            return

        # CASO 2: Mensaje entrante del vecino -> Registrar siempre en el hilo de mensajes
        await record_message(
            db=db,
            conversacion_id=conversacion.id,
            contenido=text,
            tipo=TipoMensaje.INCOMING,
            enviado_por=EnviadoPor.VECINO,
            whatsapp_message_id=message_id,
        )

    # Verificar si el Takeover Humano está activo para no contestar con el bot
    is_takeover = await takeover_service.is_takeover_active(remote_jid)
    if is_takeover:
        logger.info(f"[TAKEOVER_ACTIVE] Mensaje entrante de {remote_jid} registrado en conversación pero ignorado por el bot (atención humana activa).")
        return

    # CASO 3: Mensaje entrante normal -> Consolidar en Debounce Buffer para ejecución del bot
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
    Receptor de webhooks heredado de Chatwoot.
    Mantiene compatibilidad hacia atrás si hay instancias de Chatwoot enviando eventos.
    """
    try:
        payload = await request.json()
        event = payload.get("event")

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
