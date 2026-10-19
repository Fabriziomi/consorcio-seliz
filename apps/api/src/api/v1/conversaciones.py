import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import or_, desc, func

from core.logging import logger
from infrastructure.database import get_db
from infrastructure.models import (
    ConversacionModel,
    MensajeModel,
    ContactoModel,
    ConsorcioModel,
    UsuarioModel,
    EtiquetaModel,
)
from domain.schemas import (
    EstadoConversacion,
    TipoMensaje,
    EnviadoPor,
    ConversacionResponse,
    ConversacionDetailResponse,
    ConversacionCreate,
    ConversacionUpdate,
    MensajeCreate,
    MensajeResponse,
    EtiquetaCreate,
    EtiquetaResponse,
)
from infrastructure.evolution_client import evolution_client
from infrastructure.takeover_service import takeover_service
from core.websocket_manager import ws_manager
from api.deps import get_current_user

router = APIRouter()


def _to_conversacion_response(c: ConversacionModel) -> ConversacionResponse:
    return ConversacionResponse(
        id=c.id,
        contacto_id=c.contacto_id,
        consorcio_id=c.consorcio_id,
        estado=c.estado,
        bot_activo=c.bot_activo,
        agente_id=c.agente_id,
        etiquetas=c.etiquetas or [],
        ultimo_mensaje_el=c.ultimo_mensaje_el,
        creado_el=c.creado_el,
        contacto_nombre=c.contacto.nombre_completo if c.contacto else None,
        contacto_telefono=c.contacto.telefono_wa if c.contacto else None,
        contacto_unidad=c.contacto.unidad_funcional if c.contacto else None,
        contacto_foto_url=c.contacto.foto_url if c.contacto else None,
        consorcio_nombre=c.consorcio.nombre if c.consorcio else None,
        agente_nombre=c.agente.nombre_completo if c.agente else None,
        ultimo_mensaje_texto=c.ultimo_mensaje_texto,
        mensajes_no_leidos_count=c.mensajes_no_leidos_count,
    )


def _to_mensaje_response(m: MensajeModel) -> MensajeResponse:
    return MensajeResponse(
        id=m.id,
        conversacion_id=m.conversacion_id,
        tipo=m.tipo,
        contenido=m.contenido,
        privado=m.privado,
        enviado_por=m.enviado_por,
        agente_id=m.agente_id,
        media_url=m.media_url,
        media_tipo=m.media_tipo,
        leido=m.leido,
        whatsapp_message_id=m.whatsapp_message_id,
        creado_el=m.creado_el,
        agente_nombre=m.agente.nombre_completo if m.agente else None,
    )


@router.get("/labels/all", response_model=List[EtiquetaResponse])
async def list_labels(
    db: AsyncSession = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_user),
):
    """Obtiene el catálogo de todas las etiquetas disponibles."""
    res = await db.execute(select(EtiquetaModel).order_by(EtiquetaModel.titulo))
    return res.scalars().all()


@router.post("/labels/create", response_model=EtiquetaResponse, status_code=status.HTTP_201_CREATED)
async def create_label(
    data: EtiquetaCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_user),
):
    """Crea una nueva etiqueta en el sistema."""
    exists = await db.execute(select(EtiquetaModel).where(EtiquetaModel.titulo == data.titulo.strip().upper()))
    if exists.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Ya existe una etiqueta con este título.")

    etiqueta = EtiquetaModel(
        id=f"lbl-{str(uuid.uuid4())[:8]}",
        titulo=data.titulo.strip().upper(),
        color=data.color or "#475569",
        descripcion=data.descripcion,
    )
    db.add(etiqueta)
    await db.commit()
    await db.refresh(etiqueta)
    return etiqueta


