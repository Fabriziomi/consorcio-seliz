import uuid
from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    JSON,
    Enum as SQLEnum,
)
from sqlalchemy.orm import relationship
from infrastructure.database import Base
from domain.schemas import (
    RolContacto,
    RolUsuario,
    PrioridadTicket,
    EstadoTicket,
    CategoriaIncidencia,
    EstadoExpediente,
    EstadoConversacion,
    TipoMensaje,
    EnviadoPor,
)


class ConsorcioModel(Base):
    __tablename__ = "consorcios"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    nombre = Column(String(255), nullable=False)
    direccion = Column(String(255), nullable=False)
    cuit = Column(String(30), nullable=True)
    cbu_bancario = Column(String(30), nullable=True)
    alias_bancario = Column(String(50), nullable=True)
    email_cobranzas = Column(String(100), nullable=True)
    telefono_porteria = Column(String(50), nullable=True)
    emergencia_ascensores = Column(String(50), nullable=True)
    emergencia_plomeria = Column(String(50), nullable=True)
    pautas_mudanza = Column(Text, nullable=True)
    activo = Column(Boolean, default=True)
    creado_el = Column(DateTime, default=datetime.utcnow)

    contactos = relationship("ContactoModel", back_populates="consorcio")
    tickets = relationship("TicketConsultaModel", back_populates="consorcio")
    expedientes = relationship("ExpedienteIncidenciaModel", back_populates="consorcio")
    atributos_dinamicos = relationship("ConsorcioAtributoDinamicoModel", back_populates="consorcio")
    conversaciones = relationship("ConversacionModel", back_populates="consorcio")


class ConsorcioAtributoDinamicoModel(Base):
    __tablename__ = "consorcios_atributos_dinamicos"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    consorcio_id = Column(String(36), ForeignKey("consorcios.id"), nullable=False)
    clave = Column(String(100), nullable=False)
    etiqueta_visible = Column(String(150), nullable=False)
    valor = Column(Text, nullable=False)
    es_publico_vecinos = Column(Boolean, default=True)

    consorcio = relationship("ConsorcioModel", back_populates="atributos_dinamicos")


class ContactoModel(Base):
    __tablename__ = "contactos"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    telefono_wa = Column(String(50), unique=True, nullable=False, index=True)
    nombre_completo = Column(String(150), nullable=True)
    consorcio_id = Column(String(36), ForeignKey("consorcios.id"), nullable=True)
    unidad_funcional = Column(String(50), nullable=True)
    rol = Column(SQLEnum(RolContacto), default=RolContacto.OTRO)
    foto_url = Column(String(500), nullable=True)
    creado_el = Column(DateTime, default=datetime.utcnow)
    ultimo_contacto_el = Column(DateTime, nullable=True)

    consorcio = relationship("ConsorcioModel", back_populates="contactos")
    tickets = relationship("TicketConsultaModel", back_populates="contacto", cascade="all, delete-orphan")
    conversaciones = relationship("ConversacionModel", back_populates="contacto", cascade="all, delete-orphan")

    @property
    def consorcio_nombre(self):
        return self.consorcio.nombre if self.consorcio else None


class ExpedienteIncidenciaModel(Base):
    __tablename__ = "expedientes_incidencias"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    codigo = Column(String(50), unique=True, nullable=False, index=True)
    consorcio_id = Column(String(36), ForeignKey("consorcios.id"), nullable=False, index=True)
    titulo = Column(String(255), nullable=False)
    categoria = Column(SQLEnum(CategoriaIncidencia), default=CategoriaIncidencia.OTRO, nullable=False)
    prioridad = Column(SQLEnum(PrioridadTicket), default=PrioridadTicket.NORMAL, nullable=False)
    estado = Column(SQLEnum(EstadoExpediente), default=EstadoExpediente.ABIERTO, nullable=False)
    descripcion_consolidada = Column(Text, nullable=False)
    proveedor_asignado = Column(String(150), nullable=True)
    creado_el = Column(DateTime, default=datetime.utcnow, nullable=False)
    actualizado_el = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    resuelto_el = Column(DateTime, nullable=True)

    consorcio = relationship("ConsorcioModel", back_populates="expedientes")
    tickets = relationship("TicketConsultaModel", back_populates="expediente")

    @property
    def consorcio_nombre(self):
        return self.consorcio.nombre if self.consorcio else None

    @property
    def tickets_count(self):
        return len(self.tickets) if self.tickets else 0


