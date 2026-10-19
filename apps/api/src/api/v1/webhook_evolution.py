import uuid
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Request, BackgroundTasks, HTTPException, Depends, status
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
from infrastructure.takeover_service import takeover_service
from infrastructure.debounce_service import debounce_service
from services.ticket_service import process_and_consolidate_ticket
from services.audio_transcriber import audio_transcriber
from services.openrouter_client import OpenRouterClient
from services.templates import render_template
from engine.fsm import ConversationFSM
from engine.state_models import (
    FSMState,
    FSMContext,
    DecisionResultado,
    Intencion,
)
from guardrails.schedule_evaluator import evaluate_schedule, ScheduleStatus
from core.websocket_manager import ws_manager

router = APIRouter()
openrouter_client = OpenRouterClient()


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
            fsm_estado=FSMState.IDLE.value,
            fsm_contexto={},
            needs_human_review=False,
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


async def execute_fsm_bot_pipeline(
    remote_jid: str,
    text: str,
    has_attachment: bool = False,
    push_name: str = "Vecino",
):
    """
    Ejecuta el pipeline determinista ConversationFSM + OpenRouter (Jev 1.14 / Gemini).
    """
    phone_clean = remote_jid.split("@")[0].replace("+", "").strip()
    phone_wa = f"+{phone_clean}"
    now_utc = datetime.now(timezone.utc).replace(tzinfo=None)

    async with AsyncSessionLocal() as db:
        res = await db.execute(select(ContactoModel).where(ContactoModel.telefono_wa == phone_wa))
        contacto = res.scalar_one_or_none()

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
            logger.info(f"[FSM_PIPELINE] Nuevo contacto auto-registrado: {push_name} ({phone_wa})")

        if contacto.bot_desactivado:
            logger.info(f"[FSM_PIPELINE] Contacto {phone_wa} tiene bot_desactivado=True. Silencio permanente.")
            return

        conversacion = await get_or_create_conversacion(db, contacto)

        if conversacion.ultimo_mensaje_el:
            diff_minutes = (now_utc - conversacion.ultimo_mensaje_el).total_seconds() / 60.0
            if diff_minutes > settings.SESSION_TTL_MINUTES:
                logger.info(
                    f"[FSM_PIPELINE] Sesión expirada ({diff_minutes:.1f} min > {settings.SESSION_TTL_MINUTES} min). Reseteando a IDLE."
                )
                conversacion.fsm_estado = FSMState.IDLE.value
                conversacion.fsm_contexto = {}
                await db.commit()
                await db.refresh(conversacion)

        raw_state = conversacion.fsm_estado or FSMState.IDLE.value
        try:
            current_state = FSMState(raw_state)
        except ValueError:
            current_state = FSMState.IDLE

        ctx_dict = conversacion.fsm_contexto or {}
        current_context = FSMContext(**ctx_dict)
        current_context.has_attachment = has_attachment

        consorcios_res = await db.execute(select(ConsorcioModel).where(ConsorcioModel.activo == True))
        consorcios_objs = consorcios_res.scalars().all()
        catalog = [
            {"id": c.id, "nombre": c.nombre, "direccion": c.direccion}
            for c in consorcios_objs
        ]

        has_c = bool(contacto.consorcio_id)
        has_u = bool(contacto.unidad_funcional)

        decision = await openrouter_client.classify_intent(
            text=text,
            has_consorcio=has_c,
            has_unidad=has_u,
            consorcios_catalog=catalog,
        )

        logger.info(
            f"[FSM_PIPELINE] Decisión {decision.model_used}: intent={decision.intencion} (conf={decision.confidence:.2f}, lat={decision.latency_ms:.0f}ms)"
        )

        contact_updated = False
        if decision.consorcio_mencionado and decision.consorcio_mencionado not in ("OTRO_NO_ADMINISTRADO", "NINGUNO"):
            if not contacto.consorcio_id:
                contacto.consorcio_id = decision.consorcio_mencionado
                contact_updated = True
                logger.info(f"[EARLY_BINDING] Consorcio asignado a contacto {phone_wa}: {decision.consorcio_mencionado}")

        if decision.contiene_unidad and decision.unidad_funcional:
            if not contacto.unidad_funcional:
                contacto.unidad_funcional = decision.unidad_funcional
                contact_updated = True
                logger.info(f"[EARLY_BINDING] Unidad asignada a contacto {phone_wa}: {decision.unidad_funcional}")

        if contact_updated:
            await db.commit()
            await db.refresh(contacto)

        consorcio_data = None
        target_consorcio_id = contacto.consorcio_id or decision.consorcio_mencionado
        if target_consorcio_id:
            c_obj = next((c for c in consorcios_objs if c.id == target_consorcio_id), None)
            if c_obj:
                consorcio_data = {
                    "id": c_obj.id,
                    "nombre": c_obj.nombre,
                    "direccion": c_obj.direccion,
                    "cbu_bancario": c_obj.cbu_bancario,
                    "alias_bancario": c_obj.alias_bancario,
                    "cuit": c_obj.cuit,
                    "email_cobranzas": c_obj.email_cobranzas,
                    "telefono_porteria": c_obj.telefono_porteria,
                    "emergencia_ascensores": c_obj.emergencia_ascensores,
                    "emergencia_plomeria": c_obj.emergencia_plomeria,
                    "pautas_mudanza": c_obj.pautas_mudanza,
                }

        schedule_status = evaluate_schedule()
        is_quiet_hours = (schedule_status == ScheduleStatus.QUIET_HOURS)

        count_res = await db.execute(
            select(MensajeModel.id).where(MensajeModel.conversacion_id == conversacion.id)
        )
        historial_len = len(count_res.scalars().all())

        contact_profile = {
            "id": contacto.id,
            "nombre_completo": contacto.nombre_completo or push_name,
            "telefono_wa": contacto.telefono_wa,
            "consorcio_id": contacto.consorcio_id,
            "unidad_funcional": contacto.unidad_funcional,
        }

        resultado = ConversationFSM.process_step(
            state=current_state,
            context=current_context,
            decision=decision,
            contact_profile=contact_profile,
            consorcio_data=consorcio_data,
            incoming_text=text,
            is_quiet_hours=is_quiet_hours,
            historial_len=historial_len,
            now=now_utc,
        )

        if resultado.early_bind_consorcio_id and not contacto.consorcio_id:
            contacto.consorcio_id = resultado.early_bind_consorcio_id
            await db.commit()

        if resultado.early_bind_unidad and not contacto.unidad_funcional:
            contacto.unidad_funcional = resultado.early_bind_unidad
            await db.commit()

        conversacion.fsm_estado = resultado.nuevo_estado.value
        conversacion.fsm_contexto = resultado.nuevo_contexto.model_dump()
        if resultado.needs_human_review:
            conversacion.needs_human_review = True
        if contacto.consorcio_id and not conversacion.consorcio_id:
            conversacion.consorcio_id = contacto.consorcio_id

        await db.commit()

        should_create_ticket = (
            (resultado.needs_human_review or decision.is_emergency)
            and decision.intencion not in (Intencion.CIERRE_CORDIAL.value, Intencion.CONSULTA_EXPENSAS.value)
        )

        if should_create_ticket:
            ticket_res = await process_and_consolidate_ticket(
                db=db,
                contacto=contacto,
                message=text,
                intent=decision.intencion,
                is_emergency=decision.is_emergency,
                created_off_hours=True,
                consorcio_id=contacto.consorcio_id,
                consorcio_nombre=consorcio_data.get("nombre") if consorcio_data else None,
            )
            if ticket_res:
                t_id = ticket_res["id"]
                exp_code = ticket_res.get("expediente_codigo")
                exp_str = f" [Expediente #{exp_code}]" if exp_code else ""
                nota_texto = (
                    f"Ticket registrado #{t_id}{exp_str} (Intención: {decision.intencion}, Estado FSM: {resultado.nuevo_estado.value})."
                    if ticket_res["accion"] == "NUEVO_TICKET_CREADO"
                    else f"Ticket #{t_id}{exp_str} escalado a PRIORIDAD CRÍTICA por nuevo mensaje del vecino."
                )
                await record_message(
                    db=db,
                    conversacion_id=conversacion.id,
                    contenido=nota_texto,
                    tipo=TipoMensaje.ACTIVITY,
                    enviado_por=EnviadoPor.BOT,
                    privado=True,
                )

        if resultado.silencio:
            logger.info(f"[FSM_PIPELINE] Silencio aplicado para {remote_jid}. Motivo: {resultado.razon_silencio}")
            return

        if not resultado.template_rendered:
            return

        if settings.BOT_SHADOW_MODE:
            logger.info(
                f"[BOT_SHADOW_MODE] Respuesta proyectada no despachada a {remote_jid}: {resultado.template_rendered[:100]}..."
            )
            return

        await record_message(
            db=db,
            conversacion_id=conversacion.id,
            contenido=resultado.template_rendered,
            tipo=TipoMensaje.OUTGOING,
            enviado_por=EnviadoPor.BOT,
            privado=False,
        )

        try:
            sent = await evolution_client.send_text_with_typing(
                remote_jid,
                resultado.template_rendered,
                min_seconds=1.3,
                max_seconds=4.2,
                base_chars_per_sec=35.0,
            )
            if sent:
                logger.info(f"[FSM_PIPELINE] Plantilla '{resultado.template_key}' enviada exitosamente a {remote_jid}")
            else:
                logger.warning(f"[FSM_PIPELINE] Fallo envío a {remote_jid} vía Evolution API")
        except Exception as e:
            logger.error(f"[FSM_PIPELINE] Error al despachar WhatsApp a {remote_jid}: {e}")


