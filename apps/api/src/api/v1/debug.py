import time
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from infrastructure.database import get_db
from infrastructure.models import (
    ContactoModel,
    ConsorcioModel,
    ConsorcioAtributoDinamicoModel,
    TicketConsultaModel,
    FaqAprobadaModel,
    ConversacionModel,
    MensajeModel,
)
from domain.schemas import RolContacto, PrioridadTicket, EstadoTicket, EnviadoPor
from services.ticket_service import (
    process_and_consolidate_ticket,
    extract_consorcio_clue,
    extract_unit_clue,
)
from services.rag_engine import rag_engine
from engine.graph import decision_graph
from engine.state import ChatState
from core.logging import logger

router = APIRouter()


class DebugChatRequest(BaseModel):
    message: str = Field(..., description="Texto del mensaje enviado por el vecino")
    phone: str = Field(default="+5491144558899", description="Número telefónico de WhatsApp")
    user_name: Optional[str] = Field(default="Carlos Méndez", description="Nombre del vecino remitente")
    override_schedule: Optional[str] = Field(
        default=None,
        description="Forzar estado horario: BOT_ACTIVE_OFF_HOURS | HUMAN_OFFICE_HOURS | QUIET_HOURS"
    )
    override_time: Optional[str] = Field(
        default=None,
        description="Simular fecha/hora específica (ISO 8601, ej. 2026-10-14T20:30:00)"
    )


class DebugChatResponse(BaseModel):
    phone: str
    user_message: str
    contact: Optional[Dict[str, Any]] = None
    consorcio: Optional[Dict[str, Any]] = None
    schedule_status: str
    is_emergency: bool
    emergency_reasons: List[str]
    is_cordial_close: bool
    is_pure_greeting: bool = False
    is_noise: bool = False
    rag_matched: bool
    rag_faq_id: Optional[str] = None
    rag_score: Optional[float] = None
    tev1_decision: Optional[str] = None
    intent: Optional[str] = None
    should_respond: bool
    response_text: Optional[str] = None
    silent_reason: Optional[str] = None
    latency_metrics: Dict[str, float]
    total_pipeline_ms: float
    ticket_created: Optional[Dict[str, Any]] = None