class TicketConsultaModel(Base):
    __tablename__ = "tickets_consultas"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    contacto_id = Column(String(36), ForeignKey("contactos.id"), nullable=False)
    consorcio_id = Column(String(36), ForeignKey("consorcios.id"), nullable=True)
    expediente_id = Column(String(36), ForeignKey("expedientes_incidencias.id"), nullable=True, index=True)
    intencion = Column(String(50), nullable=False)
    sub_intencion = Column(String(100), nullable=True)
    prioridad = Column(SQLEnum(PrioridadTicket), default=PrioridadTicket.NORMAL)
    estado = Column(SQLEnum(EstadoTicket), default=EstadoTicket.NUEVO)
    descripcion = Column(Text, nullable=False)
    adjuntos_urls = Column(JSON, nullable=True)
    creado_fuera_de_horario = Column(Boolean, default=False)
    creado_el = Column(DateTime, default=datetime.utcnow)

    contacto = relationship("ContactoModel", back_populates="tickets")
    consorcio = relationship("ConsorcioModel", back_populates="tickets")
    expediente = relationship("ExpedienteIncidenciaModel", back_populates="tickets")

    @property
    def contacto_nombre(self):
        return self.contacto.nombre_completo if self.contacto else None

    @property
    def contacto_unidad(self):
        return self.contacto.unidad_funcional if self.contacto else None

    @property
    def consorcio_nombre(self):
        return self.consorcio.nombre if self.consorcio else None

    @property
    def expediente_codigo(self):
        return self.expediente.codigo if self.expediente else None


class FaqAprobadaModel(Base):
    __tablename__ = "faqs_aprobadas"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    consorcio_id = Column(String(36), ForeignKey("consorcios.id"), nullable=True)
    pregunta = Column(Text, nullable=False)
    respuesta_oficial = Column(Text, nullable=False)
    activo = Column(Boolean, default=True)


class UsuarioModel(Base):
    __tablename__ = "usuarios"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    nombre_completo = Column(String(150), nullable=False)
    rol = Column(SQLEnum(RolUsuario), default=RolUsuario.ADMINISTRADOR, nullable=False)
    activo = Column(Boolean, default=True, nullable=False)
    creado_el = Column(DateTime, default=datetime.utcnow, nullable=False)
    ultimo_login = Column(DateTime, nullable=True)

    conversaciones_asignadas = relationship("ConversacionModel", back_populates="agente")


class ConversacionModel(Base):
    __tablename__ = "conversaciones"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    contacto_id = Column(String(36), ForeignKey("contactos.id"), nullable=False, index=True)
    consorcio_id = Column(String(36), ForeignKey("consorcios.id"), nullable=True, index=True)
    estado = Column(SQLEnum(EstadoConversacion), default=EstadoConversacion.OPEN, nullable=False, index=True)
    bot_activo = Column(Boolean, default=True, nullable=False)
    agente_id = Column(String(36), ForeignKey("usuarios.id"), nullable=True, index=True)
    etiquetas = Column(JSON, nullable=True, default=list)
    ultimo_mensaje_el = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    creado_el = Column(DateTime, default=datetime.utcnow, nullable=False)

    contacto = relationship("ContactoModel", back_populates="conversaciones")
    consorcio = relationship("ConsorcioModel", back_populates="conversaciones")
    agente = relationship("UsuarioModel", back_populates="conversaciones_asignadas")
    mensajes = relationship("MensajeModel", back_populates="conversacion", cascade="all, delete-orphan", order_by="MensajeModel.creado_el")

    @property
    def contacto_nombre(self):
        return self.contacto.nombre_completo if self.contacto else None

    @property
    def contacto_telefono(self):
        return self.contacto.telefono_wa if self.contacto else None

    @property
    def contacto_unidad(self):
        return self.contacto.unidad_funcional if self.contacto else None

    @property
    def contacto_foto_url(self):
        return self.contacto.foto_url if self.contacto else None

    @property
    def consorcio_nombre(self):
        return self.consorcio.nombre if self.consorcio else None

    @property
    def agente_nombre(self):
        return self.agente.nombre_completo if self.agente else None

    @property
    def ultimo_mensaje_texto(self):
        if self.mensajes:
            return self.mensajes[-1].contenido
        return None

    @property
    def mensajes_no_leidos_count(self):
        if self.mensajes:
            return sum(1 for m in self.mensajes if not m.leido and m.tipo == TipoMensaje.INCOMING)
        return 0


class MensajeModel(Base):
    __tablename__ = "mensajes"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversacion_id = Column(String(36), ForeignKey("conversaciones.id"), nullable=False, index=True)
    tipo = Column(SQLEnum(TipoMensaje), default=TipoMensaje.OUTGOING, nullable=False)
    contenido = Column(Text, nullable=False)
    privado = Column(Boolean, default=False, nullable=False)
    enviado_por = Column(SQLEnum(EnviadoPor), default=EnviadoPor.AGENTE, nullable=False)
    agente_id = Column(String(36), ForeignKey("usuarios.id"), nullable=True)
    media_url = Column(String(500), nullable=True)
    media_tipo = Column(String(50), nullable=True)
    leido = Column(Boolean, default=False, nullable=False)
    whatsapp_message_id = Column(String(100), nullable=True, index=True)
    creado_el = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    conversacion = relationship("ConversacionModel", back_populates="mensajes")
    agente = relationship("UsuarioModel")

    @property
    def agente_nombre(self):
        return self.agente.nombre_completo if self.agente else None


class EtiquetaModel(Base):
    __tablename__ = "etiquetas"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    titulo = Column(String(50), unique=True, nullable=False, index=True)
    color = Column(String(20), default="#475569", nullable=False)
    descripcion = Column(String(150), nullable=True)
    creado_el = Column(DateTime, default=datetime.utcnow, nullable=False)
