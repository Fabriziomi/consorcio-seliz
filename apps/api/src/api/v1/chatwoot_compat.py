import zlib
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Union
from fastapi import APIRouter, Depends, HTTPException, Request, Response, Query, Header, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import desc

from core.logging import logger
from core.security import verify_password, create_access_token, decode_access_token
from infrastructure.database import get_db
from infrastructure.models import (
    UsuarioModel,
    ConversacionModel,
    MensajeModel,
    ContactoModel,
    ConsorcioModel,
    EtiquetaModel,
)
from domain.schemas import (
    EstadoConversacion,
    TipoMensaje,
    EnviadoPor,
    RolUsuario,
)
from infrastructure.evolution_client import evolution_client
from infrastructure.takeover_service import takeover_service

router = APIRouter()


def str_to_int_id(val: str) -> int:
    """Genera un identificador entero positivo y determinista a partir de un UUID o string."""
    if not val:
        return 1
    return (zlib.crc32(val.encode("utf-8")) & 0x7FFFFFFF) or 1


async def get_chatwoot_user(
    request: Request,
    access_token_header: Optional[str] = Header(None, alias="access-token"),
    authorization: Optional[str] = Header(None, alias="Authorization"),
    db: AsyncSession = Depends(get_db),
) -> UsuarioModel:
    """
    Autenticación compatible con la app móvil de Chatwoot:
    Acepta 'access-token' de los headers de Devise Token Auth o 'Authorization: Bearer <jwt>'.
    """
    token = access_token_header
    if not token and authorization:
        parts = authorization.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            token = parts[1]
        else:
            token = authorization

    if not token:
        # Intento de parámetro en query string
        token = request.query_params.get("access_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No se proporcionaron credenciales de acceso.",
        )

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado.",
        )

    user_id = payload.get("sub")
    res = await db.execute(select(UsuarioModel).where(UsuarioModel.id == user_id))
    user = res.scalar_one_or_none()
    if not user or not user.activo:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario inactivo o no encontrado.")

    return user


async def find_conversation_by_id_or_int(conv_id_str: str, db: AsyncSession) -> Optional[ConversacionModel]:
    """Permite buscar una conversación tanto por su UUID nativo como por su entero hash de Chatwoot."""
    # 1. Búsqueda directa por UUID
    res = await db.execute(
        select(ConversacionModel)
        .options(
            selectinload(ConversacionModel.contacto),
            selectinload(ConversacionModel.consorcio),
            selectinload(ConversacionModel.agente),
            selectinload(ConversacionModel.mensajes).selectinload(MensajeModel.agente),
        )
        .where(ConversacionModel.id == conv_id_str)
    )
    conv = res.scalar_one_or_none()
    if conv:
        return conv

    # 2. Si es numérico, comparar con hash
    try:
        numeric_target = int(conv_id_str)
        all_res = await db.execute(
            select(ConversacionModel).options(
                selectinload(ConversacionModel.contacto),
                selectinload(ConversacionModel.consorcio),
                selectinload(ConversacionModel.agente),
                selectinload(ConversacionModel.mensajes).selectinload(MensajeModel.agente),
            )
        )
        for c in all_res.scalars().all():
            if str_to_int_id(c.id) == numeric_target:
                return c
    except ValueError:
        pass

    return None


def _format_chatwoot_message(m: MensajeModel, conv: ConversacionModel) -> Dict[str, Any]:
    # message_type: 0 = incoming, 1 = outgoing, 2 = activity
    msg_type_code = 0 if m.tipo == TipoMensaje.INCOMING else 1
    if m.privado or m.tipo == TipoMensaje.ACTIVITY:
        msg_type_code = 2

    sender_name = "Bot Seliz"
    sender_id = 9999
    if m.enviado_por == EnviadoPor.VECINO:
        sender_name = conv.contacto_nombre or "Vecino"
        sender_id = str_to_int_id(conv.contacto_id)
    elif m.enviado_por == EnviadoPor.AGENTE:
        sender_name = m.agente_nombre or "Operador"
        sender_id = str_to_int_id(m.agente_id or "user-admin-seliz")

    created_timestamp = int(m.creado_el.replace(tzinfo=timezone.utc).timestamp()) if m.creado_el else int(datetime.now().timestamp())

    return {
        "id": str_to_int_id(m.id),
        "content": m.contenido,
        "account_id": 1,
        "inbox_id": 1,
        "conversation_id": str_to_int_id(m.conversacion_id),
        "message_type": msg_type_code,
        "created_at": created_timestamp,
        "updated_at": created_timestamp,
        "private": m.privado,
        "status": "sent",
        "source_id": m.whatsapp_message_id,
        "content_type": "text",
        "sender": {
            "id": sender_id,
            "name": sender_name,
            "available_name": sender_name,
            "avatar_url": "",
            "type": "contact" if m.enviado_por == EnviadoPor.VECINO else "user",
        },
        "attachments": [
            {
                "id": str_to_int_id(m.id),
                "message_id": str_to_int_id(m.id),
                "file_type": m.media_tipo or "audio",
                "account_id": 1,
                "data_url": m.media_url,
                "thumb_url": m.media_url,
            }
        ] if m.media_url else [],
    }


