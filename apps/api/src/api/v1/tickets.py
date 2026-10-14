from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional
from infrastructure.database import get_db
from infrastructure.models import TicketConsultaModel
from domain.schemas import TicketCreate, TicketResponse, EstadoTicket

router = APIRouter()


@router.get("/", response_model=List[TicketResponse])
async def list_tickets(
    estado: Optional[EstadoTicket] = None,
    consorcio_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Lista todos los tickets con filtros opcionales por estado o consorcio."""
    query = select(TicketConsultaModel)
    if estado:
        query = query.where(TicketConsultaModel.estado == estado)
    if consorcio_id:
        query = query.where(TicketConsultaModel.consorcio_id == consorcio_id)
    
    result = await db.execute(query.order_by(TicketConsultaModel.creado_el.desc()))
    return result.scalars().all()


@router.post("/", response_model=TicketResponse, status_code=201)
async def create_ticket(data: TicketCreate, db: AsyncSession = Depends(get_db)):
    """Registra una nueva consulta o reclamo de vecino."""
    ticket = TicketConsultaModel(**data.model_dump())
    db.add(ticket)
    await db.commit()
    await db.refresh(ticket)
    return ticket
