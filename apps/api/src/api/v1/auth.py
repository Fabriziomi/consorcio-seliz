import uuid
from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from infrastructure.database import get_db
from infrastructure.models import UsuarioModel
from domain.schemas import (
    RolUsuario,
    UsuarioCreate,
    UsuarioUpdate,
    UsuarioResponse,
    LoginRequest,
    TokenResponse,
)
from core.security import hash_password, verify_password, create_access_token
from api.deps import get_current_user, require_roles

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Inicia sesión y genera token de acceso JWT para la administración."""
    result = await db.execute(select(UsuarioModel).where(UsuarioModel.email == data.email.lower().strip()))
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo electrónico o contraseña incorrectos.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="La cuenta de usuario se encuentra suspendida.",
        )

    user.ultimo_login = datetime.now(timezone.utc).replace(tzinfo=None)
    await db.commit()
    await db.refresh(user)

    token = create_access_token(
        data={"sub": user.id, "email": user.email, "rol": user.rol.value}
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=user,
    )


@router.get("/me", response_model=UsuarioResponse)
async def get_me(current_user: UsuarioModel = Depends(get_current_user)):
    """Obtiene el perfil del usuario autenticado actualmente."""
    return current_user


@router.get(
    "/usuarios",
    response_model=List[UsuarioResponse],
    dependencies=[Depends(require_roles(RolUsuario.SUPER_ADMIN, RolUsuario.ADMINISTRADOR))],
)
async def list_usuarios(db: AsyncSession = Depends(get_db)):
    """Lista todos los operadores y administradores registrados en el sistema."""
    result = await db.execute(select(UsuarioModel).order_by(UsuarioModel.creado_el.asc()))
    return result.scalars().all()


@router.post(
    "/usuarios",
    response_model=UsuarioResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(RolUsuario.SUPER_ADMIN, RolUsuario.ADMINISTRADOR))],
)
async def create_usuario(data: UsuarioCreate, db: AsyncSession = Depends(get_db)):
    """Registra un nuevo usuario operador o administrador en el sistema."""
    clean_email = data.email.lower().strip()
    existing = await db.execute(select(UsuarioModel).where(UsuarioModel.email == clean_email))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe un usuario registrado con el correo {clean_email}.",
        )

    user = UsuarioModel(
        id=f"user-{str(uuid.uuid4())[:8]}",
        email=clean_email,
        password_hash=hash_password(data.password),
        nombre_completo=data.nombre_completo.strip(),
        rol=data.rol,
        activo=data.activo,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.patch(
    "/usuarios/{user_id}",
    response_model=UsuarioResponse,
    dependencies=[Depends(require_roles(RolUsuario.SUPER_ADMIN, RolUsuario.ADMINISTRADOR))],
)
async def update_usuario(
    user_id: str,
    data: UsuarioUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_user),
):
    """Actualiza rol, estado o contraseña de un usuario."""
    result = await db.execute(select(UsuarioModel).where(UsuarioModel.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    if data.nombre_completo is not None:
        user.nombre_completo = data.nombre_completo.strip()
    if data.rol is not None:
        user.rol = data.rol
    if data.activo is not None:
        user.activo = data.activo
    if data.password:
        user.password_hash = hash_password(data.password)

    await db.commit()
    await db.refresh(user)
    return user