@router.post("/chat", response_model=DebugChatResponse)
async def debug_chat(req: DebugChatRequest, db: AsyncSession = Depends(get_db)):
    """
    Endpoint de depuración y simulación de mensajes de WhatsApp.
    Permite probar conversaciones completas de forma local con guardrails, tono humano y anti-spam.
    """
    t_start = time.time()
    logger.info(f"[DEBUG_CHAT] Mensaje recibido de {req.phone}: \"{req.message}\"")

    result = await db.execute(select(ContactoModel).where(ContactoModel.telefono_wa == req.phone))
    contacto = result.scalar_one_or_none()

    if not contacto:
        contacto = ContactoModel(
            id=f"cont-{str(uuid.uuid4())[:8]}",
            telefono_wa=req.phone,
            nombre_completo=req.user_name or "Vecino",
            rol=RolContacto.OTRO,
        )
        db.add(contacto)
        await db.commit()
        await db.refresh(contacto)

    consorcio_info = None
    consorcio_nombre = None
    consorcio_id = None
    unidad_funcional = None

    consorcio_obj = None
    atributos_dinamicos = {}

    if contacto:
        consorcio_id = contacto.consorcio_id
        unidad_funcional = contacto.unidad_funcional

    all_consorcios_res = await db.execute(select(ConsorcioModel).where(ConsorcioModel.activo == True))
    all_consorcios = all_consorcios_res.scalars().all()

    if not consorcio_id:
        detected_c = extract_consorcio_clue(req.message, all_consorcios)
        if detected_c:
            consorcio_id = detected_c.id
            consorcio_obj = detected_c
            consorcio_nombre = detected_c.nombre
            contacto.consorcio_id = consorcio_id
            await db.commit()
            await db.refresh(contacto)
    elif not consorcio_obj:
        c_res = await db.execute(select(ConsorcioModel).where(ConsorcioModel.id == consorcio_id))
        consorcio_obj = c_res.scalar_one_or_none()
        if consorcio_obj:
            consorcio_nombre = consorcio_obj.nombre

    if not unidad_funcional:
        detected_u = extract_unit_clue(req.message)
        if detected_u:
            unidad_funcional = detected_u
            contacto.unidad_funcional = detected_u
            await db.commit()
            await db.refresh(contacto)

    if consorcio_obj:
        consorcio_info = {
            "id": consorcio_obj.id,
            "nombre": consorcio_obj.nombre,
            "direccion": consorcio_obj.direccion,
            "cbu": consorcio_obj.cbu_bancario,
            "alias": consorcio_obj.alias_bancario,
        }
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

    pending_intent = None
    last_t_res = await db.execute(
        select(TicketConsultaModel)
        .where(TicketConsultaModel.contacto_id == contacto.id)
        .order_by(TicketConsultaModel.creado_el.desc())
        .limit(1)
    )
    last_ticket = last_t_res.scalar_one_or_none()
    if last_ticket:
        if last_ticket.intencion == "SOLICITAR_CONSORCIO_PAGO":
            pending_intent = "SOLICITAR_CONSORCIO_PAGO"
        elif last_ticket.estado == EstadoTicket.ESPERANDO_RESPUESTA or last_ticket.intencion == "FUERA_HORARIO_SOLICITAR_EDIFICIO":
            pending_intent = "FUERA_HORARIO_SOLICITAR_EDIFICIO"

    faqs_res = await db.execute(select(FaqAprobadaModel).where(FaqAprobadaModel.activo == True))
    db_faqs = faqs_res.scalars().all()
    if db_faqs:
        rag_engine.load_db_faqs(db_faqs)

    schedule_override = req.override_schedule
    if not schedule_override and req.override_time:
        try:
            from guardrails.schedule_evaluator import evaluate_schedule
            parsed_dt = datetime.fromisoformat(req.override_time)
            schedule_override = evaluate_schedule(dt=parsed_dt).value
        except Exception as e:
            logger.warning(f"[DEBUG_CHAT] Error al parsear override_time: {e}")

    initial_state = ChatState(
        phone=req.phone,
        user_name=contacto.nombre_completo if contacto else req.user_name,
        user_message=req.message,
        pending_intent=pending_intent,
        consorcio_id=consorcio_id,
        consorcio_nombre=consorcio_nombre,
        unidad_funcional=unidad_funcional,
        schedule_status=schedule_override,
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

    graph_result = decision_graph.invoke(initial_state)

    ticket_info = None
    intent = graph_result.get("intent")
    is_noise = graph_result.get("is_noise", False)
    is_greeting = graph_result.get("is_pure_greeting", False)
    is_close = graph_result.get("is_cordial_close", False)
    should_respond = graph_result.get("should_respond", True)

    should_create_ticket = (
        (intent in ("EMERGENCIA", "FUERA_HORARIO_TICKET", "FUERA_HORARIO_SOLICITAR_EDIFICIO", "FUERA_HORARIO_CONFIRMACION_EDIFICIO", "SOLICITAR_CONSORCIO_PAGO", "PAGO_REALIZADO", "CONSULTA_ATRIBUTO_RESTRINGIDO") or graph_result.get("tev1_decision") == "D")
        and not is_greeting
        and not is_noise
        and not is_close
        and (should_respond or graph_result.get("is_emergency"))
    )

    if should_create_ticket:
        try:
            res_ticket = await process_and_consolidate_ticket(
                db=db,
                contacto=contacto,
                message=req.message,
                intent=intent,
                is_emergency=graph_result.get("is_emergency", False),
                created_off_hours=True,
                consorcio_id=consorcio_id,
                consorcio_nombre=consorcio_nombre,
            )
            ticket_info = {
                "id": res_ticket["id"],
                "intencion": res_ticket["intencion"],
                "prioridad": res_ticket["prioridad"],
                "estado": res_ticket["estado"],
                "accion": res_ticket["accion"],
                "expediente_id": res_ticket.get("expediente_id"),
                "expediente_codigo": res_ticket.get("expediente_codigo"),
            }
        except Exception as e:
            logger.warning(f"[DEBUG_CHAT] No se pudo guardar ticket en DB: {e}")

    total_pipeline_ms = round((time.time() - t_start) * 1000, 2)

    return DebugChatResponse(
        phone=req.phone,
        user_message=req.message,
        contact={
            "nombre": contacto.nombre_completo if contacto else req.user_name,
            "unidad": unidad_funcional,
            "rol": contacto.rol.value if contacto and contacto.rol else "OTRO",
        } if contacto else None,
        consorcio=consorcio_info,
        schedule_status=graph_result.get("schedule_status", "UNKNOWN"),
        is_emergency=graph_result.get("is_emergency", False),
        emergency_reasons=graph_result.get("emergency_reasons", []),
        is_cordial_close=graph_result.get("is_cordial_close", False),
        is_pure_greeting=graph_result.get("is_pure_greeting", False),
        is_noise=graph_result.get("is_noise", False),
        rag_matched=graph_result.get("rag_matched", False),
        rag_faq_id=graph_result.get("rag_faq_id"),
        rag_score=graph_result.get("rag_score"),
        tev1_decision=graph_result.get("tev1_decision"),
        intent=graph_result.get("intent"),
        should_respond=graph_result.get("should_respond", True),
        response_text=graph_result.get("response_text"),
        silent_reason=graph_result.get("silent_reason"),
        latency_metrics=graph_result.get("latency_metrics", {}),
        total_pipeline_ms=total_pipeline_ms,
        ticket_created=ticket_info,
    )