def _format_chatwoot_conversation(conv: ConversacionModel) -> Dict[str, Any]:
    c_int_id = str_to_int_id(conv.id)
    contact_int_id = str_to_int_id(conv.contacto_id)
    contact_name = conv.contacto_nombre or "Vecino"
    contact_phone = conv.contacto_telefono or ""

    created_ts = int(conv.creado_el.replace(tzinfo=timezone.utc).timestamp()) if conv.creado_el else int(datetime.now().timestamp())
    last_act_ts = int(conv.ultimo_mensaje_el.replace(tzinfo=timezone.utc).timestamp()) if conv.ultimo_mensaje_el else created_ts

    formatted_messages = [_format_chatwoot_message(m, conv) for m in conv.mensajes] if conv.mensajes else []

    assignee_data = None
    if conv.agente:
        assignee_data = {
            "id": str_to_int_id(conv.agente.id),
            "name": conv.agente.nombre_completo,
            "available_name": conv.agente.nombre_completo,
            "avatar_url": "",
            "email": conv.agente.email,
            "role": "administrator" if conv.agente.rol == RolUsuario.SUPER_ADMIN else "agent",
        }

    return {
        "id": c_int_id,
        "account_id": 1,
        "inbox_id": 1,
        "status": conv.estado.value,
        "muted": False,
        "can_reply": True,
        "unread_count": conv.mensajes_no_leidos_count,
        "uuid": conv.id,
        "created_at": created_ts,
        "timestamp": last_act_ts,
        "last_activity_at": last_act_ts,
        "meta": {
            "sender": {
                "id": contact_int_id,
                "name": contact_name,
                "phone_number": contact_phone,
                "thumbnail": "",
                "identifier": contact_phone,
                "additional_attributes": {
                    "consorcio": conv.consorcio_nombre or "",
                    "unidad": conv.contacto_unidad or "",
                },
            },
            "assignee": assignee_data,
        },
        "messages": formatted_messages,
        "labels": conv.etiquetas or [],
        "additional_attributes": {
            "consorcio": conv.consorcio_nombre or "",
            "unidad": conv.contacto_unidad or "",
        },
    }


# =========================================================================
# 1. AUTENTICACIÓN COMPATIBLE CON APP MÓVIL CHATWOOT
# =========================================================================
class ChatwootLoginPayload(BaseModel):
    email: str
    password: str


@router.post("/auth/sign_in")
async def chatwoot_sign_in(
    data: ChatwootLoginPayload,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """
    Endpoint de login compatible con Devise Token Auth usado por la app móvil de Chatwoot.
    Devuelve los headers: access-token, uid, client, expiry y el payload del usuario.
    """
    res = await db.execute(select(UsuarioModel).where(UsuarioModel.email == data.email.lower().strip()))
    user = res.scalar_one_or_none()

    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales de acceso incorrectas.",
        )

    if not user.activo:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cuenta inactiva.")

    # Generar JWT
    token = create_access_token(data={"sub": user.id, "email": user.email, "rol": user.rol.value})
    user_int_id = str_to_int_id(user.id)

    # Inyectar headers que espera Axios en Chatwoot Mobile
    response.headers["access-token"] = token
    response.headers["uid"] = user.email
    response.headers["client"] = "chatwoot-mobile-app"
    response.headers["expiry"] = str(int(datetime.now().timestamp()) + 86400 * 30)
    response.headers["token-type"] = "Bearer"

    user_payload = {
        "id": user_int_id,
        "name": user.nombre_completo,
        "email": user.email,
        "account_id": 1,
        "role": "administrator",
        "accounts": [
            {
                "id": 1,
                "name": "Administración Dra. Ivana Seliz",
                "role": "administrator",
                "status": "active",
            }
        ],
        "pubsub_token": token,
        "avatar_url": "",
        "available_name": user.nombre_completo,
        "availability_status": "available",
        "type": "user",
    }

    return {"data": user_payload}