@router.get("", response_model=List[ConversacionResponse])
async def list_conversaciones(
    estado: Optional[EstadoConversacion] = None,
    consorcio_id: Optional[str] = None,
    agente_id: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_user),
):
    """
    Lista conversaciones con filtros por estado, consorcio, operador asignado o búsqueda de texto.
    Ordenadas cronológicamente por último mensaje descendente.
    """
    stmt = (
        select(ConversacionModel)
        .options(
            selectinload(ConversacionModel.contacto),
            selectinload(ConversacionModel.consorcio),
            selectinload(ConversacionModel.agente),
            selectinload(ConversacionModel.mensajes),
        )
        .order_by(desc(ConversacionModel.ultimo_mensaje_el))
    )

    if estado:
        stmt = stmt.where(ConversacionModel.estado == estado)
    if consorcio_id:
        stmt = stmt.where(ConversacionModel.consorcio_id == consorcio_id)
    if agente_id:
        stmt = stmt.where(ConversacionModel.agente_id == agente_id)

    if search:
        search_term = f"%{search.strip().lower()}%"
        stmt = stmt.join(ConversacionModel.contacto).where(
            or_(
                func.lower(ContactoModel.nombre_completo).like(search_term),
                func.lower(ContactoModel.telefono_wa).like(search_term),
                func.lower(ContactoModel.unidad_funcional).like(search_term),
            )
        )

    stmt = stmt.offset(skip).limit(limit)
    res = await db.execute(stmt)
    conversaciones = res.scalars().all()

    return [_to_conversacion_response(c) for c in conversaciones]


@router.post("", response_model=ConversacionResponse, status_code=status.HTTP_201_CREATED)
async def create_conversacion(
    data: ConversacionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_user),
):
    """Crea o retorna la conversación activa para un contacto."""
    c_res = await db.execute(select(ContactoModel).where(ContactoModel.id == data.contacto_id))
    contacto = c_res.scalar_one_or_none()
    if not contacto:
        raise HTTPException(status_code=404, detail="Contacto no encontrado.")

    existing_res = await db.execute(
        select(ConversacionModel)
        .options(
            selectinload(ConversacionModel.contacto),
            selectinload(ConversacionModel.consorcio),
            selectinload(ConversacionModel.agente),
            selectinload(ConversacionModel.mensajes),
        )
        .where(ConversacionModel.contacto_id == data.contacto_id)
    )
    existing = existing_res.scalar_one_or_none()
    if existing:
        if existing.estado == EstadoConversacion.RESOLVED:
            existing.estado = EstadoConversacion.OPEN
            await db.commit()
            await db.refresh(existing)
        return _to_conversacion_response(existing)

    consorcio_id = data.consorcio_id or contacto.consorcio_id
    conv = ConversacionModel(
        id=f"conv-{str(uuid.uuid4())[:8]}",
        contacto_id=data.contacto_id,
        consorcio_id=consorcio_id,
        estado=EstadoConversacion.OPEN,
        bot_activo=True,
        etiquetas=data.etiquetas or [],
    )
    db.add(conv)
    await db.commit()

    reload_res = await db.execute(
        select(ConversacionModel)
        .options(
            selectinload(ConversacionModel.contacto),
            selectinload(ConversacionModel.consorcio),
            selectinload(ConversacionModel.agente),
            selectinload(ConversacionModel.mensajes),
        )
        .where(ConversacionModel.id == conv.id)
    )
    return _to_conversacion_response(reload_res.scalar_one())


@router.get("/{conv_id}", response_model=ConversacionDetailResponse)
async def get_conversacion(
    conv_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_user),
):
    """Obtiene el detalle completo de una conversación con todos sus mensajes cronológicos."""
    res = await db.execute(
        select(ConversacionModel)
        .options(
            selectinload(ConversacionModel.contacto),
            selectinload(ConversacionModel.consorcio),
            selectinload(ConversacionModel.agente),
            selectinload(ConversacionModel.mensajes).selectinload(MensajeModel.agente),
        )
        .where(ConversacionModel.id == conv_id)
    )
    conv = res.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversación no encontrada.")

    detail = _to_conversacion_response(conv)
    mensajes_resp = [_to_mensaje_response(m) for m in conv.mensajes]

    return ConversacionDetailResponse(
        **detail.model_dump(),
        mensajes=mensajes_resp,
    )


