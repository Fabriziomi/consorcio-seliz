import asyncio
import uuid
from datetime import datetime
from infrastructure.database import AsyncSessionLocal, engine, Base
from infrastructure.models import (
    ConsorcioModel,
    ConsorcioAtributoDinamicoModel,
    ContactoModel,
    TicketConsultaModel,
    FaqAprobadaModel,
)
from domain.schemas import RolContacto, PrioridadTicket, EstadoTicket
from core.logging import logger


async def seed_data():
    logger.info("[SEED] Creando tablas si no existen...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # 1. Consorcio Corrientes y Lavalle
        consorcio_1_id = "cons-corrientes-lavalle"
        c1 = await session.get(ConsorcioModel, consorcio_1_id)
        if not c1:
            c1 = ConsorcioModel(
                id=consorcio_1_id,
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
            session.add(c1)
            logger.info(f"[SEED] Consorcio 1 creado: {c1.nombre}")

            # Atributos dinámicos (Opción B)
            session.add(ConsorcioAtributoDinamicoModel(
                consorcio_id=consorcio_1_id,
                clave="codigo_alarma_palier",
                etiqueta_visible="Código Alarma Palier",
                valor="7842#",
                es_publico_vecinos=False,
            ))
            session.add(ConsorcioAtributoDinamicoModel(
                consorcio_id=consorcio_1_id,
                clave="llave_tanque_agua",
                etiqueta_visible="Ubicación Llave Tanque",
                valor="Sala de máquinas terraza Torre Lavalle",
                es_publico_vecinos=False,
            ))

        # 2. Consorcio Callao 2334
        consorcio_2_id = "cons-callao-2334"
        c2 = await session.get(ConsorcioModel, consorcio_2_id)
        if not c2:
            c2 = ConsorcioModel(
                id=consorcio_2_id,
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
            session.add(c2)
            logger.info(f"[SEED] Consorcio 2 creado: {c2.nombre}")

        # 3. Contactos de Vecinos Iniciales
        vecino_1_phone = "+5491144558899"
        v1 = await session.get(ContactoModel, "cont-1")
        if not v1:
            v1 = ContactoModel(
                id="cont-1",
                telefono_wa=vecino_1_phone,
                nombre_completo="Carlos Méndez",
                consorcio_id=consorcio_1_id,
                unidad_funcional="Torre Corrientes 4° B",
                rol=RolContacto.PROPIETARIO,
            )
            session.add(v1)

        vecino_2_phone = "+5491166778899"
        v2 = await session.get(ContactoModel, "cont-2")
        if not v2:
            v2 = ContactoModel(
                id="cont-2",
                telefono_wa=vecino_2_phone,
                nombre_completo="Lucía Rossi",
                consorcio_id=consorcio_2_id,
                unidad_funcional="Piso 7 Depto A",
                rol=RolContacto.INQUILINO,
            )
            session.add(v2)

        # 4. Tickets de Ejemplo
        t1 = await session.get(TicketConsultaModel, "tick-1042")
        if not t1:
            t1 = TicketConsultaModel(
                id="tick-1042",
                contacto_id="cont-1",
                consorcio_id=consorcio_1_id,
                intencion="RECLAMO_MANTENIMIENTO",
                sub_intencion="CORTE_LUZ_PALIER",
                prioridad=PrioridadTicket.ALTA,
                estado=EstadoTicket.EN_REVISION,
                descripcion="Corte de luz en palier del piso 4 Torre Corrientes.",
                creado_fuera_de_horario=True,
            )
            session.add(t1)

        await session.commit()
        logger.info("[SEED] Datos iniciales cargados con éxito.")


if __name__ == "__main__":
    asyncio.run(seed_data())
