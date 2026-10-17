import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from infrastructure.database import get_db
from infrastructure.models import ConsorcioModel, ConsorcioAtributoDinamicoModel, UsuarioModel
from domain.schemas import (
    ConsorcioCreate,
    ConsorcioUpdate,
    ConsorcioResponse,
    ConsorcioAtributoCreate,
    ConsorcioAtributoUpdate,
    ConsorcioAtributoResponse,
)
from api.deps import get_current_user

router = APIRouter()


@router.get("", response_model=List[ConsorcioResponse])
@router.get("/", response_model=List[ConsorcioResponse], include_in_schema=False)
async def list_consorcios(db: AsyncSession = Depends(get_db)):
    """Lista todos los consorcios administrados por la Dra. Ivana Seliz."""
    result = await db.execute(select(ConsorcioModel).where(ConsorcioModel.activo == True).order_by(ConsorcioModel.nombre))
    return result.scalars().all()


@router.post("", response_model=ConsorcioResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=ConsorcioResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
async def create_consorcio(
    data: ConsorcioCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_user),
):
    """Crea un nuevo consorcio en el sistema."""
    cid = f"cons-{str(uuid.uuid4())[:8]}"
    consorcio = ConsorcioModel(id=cid, **data.model_dump())
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
        raise HTTPException(status_code=404, detail="Consorcio no encontrado.")
    return consorcio


@router.put("/{consorcio_id}", response_model=ConsorcioResponse)
async def update_consorcio(
    consorcio_id: str,
    data: ConsorcioUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_user),
):
    """Actualiza datos operativos y bancarios de un consorcio."""
    result = await db.execute(select(ConsorcioModel).where(ConsorcioModel.id == consorcio_id))
    consorcio = result.scalar_one_or_none()
    if not consorcio:
        raise HTTPException(status_code=404, detail="Consorcio no encontrado.")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(consorcio, field, value)

    await db.commit()
    await db.refresh(consorcio)
    return consorcio


@router.delete("/{consorcio_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_consorcio(
    consorcio_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_user),
):
    """Desactiva un consorcio (soft delete)."""
    result = await db.execute(select(ConsorcioModel).where(ConsorcioModel.id == consorcio_id))
    consorcio = result.scalar_one_or_none()
    if not consorcio:
        raise HTTPException(status_code=404, detail="Consorcio no encontrado.")

    consorcio.activo = False
    await db.commit()
    return None


@router.get("/{consorcio_id}/atributos", response_model=List[ConsorcioAtributoResponse])
async def list_atributos(
    consorcio_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_user),
):
    """Lista los atributos dinámicos configurados para un consorcio."""
    res = await db.execute(
        select(ConsorcioAtributoDinamicoModel)
        .where(ConsorcioAtributoDinamicoModel.consorcio_id == consorcio_id)
        .order_by(ConsorcioAtributoDinamicoModel.etiqueta_visible)
    )
    return res.scalars().all()


@router.post("/{consorcio_id}/atributos", response_model=ConsorcioAtributoResponse, status_code=status.HTTP_201_CREATED)
async def create_atributo(
    consorcio_id: str,
    data: ConsorcioAtributoCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_user),
):
    """Agrega un nuevo atributo dinámico clave-valor a un consorcio."""
    c_check = await db.execute(select(ConsorcioModel).where(ConsorcioModel.id == consorcio_id))
    if not c_check.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Consorcio no encontrado.")

    attr = ConsorcioAtributoDinamicoModel(
        id=f"attr-{str(uuid.uuid4())[:8]}",
        consorcio_id=consorcio_id,
        clave=data.clave.strip().lower().replace(" ", "_"),
        etiqueta_visible=data.etiqueta_visible.strip(),
        valor=data.valor.strip(),
        es_publico_vecinos=data.es_publico_vecinos,
    )
    db.add(attr)
    await db.commit()
    await db.refresh(attr)
    return attr


@router.put("/{consorcio_id}/atributos/{attr_id}", response_model=ConsorcioAtributoResponse)
async def update_atributo(
    consorcio_id: str,
    attr_id: str,
    data: ConsorcioAtributoUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_user),
):
    """Modifica el valor o visibilidad de un atributo dinámico existente."""
    res = await db.execute(
        select(ConsorcioAtributoDinamicoModel).where(
            ConsorcioAtributoDinamicoModel.id == attr_id,
            ConsorcioAtributoDinamicoModel.consorcio_id == consorcio_id,
        )
    )
    attr = res.scalar_one_or_none()
    if not attr:
        raise HTTPException(status_code=404, detail="Atributo no encontrado.")

    for field, value in data.model_dump(exclude_unset=True).items():
        if field == "clave" and value:
            value = value.strip().lower().replace(" ", "_")
        setattr(attr, field, value)

    await db.commit()
    await db.refresh(attr)
    return attr


@router.delete("/{consorcio_id}/atributos/{attr_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_atributo(
    consorcio_id: str,
    attr_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_user),
):
    """Elimina un atributo dinámico de un consorcio."""
    res = await db.execute(
        select(ConsorcioAtributoDinamicoModel).where(
            ConsorcioAtributoDinamicoModel.id == attr_id,
            ConsorcioAtributoDinamicoModel.consorcio_id == consorcio_id,
        )
    )
    attr = res.scalar_one_or_none()
    if not attr:
        raise HTTPException(status_code=404, detail="Atributo no encontrado.")

    await db.delete(attr)
    await db.commit()
    return None
