from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List, Optional
from infrastructure.database import get_db
from infrastructure.models import ContactoModel
from domain.schemas import ContactoCreate, ContactoResponse

router = APIRouter()


@router.get("/", response_model=List[ContactoResponse])
async def list_contactos(
    consorcio_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Lista todos los contactos registrados con filtros opcionales."""
    query = (
        select(ContactoModel)
        .options(selectinload(ContactoModel.consorcio))
        .order_by(ContactoModel.creado_el.desc())
    )
    if consorcio_id:
        query = query.where(ContactoModel.consorcio_id == consorcio_id)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{contacto_id}", response_model=ContactoResponse)
async def get_contacto(contacto_id: str, db: AsyncSession = Depends(get_db)):
    """Obtiene los datos de un contacto específico."""
    query = (
        select(ContactoModel)
        .options(selectinload(ContactoModel.consorcio))
        .where(ContactoModel.id == contacto_id)
    )
    result = await db.execute(query)
    contacto = result.scalar_one_or_none()
    if not contacto:
        raise HTTPException(status_code=404, detail="Contacto no encontrado")
    return contacto


@router.post("/", response_model=ContactoResponse, status_code=201)
async def create_contacto(data: ContactoCreate, db: AsyncSession = Depends(get_db)):
    """Crea un nuevo contacto de vecino."""
    contacto = ContactoModel(**data.model_dump())
    db.add(contacto)
    await db.commit()
    await db.refresh(contacto)
    return contacto