@router.get("/profile")
async def chatwoot_profile(user: UsuarioModel = Depends(get_chatwoot_user)):
    """Devuelve el perfil del usuario autenticado para la app móvil."""
    user_int_id = str_to_int_id(user.id)
    return {
        "id": user_int_id,
        "name": user.nombre_completo,
        "email": user.email,
        "account_id": 1,
        "role": "administrator",
        "accounts": [
            {
                "id": 1,
                "name": "Administración Dra. Ivana Seliz",
                "role": "administrator",
                "status": "active",
            }
        ],
        "pubsub_token": "seliz-pubsub-token",
        "avatar_url": "",
        "available_name": user.nombre_completo,
        "availability_status": "available",
    }


# =========================================================================
# 2. CONVERSACIONES COMPATIBLES CON CHATWOOT MOBILE
# =========================================================================
@router.get("/accounts/{account_id}/conversations")
async def chatwoot_list_conversations(
    account_id: int,
    status: Optional[str] = Query(None, description="open, resolved, pending, all"),
    page: int = Query(1, ge=1),
    assignee_type: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    user: UsuarioModel = Depends(get_chatwoot_user),
):
    """Lista las conversaciones en el formato exacto requerido por Chatwoot Mobile."""
    stmt = (
        select(ConversacionModel)
        .options(
            selectinload(ConversacionModel.contacto),
            selectinload(ConversacionModel.consorcio),
            selectinload(ConversacionModel.agente),
            selectinload(ConversacionModel.mensajes).selectinload(MensajeModel.agente),
        )
        .order_by(desc(ConversacionModel.ultimo_mensaje_el))
    )

    if status and status != "all":
        try:
            stmt = stmt.where(ConversacionModel.estado == EstadoConversacion(status))
        except ValueError:
            pass

    if assignee_type == "me":
        stmt = stmt.where(ConversacionModel.agente_id == user.id)
    elif assignee_type == "unassigned":
        stmt = stmt.where(ConversacionModel.agente_id.is_(None))

    # Paginación
    limit = 25
    skip = (page - 1) * limit
    stmt = stmt.offset(skip).limit(limit)

    res = await db.execute(stmt)
    convs = res.scalars().all()

    payload_list = [_format_chatwoot_conversation(c) for c in convs]

    # Conteos para meta
    all_res = await db.execute(select(ConversacionModel.id))
    all_count = len(all_res.scalars().all())

    return {
        "data": {
            "meta": {
                "all_count": all_count,
                "mine_count": 0,
                "unassigned_count": all_count,
                "page": page,
            },
            "payload": payload_list,
        }
    }


@router.get("/accounts/{account_id}/conversations/{conversation_id}")
async def chatwoot_get_conversation(
    account_id: int,
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
    user: UsuarioModel = Depends(get_chatwoot_user),
):
    """Devuelve una conversación específica para la pantalla de chat del celular."""
    conv = await find_conversation_by_id_or_int(conversation_id, db)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversación no encontrada.")

    return {"data": _format_chatwoot_conversation(conv)}


@router.get("/accounts/{account_id}/conversations/{conversation_id}/messages")
async def chatwoot_get_messages(
    account_id: int,
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
    user: UsuarioModel = Depends(get_chatwoot_user),
):
    """Lista los mensajes de la conversación ordenados cronológicamente."""
    conv = await find_conversation_by_id_or_int(conversation_id, db)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversación no encontrada.")

    payload = [_format_chatwoot_message(m, conv) for m in conv.mensajes]
    return {
        "meta": {},
        "payload": payload,
    }


class ChatwootSendMessagePayload(BaseModel):
    content: str
    private: Optional[bool] = False
    message_type: Optional[str] = "outgoing"


