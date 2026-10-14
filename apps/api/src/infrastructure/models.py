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
from domain.schemas import RolContacto, PrioridadTicket, EstadoTicket


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
    atributos_dinamicos = relationship("ConsorcioAtributoDinamicoModel", back_populates="consorcio")


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
    creado_el = Column(DateTime, default=datetime.utcnow)
    ultimo_contacto_el = Column(DateTime, nullable=True)

    consorcio = relationship("ConsorcioModel", back_populates="contactos")
    tickets = relationship("TicketConsultaModel", back_populates="contacto")


class TicketConsultaModel(Base):
    __tablename__ = "tickets_consultas"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    contacto_id = Column(String(36), ForeignKey("contactos.id"), nullable=False)
    consorcio_id = Column(String(36), ForeignKey("consorcios.id"), nullable=True)
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

    @property
    def contacto_nombre(self):
        return self.contacto.nombre_completo if self.contacto else None

    @property
    def contacto_unidad(self):
        return self.contacto.unidad_funcional if self.contacto else None

    @property
    def consorcio_nombre(self):
        return self.consorcio.nombre if self.consorcio else None


class FaqAprobadaModel(Base):
    __tablename__ = "faqs_aprobadas"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    consorcio_id = Column(String(36), ForeignKey("consorcios.id"), nullable=True)
    pregunta = Column(Text, nullable=False)
    respuesta_oficial = Column(Text, nullable=False)
    activo = Column(Boolean, default=True)
