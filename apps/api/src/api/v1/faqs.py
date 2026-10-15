import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from infrastructure.database import get_db
from infrastructure.models import FaqAprobadaModel, UsuarioModel
from domain.schemas import FaqCreate, FaqUpdate, FaqResponse
from api.deps import get_current_user

router = APIRouter()


@router.get("", response_model=List[FaqResponse])
async def list_faqs(
    consorcio_id: Optional[str] = None,
    activo: Optional[bool] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_user),
):
    """Lista las preguntas frecuentes con filtros por consorcio, estado y búsqueda de texto."""
    stmt = select(FaqAprobadaModel).order_by(FaqAprobadaModel.pregunta)

    if consorcio_id is not None:
        stmt = stmt.where(FaqAprobadaModel.consorcio_id == consorcio_id)
    if activo is not None:
        stmt = stmt.where(FaqAprobadaModel.activo == activo)
    if search:
        term = f"%{search.strip().lower()}%"
        stmt = stmt.where(FaqAprobadaModel.pregunta.ilike(term))

    res = await db.execute(stmt)
    return res.scalars().all()


@router.post("", response_model=FaqResponse, status_code=status.HTTP_201_CREATED)
async def create_faq(
    data: FaqCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_user),
):
    """Crea una nueva FAQ homologada en la base de conocimiento."""
    faq = FaqAprobadaModel(
        id=f"faq-{str(uuid.uuid4())[:8]}",
        consorcio_id=data.consorcio_id,
        pregunta=data.pregunta.strip(),
        respuesta_oficial=data.respuesta_oficial.strip(),
        activo=data.activo,
    )
    db.add(faq)
    await db.commit()
    await db.refresh(faq)
    return faq


@router.get("/{faq_id}", response_model=FaqResponse)
async def get_faq(
    faq_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_user),
):
    """Obtiene el detalle de una FAQ específica."""
    res = await db.execute(select(FaqAprobadaModel).where(FaqAprobadaModel.id == faq_id))
    faq = res.scalar_one_or_none()
    if not faq:
        raise HTTPException(status_code=404, detail="FAQ no encontrada.")
    return faq


@router.put("/{faq_id}", response_model=FaqResponse)
async def update_faq(
    faq_id: str,
    data: FaqUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_user),
):
    """Actualiza una pregunta frecuente existente."""
    res = await db.execute(select(FaqAprobadaModel).where(FaqAprobadaModel.id == faq_id))
    faq = res.scalar_one_or_none()
    if not faq:
        raise HTTPException(status_code=404, detail="FAQ no encontrada.")

    if data.pregunta is not None:
        faq.pregunta = data.pregunta.strip()
    if data.respuesta_oficial is not None:
        faq.respuesta_oficial = data.respuesta_oficial.strip()
    if data.consorcio_id is not None:
        faq.consorcio_id = data.consorcio_id
    if data.activo is not None:
        faq.activo = data.activo

    await db.commit()
    await db.refresh(faq)
    return faq


@router.patch("/{faq_id}/toggle", response_model=FaqResponse)
async def toggle_faq_status(
    faq_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_user),
):
    """Alterna el estado activo/inactivo de una FAQ."""
    res = await db.execute(select(FaqAprobadaModel).where(FaqAprobadaModel.id == faq_id))
    faq = res.scalar_one_or_none()
    if not faq:
        raise HTTPException(status_code=404, detail="FAQ no encontrada.")

    faq.activo = not faq.activo
    await db.commit()
    await db.refresh(faq)
    return faq


@router.delete("/{faq_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_faq(
    faq_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_user),
):
    """Elimina una FAQ de la base de conocimiento."""
    res = await db.execute(select(FaqAprobadaModel).where(FaqAprobadaModel.id == faq_id))
    faq = res.scalar_one_or_none()
    if not faq:
        raise HTTPException(status_code=404, detail="FAQ no encontrada.")

    await db.delete(faq)
    await db.commit()
    return None