@router.get("/{conv_id}/messages", response_model=List[MensajeResponse])
async def list_messages(
    conv_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_user),
):
    """Lista los mensajes de una conversación con paginación."""
    res = await db.execute(
        select(MensajeModel)
        .options(selectinload(MensajeModel.agente))
        .where(MensajeModel.conversacion_id == conv_id)
        .order_by(MensajeModel.creado_el.asc())
        .offset(skip)
        .limit(limit)
    )
    mensajes = res.scalars().all()
    return [_to_mensaje_response(m) for m in mensajes]


@router.post("/{conv_id}/messages", response_model=MensajeResponse, status_code=status.HTTP_201_CREATED)
async def send_message(
    conv_id: str,
    data: MensajeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_user),
):
    """
    Envía un mensaje a la conversación.
    - Si es público (privado=False):
        1. Despacha por WhatsApp vía Evolution API.
        2. Activa Takeover Humano (12 hs TTL) para silenciar el bot.
        3. Pone bot_activo=False en la conversación.
    - Si es privado (privado=True):
        Se almacena como nota interna visible únicamente en el CRM.
    """
    conv_res = await db.execute(
        select(ConversacionModel)
        .options(selectinload(ConversacionModel.contacto))
        .where(ConversacionModel.id == conv_id)
    )
    conv = conv_res.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversación no encontrada.")

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    msg_id = f"msg-{str(uuid.uuid4())[:8]}"

    if not data.privado:
        phone_wa = conv.contacto.telefono_wa if conv.contacto else None
        if not phone_wa:
            raise HTTPException(status_code=400, detail="La conversación no tiene un contacto telefónico válido.")

        clean_phone = phone_wa.replace("+", "").strip()
        remote_jid = f"{clean_phone}@s.whatsapp.net"

        sent = await evolution_client.send_text(remote_jid, data.contenido)
        if not sent:
            logger.warning(f"[CONVERSACIONES] No se pudo enviar mensaje por WhatsApp a {remote_jid}, se guardará en BD.")

        await takeover_service.set_takeover(remote_jid)
        conv.bot_activo = False

        nuevo_mensaje = MensajeModel(
            id=msg_id,
            conversacion_id=conv_id,
            tipo=TipoMensaje.OUTGOING,
            contenido=data.contenido,
            privado=False,
            enviado_por=EnviadoPor.AGENTE,
            agente_id=current_user.id,
            media_url=data.media_url,
            media_tipo=data.media_tipo,
            leido=True,
            creado_el=now,
        )
    else:
        nuevo_mensaje = MensajeModel(
            id=msg_id,
            conversacion_id=conv_id,
            tipo=TipoMensaje.ACTIVITY,
            contenido=data.contenido,
            privado=True,
            enviado_por=EnviadoPor.AGENTE,
            agente_id=current_user.id,
            media_url=data.media_url,
            media_tipo=data.media_tipo,
            leido=True,
            creado_el=now,
        )

    conv.ultimo_mensaje_el = now
    db.add(nuevo_mensaje)
    await db.commit()

    reload_res = await db.execute(
        select(MensajeModel)
        .options(selectinload(MensajeModel.agente))
        .where(MensajeModel.id == msg_id)
    )
    msg_response = _to_mensaje_response(reload_res.scalar_one())
    try:
        await ws_manager.broadcast("new_message", {
            "conversacion_id": conv_id,
            "mensaje": msg_response.model_dump(mode="json"),
        })
    except Exception as e:
        logger.warning(f"[WS] Broadcast error in send_message: {e}")
    return msg_response


