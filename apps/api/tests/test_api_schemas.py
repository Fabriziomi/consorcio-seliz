from domain.schemas import ConsorcioCreate, ContactoCreate, TicketCreate, PrioridadTicket, EstadoTicket


def test_consorcio_schema():
    consorcio = ConsorcioCreate(
        nombre="Consorcio Corrientes y Lavalle",
        direccion="Av. Corrientes 1240, CABA",
        cuit="30-71122334-5",
        cbu_bancario="0140000000000000000001",
        alias_bancario="CONSORCIO.LAVALLE",
        email_cobranzas="cobranzas.lavalle@seliz.com.ar",
    )
    assert consorcio.nombre == "Consorcio Corrientes y Lavalle"
    assert consorcio.alias_bancario == "CONSORCIO.LAVALLE"
    assert consorcio.activo is True


def test_ticket_schema():
    ticket = TicketCreate(
        contacto_id="cont-123",
        intencion="RECLAMO_MANTENIMIENTO",
        descripcion="Pérdida de agua en palier 4to piso",
        prioridad=PrioridadTicket.ALTA,
        estado=EstadoTicket.NUEVO,
        creado_fuera_de_horario=True,
    )
    assert ticket.prioridad == PrioridadTicket.ALTA
    assert ticket.creado_fuera_de_horario is True
