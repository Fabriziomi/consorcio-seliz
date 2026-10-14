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


class RolUsuario(str, Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    ADMINISTRADOR = "ADMINISTRADOR"
    OPERADOR = "OPERADOR"
    LECTOR = "LECTOR"


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


class CategoriaIncidencia(str, Enum):
    ASCENSORES = "ASCENSORES"
    PLOMERIA = "PLOMERIA"
    ELECTRICIDAD = "ELECTRICIDAD"
    GAS_CALEFACCION = "GAS_CALEFACCION"
    PORTON_ACCESO = "PORTON_ACCESO"
    LIMPIEZA_AREAS_COMUNES = "LIMPIEZA_AREAS_COMUNES"
    SEGURIDAD = "SEGURIDAD"
    ADMINISTRACION_CONSULTA = "ADMINISTRACION_CONSULTA"
    OTRO = "OTRO"


class EstadoExpediente(str, Enum):
    ABIERTO = "ABIERTO"
    EN_CURSO = "EN_CURSO"
    EN_ESPERA_PROVEEDOR = "EN_ESPERA_PROVEEDOR"
    RESUELTO = "RESUELTO"
    CERRADO = "CERRADO"


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
    consorcio_nombre: Optional[str] = None


class TicketBase(BaseModel):
    contacto_id: str
    consorcio_id: Optional[str] = None
    expediente_id: Optional[str] = None
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
    expediente_id: Optional[str] = None


class TicketResponse(TicketBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    creado_el: datetime
    contacto_nombre: Optional[str] = None
    contacto_unidad: Optional[str] = None
    consorcio_nombre: Optional[str] = None
    expediente_codigo: Optional[str] = None


class ExpedienteBase(BaseModel):
    consorcio_id: str
    titulo: str
    categoria: CategoriaIncidencia = CategoriaIncidencia.OTRO
    prioridad: PrioridadTicket = PrioridadTicket.NORMAL
    estado: EstadoExpediente = EstadoExpediente.ABIERTO
    descripcion_consolidada: str
    proveedor_asignado: Optional[str] = None


class ExpedienteCreate(ExpedienteBase):
    pass


class ExpedienteUpdate(BaseModel):
    titulo: Optional[str] = None
    categoria: Optional[CategoriaIncidencia] = None
    prioridad: Optional[PrioridadTicket] = None
    estado: Optional[EstadoExpediente] = None
    descripcion_consolidada: Optional[str] = None
    proveedor_asignado: Optional[str] = None


class ExpedienteResponse(ExpedienteBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    codigo: str
    creado_el: datetime
    actualizado_el: datetime
    resuelto_el: Optional[datetime] = None
    consorcio_nombre: Optional[str] = None
    tickets_count: int = 0


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


# --- Esquemas de Usuarios y Autenticación ---
class UsuarioBase(BaseModel):
    email: str
    nombre_completo: str
    rol: RolUsuario = RolUsuario.OPERADOR
    activo: bool = True


class UsuarioCreate(UsuarioBase):
    password: str


class UsuarioUpdate(BaseModel):
    nombre_completo: Optional[str] = None
    rol: Optional[RolUsuario] = None
    activo: Optional[bool] = None
    password: Optional[str] = None


class UsuarioResponse(UsuarioBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    creado_el: datetime
    ultimo_login: Optional[datetime] = None


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UsuarioResponse
