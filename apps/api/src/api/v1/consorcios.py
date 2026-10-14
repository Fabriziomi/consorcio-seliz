from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from infrastructure.database import get_db
from infrastructure.models import ConsorcioModel
from domain.schemas import ConsorcioCreate, ConsorcioResponse

router = APIRouter()


@router.get("/", response_model=List[ConsorcioResponse])
async def list_consorcios(db: AsyncSession = Depends(get_db)):
    """Lista todos los consorcios administrados por la Dra. Ivana Seliz."""
    result = await db.execute(select(ConsorcioModel).where(ConsorcioModel.activo == True))
    return result.scalars().all()


@router.post("/", response_model=ConsorcioResponse, status_code=201)
async def create_consorcio(data: ConsorcioCreate, db: AsyncSession = Depends(get_db)):
    """Crea un nuevo consorcio en el sistema."""
    consorcio = ConsorcioModel(**data.model_dump())
    db.add(consorcio)
    await db.commit()
    await db.refresh(consorcio)
    return consorcio


@router.get("/{consorcio_id}", response_model=ConsorcioResponse)
async def get_consorcio(consorcio_id: str, db: AsyncSession = Depends(get_db)):
    """Obtiene el detalle y datos operativos de un consorcio específico."""
    result = await db.execute(select(ConsorcioModel).where(ConsorcioModel.id == consorcio_id))
    consorcio = result.scalar_one_or_none()
    if not consorcio:
        raise HTTPException(status_code=404, detail="Consorcio no encontrado")
    return consorcio
