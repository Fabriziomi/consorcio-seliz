"""
Script de migración liviana y backfill de perfiles conversacionales (Fase 2).
Actualiza la estructura de la base de datos (SQLite o PostgreSQL) incorporando:
- contactos.bot_desactivado
- conversaciones.fsm_estado
- conversaciones.fsm_contexto
- conversaciones.needs_human_review
- conversaciones.ultimo_takeover_at
Y sincroniza los datos existentes para garantizar compatibilidad con ConversationFSM.
"""

import asyncio
import os
import sys
import logging
from typing import Set

# Ajustar PYTHONPATH
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
API_SRC = os.path.join(PROJECT_ROOT, "apps", "api", "src")
if API_SRC not in sys.path:
    sys.path.insert(0, API_SRC)

from dotenv import load_dotenv

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text, inspect

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("backfill_profiles")


async def migrate_and_backfill():
    db_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./consorcio.db")
    logger.info("Iniciando migración y backfill sobre: %s", db_url)

    engine = create_async_engine(db_url, echo=False)
    is_sqlite = db_url.startswith("sqlite")

    async with engine.begin() as conn:
        # 1. Obtener columnas existentes en 'contactos'
        def get_contactos_cols(sync_conn):
            insp = inspect(sync_conn)
            return {col["name"] for col in insp.get_columns("contactos")}

        cols_contactos: Set[str] = await conn.run_sync(get_contactos_cols)
        logger.info("Columnas actuales en 'contactos': %s", cols_contactos)

        if "bot_desactivado" not in cols_contactos:
            logger.info("Agregando columna 'bot_desactivado' a tabla 'contactos'...")
            if is_sqlite:
                await conn.execute(
                    text("ALTER TABLE contactos ADD COLUMN bot_desactivado BOOLEAN DEFAULT 0 NOT NULL")
                )
            else:
                await conn.execute(
                    text("ALTER TABLE contactos ADD COLUMN bot_desactivado BOOLEAN DEFAULT FALSE NOT NULL")
                )

        # 2. Obtener columnas existentes en 'conversaciones'
        def get_conversaciones_cols(sync_conn):
            insp = inspect(sync_conn)
            return {col["name"] for col in insp.get_columns("conversaciones")}

        cols_conv: Set[str] = await conn.run_sync(get_conversaciones_cols)
        logger.info("Columnas actuales en 'conversaciones': %s", cols_conv)

        if "fsm_estado" not in cols_conv:
            logger.info("Agregando columna 'fsm_estado' a tabla 'conversaciones'...")
            await conn.execute(
                text("ALTER TABLE conversaciones ADD COLUMN fsm_estado VARCHAR(50) DEFAULT 'IDLE' NOT NULL")
            )

        if "fsm_contexto" not in cols_conv:
            logger.info("Agregando columna 'fsm_contexto' a tabla 'conversaciones'...")
            if is_sqlite:
                await conn.execute(
                    text("ALTER TABLE conversaciones ADD COLUMN fsm_contexto JSON DEFAULT '{}'")
                )
            else:
                await conn.execute(
                    text("ALTER TABLE conversaciones ADD COLUMN fsm_contexto JSONB DEFAULT '{}'::jsonb")
                )

        if "needs_human_review" not in cols_conv:
            logger.info("Agregando columna 'needs_human_review' a tabla 'conversaciones'...")
            if is_sqlite:
                await conn.execute(
                    text("ALTER TABLE conversaciones ADD COLUMN needs_human_review BOOLEAN DEFAULT 0 NOT NULL")
                )
            else:
                await conn.execute(
                    text("ALTER TABLE conversaciones ADD COLUMN needs_human_review BOOLEAN DEFAULT FALSE NOT NULL")
                )

        if "ultimo_takeover_at" not in cols_conv:
            logger.info("Agregando columna 'ultimo_takeover_at' a tabla 'conversaciones'...")
            await conn.execute(
                text("ALTER TABLE conversaciones ADD COLUMN ultimo_takeover_at DATETIME")
            )

        # 3. Crear índices si no existen
        logger.info("Creando índices para optimizar consultas de FSM y revisión humana...")
        await conn.execute(
            text("CREATE INDEX IF NOT EXISTS idx_conversaciones_fsm_estado ON conversaciones(fsm_estado)")
        )
        await conn.execute(
            text("CREATE INDEX IF NOT EXISTS idx_conversaciones_needs_human_review ON conversaciones(needs_human_review)")
        )

        # 4. Backfill y normalización de registros existentes
        logger.info("Ejecutando backfill de datos preexistentes...")
        await conn.execute(
            text("UPDATE contactos SET bot_desactivado = 0 WHERE bot_desactivado IS NULL")
            if is_sqlite
            else text("UPDATE contactos SET bot_desactivado = FALSE WHERE bot_desactivado IS NULL")
        )
        await conn.execute(
            text("UPDATE conversaciones SET fsm_estado = 'IDLE' WHERE fsm_estado IS NULL OR fsm_estado = ''")
        )
        await conn.execute(
            text("UPDATE conversaciones SET fsm_contexto = '{}' WHERE fsm_contexto IS NULL")
        )
        await conn.execute(
            text("UPDATE conversaciones SET needs_human_review = 0 WHERE needs_human_review IS NULL")
            if is_sqlite
            else text("UPDATE conversaciones SET needs_human_review = FALSE WHERE needs_human_review IS NULL")
        )

        # 5. Sincronizar consorcio_id en conversaciones si el contacto ya posee uno asignado
        logger.info("Sincronizando consorcio_id entre contactos y conversaciones...")
        await conn.execute(
            text(
                """
                UPDATE conversaciones
                SET consorcio_id = (
                    SELECT consorcio_id FROM contactos WHERE contactos.id = conversaciones.contacto_id
                )
                WHERE consorcio_id IS NULL AND contacto_id IN (
                    SELECT id FROM contactos WHERE consorcio_id IS NOT NULL
                )
                """
            )
        )

        # 6. Estadísticas finales
        res_contactos = await conn.execute(text("SELECT count(*) FROM contactos"))
        count_contactos = res_contactos.scalar()

        res_conv = await conn.execute(text("SELECT count(*) FROM conversaciones"))
        count_conv = res_conv.scalar()

        logger.info("Migración completada con éxito.")
        logger.info("Total contactos verificados: %d", count_contactos)
        logger.info("Total conversaciones sincronizadas: %d", count_conv)

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(migrate_and_backfill())