@router.patch("/{conv_id}/status", response_model=ConversacionResponse)
async def update_status(
    conv_id: str,
    nuevo_estado: EstadoConversacion = Query(..., description="Nuevo estado: open, resolved, pending"),
    db: AsyncSession = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_user),
):
    """Cambia el estado de una conversación y reactiva el bot si se resuelve."""
    res = await db.execute(
        select(ConversacionModel)
        .options(
            selectinload(ConversacionModel.contacto),
            selectinload(ConversacionModel.consorcio),
            selectinload(ConversacionModel.agente),
            selectinload(ConversacionModel.mensajes),
        )
        .where(ConversacionModel.id == conv_id)
    )
    conv = res.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversación no encontrada.")

    conv.estado = nuevo_estado
    if nuevo_estado == EstadoConversacion.RESOLVED:
        conv.bot_activo = True
        if conv.contacto and conv.contacto.telefono_wa:
            clean_phone = conv.contacto.telefono_wa.replace("+", "").strip()
            await takeover_service.release_takeover(f"{clean_phone}@s.whatsapp.net")

    await db.commit()
    await db.refresh(conv)
    status_resp = _to_conversacion_response(conv)
    try:
        await ws_manager.broadcast("status_changed", {
            "conversacion_id": conv_id,
            "estado": nuevo_estado.value if hasattr(nuevo_estado, "value") else str(nuevo_estado),
        })
    except Exception as e:
        logger.warning(f"[WS] Broadcast error in update_status: {e}")
    return status_resp


@router.patch("/{conv_id}/assign", response_model=ConversacionResponse)
async def assign_agent(
    conv_id: str,
    agente_id: Optional[str] = Query(None, description="ID del usuario operador a asignar o null para desasignar"),
    db: AsyncSession = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_user),
):
    """Asigna la conversación a un operador específico."""
    res = await db.execute(
        select(ConversacionModel)
        .options(
            selectinload(ConversacionModel.contacto),
            selectinload(ConversacionModel.consorcio),
            selectinload(ConversacionModel.agente),
            selectinload(ConversacionModel.mensajes),
        )
        .where(ConversacionModel.id == conv_id)
    )
    conv = res.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversación no encontrada.")

    if agente_id:
        user_check = await db.execute(select(UsuarioModel).where(UsuarioModel.id == agente_id))
        if not user_check.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="El operador indicado no existe.")

    conv.agente_id = agente_id
    await db.commit()
    await db.refresh(conv)
    return _to_conversacion_response(conv)


@router.post("/{conv_id}/labels", response_model=ConversacionResponse)
async def update_labels(
    conv_id: str,
    labels: List[str],
    db: AsyncSession = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_user),
):
    """Reemplaza o asigna el conjunto de etiquetas de una conversación."""
    res = await db.execute(
        select(ConversacionModel)
        .options(
            selectinload(ConversacionModel.contacto),
            selectinload(ConversacionModel.consorcio),
            selectinload(ConversacionModel.agente),
            selectinload(ConversacionModel.mensajes),
        )
        .where(ConversacionModel.id == conv_id)
    )
    conv = res.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversación no encontrada.")

    conv.etiquetas = [lbl.strip().upper() for lbl in labels if lbl.strip()]
    await db.commit()
    await db.refresh(conv)
    label_resp = _to_conversacion_response(conv)
    try:
        await ws_manager.broadcast("labels_updated", {
            "conversacion_id": conv_id,
            "etiquetas": conv.etiquetas,
        })
    except Exception as e:
        logger.warning(f"[WS] Broadcast error in update_labels: {e}")
    return label_resp


@router.post("/{conv_id}/read")
async def mark_as_read(
    conv_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_user),
):
    """Marca todos los mensajes entrantes de una conversación como leídos."""
    res = await db.execute(
        select(MensajeModel)
        .where(MensajeModel.conversacion_id == conv_id, MensajeModel.leido == False)
    )
    unread = res.scalars().all()
    for m in unread:
        m.leido = True
    await db.commit()
    return {"status": "ok", "marked_read": len(unread)}
