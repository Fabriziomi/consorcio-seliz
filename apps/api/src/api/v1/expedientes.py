import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from core.logging import logger
from infrastructure.database import get_db
from infrastructure.models import ExpedienteIncidenciaModel, TicketConsultaModel, ContactoModel
from domain.schemas import (
    ExpedienteCreate,
    ExpedienteUpdate,
    ExpedienteResponse,
    TicketResponse,
    EstadoExpediente,
    CategoriaIncidencia,
)
from infrastructure.evolution_client import evolution_client
from services.ticket_service import generate_expediente_code

router = APIRouter()


class ExpedienteDetailResponse(ExpedienteResponse):
    tickets: List[TicketResponse] = []


class NotificarVecinosRequest(BaseModel):
    mensaje: str = Field(..., description="Texto del mensaje a despachar por WhatsApp a todos los vecinos vinculados al expediente.")


@router.get("/", response_model=List[ExpedienteResponse])
async def list_expedientes(
    estado: Optional[EstadoExpediente] = None,
    categoria: Optional[CategoriaIncidencia] = None,
    consorcio_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Lista los expedientes e incidencias edilicias con filtros opcionales."""
    query = (
        select(ExpedienteIncidenciaModel)
        .options(
            selectinload(ExpedienteIncidenciaModel.consorcio),
            selectinload(ExpedienteIncidenciaModel.tickets),
        )
    )
    if estado:
        query = query.where(ExpedienteIncidenciaModel.estado == estado)
    if categoria:
        query = query.where(ExpedienteIncidenciaModel.categoria == categoria)
    if consorcio_id:
        query = query.where(ExpedienteIncidenciaModel.consorcio_id == consorcio_id)

    res = await db.execute(query.order_by(ExpedienteIncidenciaModel.actualizado_el.desc()))
    return res.scalars().all()


@router.post("/", response_model=ExpedienteResponse, status_code=status.HTTP_201_CREATED)
async def create_expediente(
    data: ExpedienteCreate,
    db: AsyncSession = Depends(get_db),
):
    """Crea manualmente un nuevo expediente edilicio."""
    codigo = await generate_expediente_code(db)
    exp = ExpedienteIncidenciaModel(
        id=f"exp-{str(uuid.uuid4())[:8]}",
        codigo=codigo,
        **data.model_dump(),
    )
    db.add(exp)
    await db.commit()
    await db.refresh(exp)
    
    res = await db.execute(
        select(ExpedienteIncidenciaModel)
        .options(
            selectinload(ExpedienteIncidenciaModel.consorcio),
            selectinload(ExpedienteIncidenciaModel.tickets),
        )
        .where(ExpedienteIncidenciaModel.id == exp.id)
    )
    return res.scalar_one()


@router.get("/{expediente_id}", response_model=ExpedienteDetailResponse)
async def get_expediente(
    expediente_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Obtiene el detalle completo de un expediente con todos los reclamos asociados de vecinos."""
    query = (
        select(ExpedienteIncidenciaModel)
        .options(
            selectinload(ExpedienteIncidenciaModel.consorcio),
            selectinload(ExpedienteIncidenciaModel.tickets).selectinload(TicketConsultaModel.contacto),
            selectinload(ExpedienteIncidenciaModel.tickets).selectinload(TicketConsultaModel.consorcio),
        )
        .where(ExpedienteIncidenciaModel.id == expediente_id)
    )
    res = await db.execute(query)
    exp = res.scalar_one_or_none()
    if not exp:
        raise HTTPException(status_code=404, detail="Expediente no encontrado")
    return exp


@router.patch("/{expediente_id}", response_model=ExpedienteResponse)
async def update_expediente(
    expediente_id: str,
    data: ExpedienteUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Actualiza el estado, proveedor asignado o notas consolidadas de un expediente."""
    query = (
        select(ExpedienteIncidenciaModel)
        .options(
            selectinload(ExpedienteIncidenciaModel.consorcio),
            selectinload(ExpedienteIncidenciaModel.tickets),
        )
        .where(ExpedienteIncidenciaModel.id == expediente_id)
    )
    res = await db.execute(query)
    exp = res.scalar_one_or_none()
    if not exp:
        raise HTTPException(status_code=404, detail="Expediente no encontrado")

    update_dict = data.model_dump(exclude_unset=True)
    if "estado" in update_dict and update_dict["estado"] in (EstadoExpediente.RESUELTO, EstadoExpediente.CERRADO):
        exp.resuelto_el = datetime.utcnow()

    for k, v in update_dict.items():
        setattr(exp, k, v)

    exp.actualizado_el = datetime.utcnow()
    await db.commit()
    await db.refresh(exp)
    return exp


@router.post("/{expediente_id}/notificar-vecinos")
async def notificar_vecinos(
    expediente_id: str,
    req: NotificarVecinosRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Envía una notificación oficial por WhatsApp a todos los vecinos que reportaron sobre esta incidencia.
    Permite avisar avances, llegada de cuadrilla técnica o resolución definitiva del problema.
    """
    query = (
        select(ExpedienteIncidenciaModel)
        .options(
            selectinload(ExpedienteIncidenciaModel.tickets).selectinload(TicketConsultaModel.contacto),
        )
        .where(ExpedienteIncidenciaModel.id == expediente_id)
    )
    res = await db.execute(query)
    exp = res.scalar_one_or_none()
    if not exp:
        raise HTTPException(status_code=404, detail="Expediente no encontrado")

    telefonos = set()
    for t in exp.tickets:
        if t.contacto and t.contacto.telefono_wa:
            telefonos.add(t.contacto.telefono_wa)

    despachados = 0
    fallidos = 0
    for tel in telefonos:
        remote_jid = tel.replace("+", "").strip()
        if not remote_jid.endswith("@s.whatsapp.net"):
            remote_jid = f"{remote_jid}@s.whatsapp.net"
        try:
            ok = await evolution_client.send_text(remote_jid, req.mensaje)
            if ok:
                despachados += 1
            else:
                fallidos += 1
        except Exception as e:
            logger.error(f"[NOTIFICAR_VECINOS] Error al enviar WhatsApp a {remote_jid}: {e}")
            fallidos += 1

    logger.info(f"[NOTIFICAR_VECINOS] Notificación de expediente #{exp.codigo} enviada a {despachados} vecinos ({fallidos} fallidos).")
    return {
        "expediente_id": exp.id,
        "codigo": exp.codigo,
        "total_destinatarios": len(telefonos),
        "enviados_ok": despachados,
        "fallidos": fallidos,
    }
