from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List, Optional
from infrastructure.database import get_db
from infrastructure.models import TicketConsultaModel, UsuarioModel
from domain.schemas import TicketCreate, TicketUpdate, TicketResponse, EstadoTicket
from api.deps import get_current_user

router = APIRouter()


@router.get("/", response_model=List[TicketResponse])
async def list_tickets(
    estado: Optional[EstadoTicket] = None,
    consorcio_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_user),
):
    """Lista todos los tickets con filtros opcionales por estado o consorcio."""
    query = (
        select(TicketConsultaModel)
        .options(
            selectinload(TicketConsultaModel.contacto),
            selectinload(TicketConsultaModel.consorcio),
        )
    )
    if estado:
        query = query.where(TicketConsultaModel.estado == estado)
    if consorcio_id:
        query = query.where(TicketConsultaModel.consorcio_id == consorcio_id)
    
    result = await db.execute(query.order_by(TicketConsultaModel.creado_el.desc()))
    return result.scalars().all()


@router.post("/", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
async def create_ticket(
    data: TicketCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_user),
):
    """Registra una nueva consulta o reclamo de vecino."""
    ticket = TicketConsultaModel(**data.model_dump())
    db.add(ticket)
    await db.commit()
    await db.refresh(ticket)
    return ticket


@router.get("/{ticket_id}", response_model=TicketResponse)
async def get_ticket(
    ticket_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_user),
):
    """Obtiene el detalle de un ticket específico."""
    query = (
        select(TicketConsultaModel)
        .options(
            selectinload(TicketConsultaModel.contacto),
            selectinload(TicketConsultaModel.consorcio),
        )
        .where(TicketConsultaModel.id == ticket_id)
    )
    result = await db.execute(query)
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    return ticket


@router.patch("/{ticket_id}", response_model=TicketResponse)
async def update_ticket(
    ticket_id: str,
    data: TicketUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_user),
):
    """Actualiza el estado, prioridad o descripción de un ticket."""
    query = (
        select(TicketConsultaModel)
        .options(
            selectinload(TicketConsultaModel.contacto),
            selectinload(TicketConsultaModel.consorcio),
        )
        .where(TicketConsultaModel.id == ticket_id)
    )
    result = await db.execute(query)
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")

    update_dict = data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(ticket, key, value)

    await db.commit()
    await db.refresh(ticket)
    return ticket