@router.post("/accounts/{account_id}/conversations/{conversation_id}/messages")
async def chatwoot_send_message(
    account_id: int,
    conversation_id: str,
    data: ChatwootSendMessagePayload,
    db: AsyncSession = Depends(get_db),
    user: UsuarioModel = Depends(get_chatwoot_user),
):
    """
    Envía un mensaje desde la app móvil oficial de Chatwoot:
    1. Si es público, se despacha a WhatsApp al vecino por Evolution API.
    2. Activa el Takeover Humano (12 hs).
    3. Persiste en MensajeModel.
    """
    conv = await find_conversation_by_id_or_int(conversation_id, db)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversación no encontrada.")

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    msg_id = f"msg-{str(uuid.uuid4())[:8]}"

    if not data.private:
        phone_wa = conv.contacto.telefono_wa if conv.contacto else None
        if phone_wa:
            clean_phone = phone_wa.replace("+", "").strip()
            remote_jid = f"{clean_phone}@s.whatsapp.net"
            await evolution_client.send_text(remote_jid, data.content)
            await takeover_service.set_takeover(remote_jid)
            conv.bot_activo = False

        nuevo_mensaje = MensajeModel(
            id=msg_id,
            conversacion_id=conv.id,
            tipo=TipoMensaje.OUTGOING,
            contenido=data.content,
            privado=False,
            enviado_por=EnviadoPor.AGENTE,
            agente_id=user.id,
            leido=True,
            creado_el=now,
        )
    else:
        nuevo_mensaje = MensajeModel(
            id=msg_id,
            conversacion_id=conv.id,
            tipo=TipoMensaje.ACTIVITY,
            contenido=data.content,
            privado=True,
            enviado_por=EnviadoPor.AGENTE,
            agente_id=user.id,
            leido=True,
            creado_el=now,
        )

    conv.ultimo_mensaje_el = now
    db.add(nuevo_mensaje)
    await db.commit()
    await db.refresh(nuevo_mensaje)

    return _format_chatwoot_message(nuevo_mensaje, conv)


class ChatwootToggleStatusPayload(BaseModel):
    status: str


@router.post("/accounts/{account_id}/conversations/{conversation_id}/toggle_status")
async def chatwoot_toggle_status(
    account_id: int,
    conversation_id: str,
    data: ChatwootToggleStatusPayload,
    db: AsyncSession = Depends(get_db),
    user: UsuarioModel = Depends(get_chatwoot_user),
):
    """Cambia el estado de la conversación (open, resolved, pending) desde el celular."""
    conv = await find_conversation_by_id_or_int(conversation_id, db)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversación no encontrada.")

    try:
        conv.estado = EstadoConversacion(data.status.lower())
    except ValueError:
        conv.estado = EstadoConversacion.OPEN

    if conv.estado == EstadoConversacion.RESOLVED:
        conv.bot_activo = True
        if conv.contacto and conv.contacto.telefono_wa:
            clean_phone = conv.contacto.telefono_wa.replace("+", "").strip()
            await takeover_service.release_takeover(f"{clean_phone}@s.whatsapp.net")

    await db.commit()
    await db.refresh(conv)

    return {
        "payload": {
            "success": True,
            "current_status": conv.estado.value,
            "conversation_id": str_to_int_id(conv.id),
        }
    }


class ChatwootAssignPayload(BaseModel):
    assignee_id: Optional[Union[int, str]] = None


@router.post("/accounts/{account_id}/conversations/{conversation_id}/assignments")
async def chatwoot_assign_conversation(
    account_id: int,
    conversation_id: str,
    data: ChatwootAssignPayload,
    db: AsyncSession = Depends(get_db),
    user: UsuarioModel = Depends(get_chatwoot_user),
):
    """Asigna la conversación a un operador desde la app móvil."""
    conv = await find_conversation_by_id_or_int(conversation_id, db)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversación no encontrada.")

    if data.assignee_id:
        conv.agente_id = user.id
    else:
        conv.agente_id = None

    await db.commit()
    await db.refresh(conv)
    return {"payload": _format_chatwoot_conversation(conv)}


class ChatwootLabelsPayload(BaseModel):
    labels: List[str]