execute_bot_pipeline = execute_fsm_bot_pipeline


async def process_incoming_message(payload: dict):
    """Procesamiento asíncrono y guardrails del webhook de Evolution API v2."""
    event = payload.get("event")
    data = payload.get("data", {})

    if event != "messages.upsert":
        return

    key = data.get("key", {})
    remote_jid = key.get("remoteJid", "")
    from_me = key.get("fromMe", False)
    message_id = key.get("id")
    message_content = data.get("message", {})
    if (
        "@g.us" in remote_jid
        or "status@broadcast" in remote_jid
        or not remote_jid
        or "reactionMessage" in message_content
    ):
        return

    push_name = data.get("pushName") or "Vecino"
    phone_clean = remote_jid.split("@")[0].replace("+", "").strip()
    phone_wa = f"+{phone_clean}"
    now_utc = datetime.now(timezone.utc).replace(tzinfo=None)

    text = (
        message_content.get("conversation")
        or message_content.get("extendedTextMessage", {}).get("text")
        or ""
    ).strip()

    context_info = message_content.get("extendedTextMessage", {}).get("contextInfo") or message_content.get("contextInfo") or {}
    quoted_msg = context_info.get("quotedMessage", {})
    quoted_text = quoted_msg.get("conversation") or quoted_msg.get("extendedTextMessage", {}).get("text")
    if quoted_text and isinstance(quoted_text, str) and quoted_text.strip():
        text = f'[Citando: "{quoted_text.strip()}"] {text}'.strip()

    is_audio = "audioMessage" in message_content
    has_attachment = bool(
        "imageMessage" in message_content
        or "documentMessage" in message_content
        or "documentWithCaptionMessage" in message_content
    )

    if has_attachment and not text:
        caption = (
            message_content.get("imageMessage", {}).get("caption")
            or message_content.get("documentMessage", {}).get("caption")
            or ""
        ).strip()
        if caption:
            text = caption

    if not text and is_audio:
        logger.info(f"[WEBHOOK_EVOLUTION] Nota de voz recibida de {push_name} ({remote_jid}). Iniciando transcripción...")
        audio_b64 = message_content.get("base64")
        if not audio_b64:
            audio_b64 = await evolution_client.get_media_base64(message_content)

        if audio_b64:
            transcription = await audio_transcriber.transcribe_async(audio_b64)
            if transcription:
                text = transcription.strip()
                logger.info(f"[WEBHOOK_EVOLUTION] Audio transcripto exitosamente para {remote_jid}: '{text}'")

    if not text and not has_attachment:
        if is_audio:
            logger.info(f"[WEBHOOK_EVOLUTION] Audio inaudible de {remote_jid}. Solicitando aclaración por texto.")
            prompt_text = render_template("AUDIO_INVALIDO", historial_len=0, user_name=push_name)
            await evolution_client.send_text_with_typing(remote_jid, prompt_text)
        return

    profile_pic = (
        data.get("profilePicUrl")
        or data.get("senderPhoto")
        or (data.get("sender") or {}).get("profilePictureUrl")
        or (data.get("contact") or {}).get("profilePicUrl")
    )

    async with AsyncSessionLocal() as db:
        c_res = await db.execute(select(ContactoModel).where(ContactoModel.telefono_wa == phone_wa))
        contacto = c_res.scalar_one_or_none()
        if not contacto:
            contacto = ContactoModel(
                id=f"cont-{str(uuid.uuid4())[:8]}",
                telefono_wa=phone_wa,
                nombre_completo=push_name,
                rol=RolContacto.OTRO,
                foto_url=profile_pic,
                bot_desactivado=False,
            )
            db.add(contacto)
            await db.commit()
            await db.refresh(contacto)
        elif profile_pic and not contacto.foto_url:
            contacto.foto_url = profile_pic
            await db.commit()

        conversacion = await get_or_create_conversacion(db, contacto)

        if from_me:
            is_bot_msg = await takeover_service.is_bot_message_id(message_id)
            if is_bot_msg:
                return

            logger.info(f"[TAKEOVER_TRIGGER] Intervención manual de Ivana para {remote_jid}. Activando Takeover por 12h.")
            await record_message(
                db=db,
                conversacion_id=conversacion.id,
                contenido=text or "[Adjunto saliente]",
                tipo=TipoMensaje.OUTGOING,
                enviado_por=EnviadoPor.AGENTE,
                whatsapp_message_id=message_id,
            )
            conversacion.bot_activo = False
            conversacion.ultimo_takeover_at = now_utc
            await db.commit()
            await takeover_service.set_takeover(remote_jid, duration_seconds=settings.TAKEOVER_TTL_HOURS * 3600)
            return

        await record_message(
            db=db,
            conversacion_id=conversacion.id,
            contenido=text or "[Archivo adjunto sin texto]",
            tipo=TipoMensaje.INCOMING,
            enviado_por=EnviadoPor.VECINO,
            whatsapp_message_id=message_id,
        )

        if not settings.BOT_GLOBAL_ENABLED:
            logger.info("[WEBHOOK_EVOLUTION] BOT_GLOBAL_ENABLED=False. Silencio total.")
            return

        if contacto.bot_desactivado:
            logger.info(f"[WEBHOOK_EVOLUTION] Contacto {phone_wa} excluido (bot_desactivado=True). Silencio.")
            return

    is_takeover = await takeover_service.is_takeover_active(remote_jid)
    if is_takeover:
        logger.info(f"[TAKEOVER_ACTIVE] Mensaje de {remote_jid} registrado pero ignorado por Takeover activo.")
        return

    schedule_status = evaluate_schedule()
    if schedule_status == ScheduleStatus.HUMAN_OFFICE_HOURS:
        logger.info(f"[HORARIO_OFICINA] Mensaje de {remote_jid} recibido en horario laboral. Silencio para atención humana.")
        return

    logger.info(f"[WEBHOOK_EVOLUTION] Encolando mensaje de {push_name} ({remote_jid}) para ejecución FSM.")
    if settings.BYPASS_DEBOUNCE_BUFFER or settings.FAST_DEBUG_MODE:
        await execute_fsm_bot_pipeline(remote_jid, text, has_attachment=has_attachment, push_name=push_name)
    else:
        await debounce_service.add_message(
            remote_jid,
            text,
            callback=lambda r_jid, c_text: execute_fsm_bot_pipeline(
                r_jid, c_text, has_attachment=has_attachment, push_name=push_name
            ),
        )


