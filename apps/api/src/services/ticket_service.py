import re
import uuid
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from core.logging import logger
from domain.schemas import (
    PrioridadTicket,
    EstadoTicket,
    CategoriaIncidencia,
    EstadoExpediente,
)
from infrastructure.models import (
    ContactoModel,
    ConsorcioModel,
    TicketConsultaModel,
    ExpedienteIncidenciaModel,
)
from services.semantic_extractor import semantic_extractor


def extract_unit_clue(message: str) -> Optional[str]:
    """Extrae indicios de unidad funcional o departamento del texto."""
    raw = message.strip()
    patterns = [
        r"(?:piso\s*(\d{1,2})\s*(?:depto|dto|departamento)?\s*([a-zA-Z]))",
        r"(?:depto|dto|departamento|unidad|uf)\s*([0-9]{1,4}\s*[a-zA-Z]?)",
        r"\b(\d{1,2}[°º]?\s*[a-zA-Z])\b",
        r"\b(cochera\s*\d{1,3})\b",
        r"\b(pb\s*[a-zA-Z]?)\b",
    ]
    for pat in patterns:
        m = re.search(pat, raw, re.IGNORECASE)
        if m:
            groups = [g for g in m.groups() if g]
            if len(groups) == 2:
                return f"{groups[0]}° {groups[1].upper()}"
            elif len(groups) == 1:
                val = groups[0].strip().upper()
                return val
    return None


def extract_consorcio_clue(message: str, consorcios: List[ConsorcioModel]) -> Optional[ConsorcioModel]:
    """Compara palabras clave del mensaje con los consorcios activos en base de datos."""
    msg_lower = message.lower()
    for c in consorcios:
        text_corpus = f"{c.nombre} {c.direccion}".lower()
        keywords = [
            w for w in re.findall(r"\w+", text_corpus)
            if len(w) >= 5 and w not in ("torres", "consorcio", "avenida", "calle", "galeria", "cochera")
        ]
        if any(kw in msg_lower for kw in keywords):
            return c
    return None


def classify_incident_category(message: str, intent: Optional[str] = None) -> CategoriaIncidencia:
    """Clasifica el reclamo o consulta en una categoría edilicia estandarizada."""
    m = message.lower()
    
    if any(k in m for k in ("ascensor", "elevador", "montacargas", "atrapad", "botonera")):
        return CategoriaIncidencia.ASCENSORES
    if any(k in m for k in ("agua", "caño", "plomer", "inund", "filtrac", "gotera", "desagüe", "desague", "bomba", "tanque", "llave de paso", "canilla", "desborde")):
        return CategoriaIncidencia.PLOMERIA
    if any(k in m for k in ("luz", "electric", "fase", "térmica", "termica", "disyuntor", "tablero", "cortocircuito", "enchufe", "toma")):
        return CategoriaIncidencia.ELECTRICIDAD
    if any(k in m for k in ("gas", "caldera", "calefacc", "estufa", "termotanque", "tiro balanceado", "olor a gas")):
        return CategoriaIncidencia.GAS_CALEFACCION
    if any(k in m for k in ("porton", "portón", "cochera", "remoto", "control", "cerradura", "llave magnética", "portero eléctrico", "intercomunicador")):
        return CategoriaIncidencia.PORTON_ACCESO
    if any(k in m for k in ("basura", "olor", "palier sucio", "limpieza", "residuo", "suciedad", "mugre")):
        return CategoriaIncidencia.LIMPIEZA_AREAS_COMUNES
    if any(k in m for k in ("seguridad", "camara", "cámaras", "alarma", "robo", "intruso", "sospechoso")):
        return CategoriaIncidencia.SEGURIDAD
    if intent in ("EXPENSAS_DATOS_PAGO", "PAGO_REALIZADO", "CONSULTA_MUDANZA") or "expensas" in m or "cbu" in m:
        return CategoriaIncidencia.ADMINISTRACION_CONSULTA
        
    return CategoriaIncidencia.OTRO


async def generate_expediente_code(db: AsyncSession) -> str:
    """Genera un código correlativo único para un nuevo expediente (ej. EXP-2026-0001)."""
    current_year = datetime.utcnow().year
    count_q = select(func.count()).select_from(ExpedienteIncidenciaModel)
    res = await db.execute(count_q)
    total_count = res.scalar() or 0
    return f"EXP-{current_year}-{(total_count + 1):04d}"


