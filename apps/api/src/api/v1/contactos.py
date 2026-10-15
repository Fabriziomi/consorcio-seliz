import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import or_, func

from infrastructure.database import get_db
from infrastructure.models import ContactoModel, UsuarioModel
from domain.schemas import ContactoCreate, ContactoUpdate, ContactoResponse
from api.deps import get_current_user

router = APIRouter()


@router.get("", response_model=List[ContactoResponse])
@router.get("/", response_model=List[ContactoResponse], include_in_schema=False)
async def list_contactos(
    consorcio_id: Optional[str] = None,
    rol: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """Lista todos los contactos registrados con filtros por consorcio, rol o búsqueda de texto."""
    query = (
        select(ContactoModel)
        .options(selectinload(ContactoModel.consorcio))
        .order_by(ContactoModel.nombre_completo.asc())
    )
    if consorcio_id:
        query = query.where(ContactoModel.consorcio_id == consorcio_id)
    if rol:
        query = query.where(ContactoModel.rol == rol)
    if search:
        term = f"%{search.strip().lower()}%"
        query = query.where(
            or_(
                func.lower(ContactoModel.nombre_completo).like(term),
                func.lower(ContactoModel.telefono_wa).like(term),
                func.lower(ContactoModel.unidad_funcional).like(term),
            )
        )

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("", response_model=ContactoResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=ContactoResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
async def create_contacto(
    data: ContactoCreate,
    db: AsyncSession = Depends(get_db),
):
    """Crea un nuevo contacto de vecino."""
    cid = f"cont-{str(uuid.uuid4())[:8]}"
    contacto = ContactoModel(id=cid, **data.model_dump())
    db.add(contacto)
    await db.commit()

    reload_query = (
        select(ContactoModel)
        .options(selectinload(ContactoModel.consorcio))
        .where(ContactoModel.id == cid)
    )
    reloaded = await db.execute(reload_query)
    return reloaded.scalar_one()


@router.get("/{contacto_id}", response_model=ContactoResponse)
async def get_contacto(
    contacto_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_user),
):
    """Obtiene los datos de un contacto específico."""
    query = (
        select(ContactoModel)
        .options(selectinload(ContactoModel.consorcio))
        .where(ContactoModel.id == contacto_id)
    )
    result = await db.execute(query)
    contacto = result.scalar_one_or_none()
    if not contacto:
        raise HTTPException(status_code=404, detail="Contacto no encontrado.")
    return contacto


@router.put("/{contacto_id}", response_model=ContactoResponse)
async def update_contacto(
    contacto_id: str,
    data: ContactoUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_user),
):
    """Actualiza datos de un contacto (nombre, consorcio, unidad funcional, rol)."""
    query = (
        select(ContactoModel)
        .options(selectinload(ContactoModel.consorcio))
        .where(ContactoModel.id == contacto_id)
    )
    result = await db.execute(query)
    contacto = result.scalar_one_or_none()
    if not contacto:
        raise HTTPException(status_code=404, detail="Contacto no encontrado.")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(contacto, field, value)

    await db.commit()
    await db.refresh(contacto)
    return contacto


@router.delete("/{contacto_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contacto(
    contacto_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_user),
):
    """Elimina un contacto del sistema."""
    result = await db.execute(select(ContactoModel).where(ContactoModel.id == contacto_id))
    contacto = result.scalar_one_or_none()
    if not contacto:
        raise HTTPException(status_code=404, detail="Contacto no encontrado.")

    await db.delete(contacto)
    await db.commit()
    return None
