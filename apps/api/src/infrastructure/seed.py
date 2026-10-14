from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from core.logging import logger
from infrastructure.models import (
    ConsorcioModel,
    ConsorcioAtributoDinamicoModel,
    ContactoModel,
    TicketConsultaModel,
)
from domain.schemas import RolContacto, PrioridadTicket, EstadoTicket


async def seed_initial_data(db: AsyncSession):
    """
    Pobla la base de datos con los consorcios administrados por Dra. Ivana Seliz,
    atributos dinámicos, contactos de prueba y tickets iniciales si la base está vacía.
    """
    res = await db.execute(select(ConsorcioModel))
    existing = res.scalars().first()
    if existing:
        logger.info("[DB_SEED] La base de datos ya cuenta con consorcios. Omitiendo seed.")
        return

    logger.info("[DB_SEED] Base de datos vacía detectada. Sembrando datos iniciales de Consorcios Seliz...")

    # 1. Consorcios
    c1 = ConsorcioModel(
        id="cons-corrientes-lavalle",
        nombre="Consorcio Corrientes y Lavalle (Torres, Cochera y Galería)",
        direccion="Av. Corrientes 1240 / Lavalle 1241, CABA",
        cuit="30-71122334-5",
        cbu_bancario="0140000000000000000001",
        alias_bancario="CONSORCIO.LAVALLE.OFICIAL",
        email_cobranzas="cobranzas.lavalle@selizadministraciones.com.ar",
        telefono_porteria="+54 9 11 4371-0001",
        emergencia_ascensores="+54 9 11 4444-1111",
        emergencia_plomeria="+54 9 11 4444-2222",
        pautas_mudanza="Lunes a Viernes de 9 a 17 hs y Sábados de 9 a 13 hs. Presentar seguro flete 48hs antes.",
        activo=True,
    )

    c2 = ConsorcioModel(
        id="cons-callao-2334",
        nombre="Consorcio Callao 2334",
        direccion="Av. Callao 2334, Recoleta, CABA",
        cuit="30-71998877-6",
        cbu_bancario="0140000000000000000002",
        alias_bancario="CALLAO.2334.EXPENSAS",
        email_cobranzas="callao2334@selizadministraciones.com.ar",
        telefono_porteria="+54 9 11 4801-9999",
        emergencia_ascensores="+54 9 11 4444-3333",
        emergencia_plomeria="+54 9 11 4444-4444",
        pautas_mudanza="Lunes a Viernes de 10 a 16 hs exclusivamente.",
        activo=True,
    )

    db.add_all([c1, c2])
    await db.flush()

    # 2. Atributos Dinámicos
    attrs = [
        # Corrientes y Lavalle
        ConsorcioAtributoDinamicoModel(
            id="attr-c1-1",
            consorcio_id="cons-corrientes-lavalle",
            clave="codigo_alarma_palier",
            etiqueta_visible="Código de Alarma Palier",
            valor="9842#",
            es_publico_vecinos=False,  # Protegido por seguridad
        ),
        ConsorcioAtributoDinamicoModel(
            id="attr-c1-2",
            consorcio_id="cons-corrientes-lavalle",
            clave="piso_sum",
            etiqueta_visible="Ubicación SUM y Parrilla",
            valor="Piso 15 Torre Lavalle",
            es_publico_vecinos=True,
        ),
        ConsorcioAtributoDinamicoModel(
            id="attr-c1-3",
            consorcio_id="cons-corrientes-lavalle",
            clave="encargado_nombre",
            etiqueta_visible="Encargado Titular",
            valor="Roberto Martínez (+54 9 11 4371-0002)",
            es_publico_vecinos=True,
        ),
        # Callao 2334
        ConsorcioAtributoDinamicoModel(
            id="attr-c2-1",
            consorcio_id="cons-callao-2334",
            clave="llave_tanque_agua",
            etiqueta_visible="Ubicación Llave Tanque",
            valor="Guardada en tablero técnico central",
            es_publico_vecinos=False,  # Protegido por seguridad
        ),
        ConsorcioAtributoDinamicoModel(
            id="attr-c2-2",
            consorcio_id="cons-callao-2334",
            clave="horario_retiro_basura",
            etiqueta_visible="Horario de Basura",
            valor="Todos los días de 20:00 a 21:00 hs",
            es_publico_vecinos=True,
        ),
    ]
    db.add_all(attrs)
    await db.flush()

    # 3. Contactos
    contactos = [
        ContactoModel(
            id="cont-1",
            telefono_wa="+5491144558899",
            nombre_completo="Carlos Méndez",
            consorcio_id="cons-corrientes-lavalle",
            unidad_funcional="Torre Corrientes 4° B",
            rol=RolContacto.PROPIETARIO,
        ),
        ContactoModel(
            id="cont-2",
            telefono_wa="+5491166778899",
            nombre_completo="Lucía Rossi",
            consorcio_id="cons-callao-2334",
            unidad_funcional="7° A",
            rol=RolContacto.INQUILINO,
        ),
        ContactoModel(
            id="cont-3",
            telefono_wa="+5491133221100",
            nombre_completo="Mariano Gómez",
            consorcio_id="cons-corrientes-lavalle",
            unidad_funcional="Cochera 14",
            rol=RolContacto.PROPIETARIO,
        ),
    ]
    db.add_all(contactos)
    await db.flush()

    # 4. Tickets Iniciales
    tickets = [
        TicketConsultaModel(
            id="tick-1042",
            contacto_id="cont-1",
            consorcio_id="cons-corrientes-lavalle",
            intencion="RECLAMO",
            sub_intencion="CORTE_LUZ_PALIER",
            prioridad=PrioridadTicket.ALTA,
            estado=EstadoTicket.EN_REVISION,
            descripcion="Corte de luz en palier del piso 4 Torre Corrientes.",
        ),
        TicketConsultaModel(
            id="tick-1041",
            contacto_id="cont-2",
            consorcio_id="cons-callao-2334",
            intencion="EXPENSAS",
            sub_intencion="CONSULTA_DATOS_PAGO",
            prioridad=PrioridadTicket.NORMAL,
            estado=EstadoTicket.NUEVO,
            descripcion="Consulta de CBU y datos de pago de expensas.",
        ),
        TicketConsultaModel(
            id="tick-1040",
            contacto_id="cont-3",
            consorcio_id="cons-corrientes-lavalle",
            intencion="EMERGENCIA",
            sub_intencion="ASCENSOR_ATRAPADOS",
            prioridad=PrioridadTicket.CRITICA,
            estado=EstadoTicket.DERIVADO,
            descripcion="Personas atrapadas en ascensor Torre Lavalle.",
        ),
    ]
    db.add_all(tickets)
    await db.commit()
    logger.info("[DB_SEED] Sembrado inicial completado con éxito.")