async def process_and_consolidate_ticket(
    db: AsyncSession,
    contacto: ContactoModel,
    message: str,
    intent: Optional[str] = None,
    is_emergency: bool = False,
    created_off_hours: bool = True,
    consorcio_id: Optional[str] = None,
    consorcio_nombre: Optional[str] = None,
    consolidation_hours: int = 24,
) -> Dict[str, Any]:
    """
    Servicio central de consolidación inteligente de tickets y expedientes.
    1. Consolida mensajes en el ticket activo del vecino en una ventana de 24hs (elimina informes duplicados).
    2. Enriquece la ficha del contacto si detecta unidad funcional o consorcio en el texto mediante LLM 3B.
    3. Si es un reclamo edilicio con consorcio conocido, agrupa bajo un Expediente de Incidencia común.
    """
    all_consorcios_res = await db.execute(select(ConsorcioModel).where(ConsorcioModel.activo == True))
    all_consorcios = all_consorcios_res.scalars().all()
    consorcios_nombres = [c.nombre for c in all_consorcios]

    sem_res = semantic_extractor.extract(message, consorcios_nombres)

    if sem_res.es_emergencia:
        is_emergency = True

    unit_clue = sem_res.unidad_funcional or extract_unit_clue(message)
    if unit_clue and not contacto.unidad_funcional:
        contacto.unidad_funcional = unit_clue
        logger.info(f"[TICKET_SERVICE] Unidad funcional detectada por semántica y guardada para {contacto.id}: {unit_clue}")

    if not consorcio_id:
        if sem_res.consorcio_mencionado:
            matched = next((c for c in all_consorcios if c.nombre == sem_res.consorcio_mencionado), None)
        else:
            matched = extract_consorcio_clue(message, all_consorcios)

        if matched:
            consorcio_id = matched.id
            consorcio_nombre = matched.nombre
            if not contacto.consorcio_id:
                contacto.consorcio_id = matched.id
                logger.info(f"[TICKET_SERVICE] Consorcio detectado y asociado a contacto {contacto.id}: {matched.nombre}")

    cutoff = datetime.utcnow() - timedelta(hours=consolidation_hours)
    recent_q = (
        select(TicketConsultaModel)
        .where(
            TicketConsultaModel.contacto_id == contacto.id,
            TicketConsultaModel.estado.in_([
                EstadoTicket.NUEVO,
                EstadoTicket.ESPERANDO_RESPUESTA,
            ]),
            TicketConsultaModel.creado_el >= cutoff,
        )
        .order_by(TicketConsultaModel.creado_el.desc())
    )
    recent_res = await db.execute(recent_q)
    existing_ticket = recent_res.scalars().first()

    if existing_ticket:
        timestamp = datetime.utcnow().strftime("%H:%M")
        existing_ticket.descripcion = f"{existing_ticket.descripcion}\n[{timestamp}] - {message}"
        
        was_emergency = existing_ticket.prioridad == PrioridadTicket.CRITICA
        if is_emergency:
            existing_ticket.prioridad = PrioridadTicket.CRITICA
            existing_ticket.intencion = "EMERGENCIA"

        if consorcio_id and (not existing_ticket.consorcio_id or existing_ticket.estado == EstadoTicket.ESPERANDO_RESPUESTA):
            existing_ticket.consorcio_id = consorcio_id
            existing_ticket.estado = EstadoTicket.NUEVO

        await db.commit()
        await db.refresh(existing_ticket)

        logger.info(f"[TICKET_SERVICE] Mensaje consolidado en ticket existente #{existing_ticket.id}")
        return {
            "ticket": existing_ticket,
            "id": existing_ticket.id,
            "intencion": existing_ticket.intencion,
            "prioridad": existing_ticket.prioridad.value,
            "estado": existing_ticket.estado.value,
            "accion": "CONSOLIDADO_EN_TICKET_EXISTENTE",
            "is_escalation": (is_emergency and not was_emergency),
            "expediente_id": existing_ticket.expediente_id,
        }

    ticket_id = f"tick-{str(uuid.uuid4())[:8]}"
    if is_emergency:
        prioridad = PrioridadTicket.CRITICA
    elif intent == "CONSULTA_ATRIBUTO_RESTRINGIDO":
        prioridad = PrioridadTicket.ALTA
    else:
        prioridad = PrioridadTicket.NORMAL

    if not consorcio_id and not is_emergency:
        estado = EstadoTicket.ESPERANDO_RESPUESTA
    else:
        estado = EstadoTicket.NUEVO

    ticket = TicketConsultaModel(
        id=ticket_id,
        contacto_id=contacto.id,
        consorcio_id=consorcio_id,
        intencion=intent or "CONSULTA_GENERAL",
        descripcion=message,
        prioridad=prioridad,
        estado=estado,
        creado_fuera_de_horario=created_off_hours,
    )

    expediente_asignado = None
    is_technical_issue = is_emergency or intent in ("FUERA_HORARIO_TICKET", "RECLAMO", "EMERGENCIA")
    
    if consorcio_id and is_technical_issue:
        if sem_res.categoria and sem_res.categoria != "OTRO":
            try:
                categoria = CategoriaIncidencia(sem_res.categoria)
            except ValueError:
                categoria = classify_incident_category(message, intent)
        else:
            categoria = classify_incident_category(message, intent)
        
        cutoff_exp = datetime.utcnow() - timedelta(hours=48)
        exp_q = (
            select(ExpedienteIncidenciaModel)
            .where(
                ExpedienteIncidenciaModel.consorcio_id == consorcio_id,
                ExpedienteIncidenciaModel.categoria == categoria,
                ExpedienteIncidenciaModel.estado.in_([
                    EstadoExpediente.ABIERTO,
                    EstadoExpediente.EN_CURSO,
                    EstadoExpediente.EN_ESPERA_PROVEEDOR,
                ]),
                ExpedienteIncidenciaModel.creado_el >= cutoff_exp,
            )
            .order_by(ExpedienteIncidenciaModel.creado_el.desc())
        )
        exp_res = await db.execute(exp_q)
        existing_exp = exp_res.scalars().first()

        if existing_exp:
            ticket.expediente_id = existing_exp.id
            uf_label = contacto.unidad_funcional or "S/UF"
            existing_exp.descripcion_consolidada += f"\n- [{datetime.utcnow().strftime('%H:%M')}] Reporte UF {uf_label} ({contacto.nombre_completo or 'Vecino'}): {message}"
            if is_emergency:
                existing_exp.prioridad = PrioridadTicket.CRITICA
            expediente_asignado = existing_exp
            logger.info(f"[TICKET_SERVICE] Reclamo asignado a expediente activo #{existing_exp.codigo}")
        else:
            codigo = await generate_expediente_code(db)
            titulo = f"Incidencia en {categoria.value.replace('_', ' ').title()} - {consorcio_nombre or 'Consorcio'}"
            uf_label = contacto.unidad_funcional or "S/UF"
            nuevo_exp = ExpedienteIncidenciaModel(
                id=f"exp-{str(uuid.uuid4())[:8]}",
                codigo=codigo,
                consorcio_id=consorcio_id,
                titulo=titulo,
                categoria=categoria,
                prioridad=prioridad,
                estado=EstadoExpediente.ABIERTO,
                descripcion_consolidada=f"Apertura por UF {uf_label} ({contacto.nombre_completo or 'Vecino'}): {message}",
            )
            db.add(nuevo_exp)
            await db.flush()
            ticket.expediente_id = nuevo_exp.id
            expediente_asignado = nuevo_exp
            logger.info(f"[TICKET_SERVICE] Nuevo expediente abierto #{codigo}: {titulo}")

    db.add(ticket)
    await db.commit()
    await db.refresh(ticket)

    logger.info(f"[TICKET_SERVICE] Nuevo ticket creado: {ticket.id} [{prioridad.value}]")
    return {
        "ticket": ticket,
        "id": ticket.id,
        "intencion": ticket.intencion,
        "prioridad": ticket.prioridad.value,
        "estado": ticket.estado.value,
        "accion": "NUEVO_TICKET_CREADO",
        "is_escalation": False,
        "expediente_id": ticket.expediente_id,
        "expediente_codigo": expediente_asignado.codigo if expediente_asignado else None,
    }
