from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class RolContacto(str, Enum):
    PROPIETARIO = "PROPIETARIO"
    INQUILINO = "INQUILINO"
    INMOBILIARIA = "INMOBILIARIA"
    PROVEEDOR = "PROVEEDOR"
    OTRO = "OTRO"


class PrioridadTicket(str, Enum):
    CRITICA = "CRITICA"
    ALTA = "ALTA"
    NORMAL = "NORMAL"
    BAJA = "BAJA"


class EstadoTicket(str, Enum):
    NUEVO = "NUEVO"
    EN_REVISION = "EN_REVISION"
    DERIVADO = "DERIVADO"
    ESPERANDO_RESPUESTA = "ESPERANDO_RESPUESTA"
    RESUELTO = "RESUELTO"


class ConsorcioBase(BaseModel):
    nombre: str
    direccion: str
    cuit: Optional[str] = None
    cbu_bancario: Optional[str] = None
    alias_bancario: Optional[str] = None
    email_cobranzas: Optional[str] = None
    telefono_porteria: Optional[str] = None
    emergencia_ascensores: Optional[str] = None
    emergencia_plomeria: Optional[str] = None
    pautas_mudanza: Optional[str] = None
    activo: bool = True


class ConsorcioCreate(ConsorcioBase):
    pass


class ConsorcioResponse(ConsorcioBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    creado_el: datetime


class ContactoBase(BaseModel):
    telefono_wa: str
    nombre_completo: Optional[str] = None
    consorcio_id: Optional[str] = None
    unidad_funcional: Optional[str] = None
    rol: RolContacto = RolContacto.OTRO


class ContactoCreate(ContactoBase):
    pass


class ContactoResponse(ContactoBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    creado_el: datetime
    ultimo_contacto_el: Optional[datetime] = None


class TicketBase(BaseModel):
    contacto_id: str
    consorcio_id: Optional[str] = None
    intencion: str
    sub_intencion: Optional[str] = None
    prioridad: PrioridadTicket = PrioridadTicket.NORMAL
    estado: EstadoTicket = EstadoTicket.NUEVO
    descripcion: str
    adjuntos_urls: Optional[List[str]] = None
    creado_fuera_de_horario: bool = False


class TicketCreate(TicketBase):
    pass


class TicketUpdate(BaseModel):
    estado: Optional[EstadoTicket] = None
    prioridad: Optional[PrioridadTicket] = None
    descripcion: Optional[str] = None


class TicketResponse(TicketBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    creado_el: datetime
    contacto_nombre: Optional[str] = None
    contacto_unidad: Optional[str] = None
    consorcio_nombre: Optional[str] = None


# --- Esquemas de Webhooks ---
class EvolutionMessageData(BaseModel):
    remoteJid: str
    fromMe: bool
    pushName: Optional[str] = None
    conversation: Optional[str] = None
    messageType: Optional[str] = None
    messageTimestamp: Optional[int] = None


class EvolutionWebhookPayload(BaseModel):
    event: str
    instance: str
    data: Dict[str, Any]