def verify_webhook_token(request: Request) -> bool:
    """Valida la autenticidad del webhook entrante contra los tokens autorizados del sistema."""
    if not settings.ENABLE_WEBHOOK_AUTH:
        return True

    token = (
        request.headers.get("apikey")
        or request.headers.get("x-api-key")
        or request.headers.get("X-Webhook-Token")
        or request.query_params.get("token")
        or request.query_params.get("apikey")
    )
    if not token and "Authorization" in request.headers:
        auth_header = request.headers["Authorization"]
        if auth_header.startswith("Bearer "):
            token = auth_header.split("Bearer ", 1)[1].strip()

    valid_tokens = {settings.WEBHOOK_SECRET_TOKEN, settings.EVOLUTION_API_KEY}
    valid_tokens.discard(None)

    client_ip = request.client.host if request.client else "desconocida"
    if not token or token not in valid_tokens:
        logger.warning(f"[SECURITY_ALERT] Webhook no autorizado rechazado desde IP {client_ip}.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticación de webhook ausente o inválido.",
        )
    return True


@router.post("/webhook/evolution", dependencies=[Depends(verify_webhook_token)])
async def evolution_webhook(request: Request, background_tasks: BackgroundTasks):
    """Receptor oficial de webhooks de Evolution API v2."""
    try:
        payload = await request.json()
        background_tasks.add_task(process_incoming_message, payload)
        return {"status": "received", "event": payload.get("event")}
    except Exception as e:
        logger.error(f"[WEBHOOK_EVOLUTION] Error al decodificar webhook: {e}")
        return {"status": "error", "message": str(e)}


@router.post("/webhook/chatwoot", dependencies=[Depends(verify_webhook_token)])
async def chatwoot_webhook(request: Request, background_tasks: BackgroundTasks):
    """Receptor de webhooks para Chatwoot con activación de takeover."""
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
                    logger.info(f"[CHATWOOT_WEBHOOK] Operador manual respondió a {remote_jid}. Activando Takeover por 12h.")
                    await takeover_service.set_takeover(remote_jid, duration_seconds=settings.TAKEOVER_TTL_HOURS * 3600)
                    await evolution_client.send_text(remote_jid, content)

                background_tasks.add_task(_send_and_takeover)

        return {"status": "received", "event": event}
    except Exception as e:
        logger.error(f"[CHATWOOT_WEBHOOK] Error al procesar webhook: {e}")
        return {"status": "error", "message": str(e)}


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