@router.post("/accounts/{account_id}/conversations/{conversation_id}/labels")
async def chatwoot_update_labels(
    account_id: int,
    conversation_id: str,
    data: ChatwootLabelsPayload,
    db: AsyncSession = Depends(get_db),
    user: UsuarioModel = Depends(get_chatwoot_user),
):
    """Actualiza etiquetas de la conversación desde el celular."""
    conv = await find_conversation_by_id_or_int(conversation_id, db)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversación no encontrada.")

    conv.etiquetas = [lbl.strip().upper() for lbl in data.labels if lbl.strip()]
    await db.commit()
    await db.refresh(conv)

    return {"payload": conv.etiquetas}


# =========================================================================
# 3. METADATOS: INBOXES, AGENTES Y ETIQUETAS
# =========================================================================
@router.get("/accounts/{account_id}/inboxes")
async def chatwoot_list_inboxes(
    account_id: int,
    user: UsuarioModel = Depends(get_chatwoot_user),
):
    """Devuelve la bandeja oficial de WhatsApp para la app móvil."""
    return {
        "payload": [
            {
                "id": 1,
                "name": "WhatsApp Dra. Ivana Seliz",
                "channel_type": "Channel::Whatsapp",
                "avatar_url": "",
                "phone_number": "+5491162483302",
                "enable_auto_assignment": True,
            }
        ]
    }


@router.get("/accounts/{account_id}/agents")
async def chatwoot_list_agents(
    account_id: int,
    db: AsyncSession = Depends(get_db),
    user: UsuarioModel = Depends(get_chatwoot_user),
):
    """Devuelve los operadores y administradores disponibles."""
    res = await db.execute(select(UsuarioModel).where(UsuarioModel.activo == True))
    users = res.scalars().all()
    payload = [
        {
            "id": str_to_int_id(u.id),
            "name": u.nombre_completo,
            "available_name": u.nombre_completo,
            "email": u.email,
            "role": "administrator" if u.rol == RolUsuario.SUPER_ADMIN else "agent",
            "availability_status": "available",
            "thumbnail": "",
        }
        for u in users
    ]
    return {"payload": payload}


@router.get("/accounts/{account_id}/labels")
async def chatwoot_list_labels(
    account_id: int,
    db: AsyncSession = Depends(get_db),
    user: UsuarioModel = Depends(get_chatwoot_user),
):
    """Devuelve las etiquetas disponibles para la app móvil."""
    res = await db.execute(select(EtiquetaModel).order_by(EtiquetaModel.titulo))
    labels = res.scalars().all()
    payload = [
        {
            "id": str_to_int_id(lbl.id),
            "title": lbl.titulo,
            "color": lbl.color,
            "description": lbl.descripcion or "",
        }
        for lbl in labels
    ]
    return {"payload": payload}


@router.get("/accounts/{account_id}/contacts")
async def chatwoot_list_contacts(
    account_id: int,
    db: AsyncSession = Depends(get_db),
    user: UsuarioModel = Depends(get_chatwoot_user),
):
    """Devuelve el directorio de contactos."""
    res = await db.execute(select(ContactoModel).order_by(ContactoModel.nombre_completo.asc()))
    contacts = res.scalars().all()
    payload = [
        {
            "id": str_to_int_id(c.id),
            "name": c.nombre_completo or c.telefono_wa,
            "phone_number": c.telefono_wa,
            "thumbnail": "",
            "identifier": c.telefono_wa,
            "additional_attributes": {
                "unidad": c.unidad_funcional or "",
            },
        }
        for c in contacts
    ]
    return {"payload": payload}


# =========================================================================
# 4. SUBSCRIPCIÓN A NOTIFICACIONES PUSH MÓVILES
# =========================================================================
class PushSubscriptionPayload(BaseModel):
    subscription_type: Optional[str] = "fcm"
    subscription_attributes: Optional[Dict[str, Any]] = None


@router.post("/notification_subscriptions")
async def register_push_token(
    data: PushSubscriptionPayload,
    user: UsuarioModel = Depends(get_chatwoot_user),
):
    """Registra el token FCM/APNS del teléfono de Ivana para notificaciones push."""
    logger.info(f"[CHATWOOT_COMPAT] Token push registrado para {user.email}: {data.subscription_type}")
    return {"status": "success", "message": "Dispositivo registrado para notificaciones push"}
