import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from core.logging import logger
from api.v1.webhook_evolution import router as webhook_router
from api.v1.consorcios import router as consorcios_router
from api.v1.contactos import router as contactos_router
from api.v1.tickets import router as tickets_router
from api.v1.expedientes import router as expedientes_router
from api.v1.auth import router as auth_router
from api.v1.debug import router as debug_router
from api.v1.conversaciones import router as conversaciones_router
from api.v1.faqs import router as faqs_router
from api.v1.chatwoot_compat import router as chatwoot_compat_router
from api.v1.ws import router as ws_router
from infrastructure.database import engine, Base, AsyncSessionLocal
from infrastructure.seed import seed_initial_data


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"[API_STARTUP] Inicializando base de datos en entorno {settings.ENV}")
    connected = False
    for attempt in range(1, 15):
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            connected = True
            logger.info("[API_STARTUP] Tablas sincronizadas correctamente.")
            break
        except Exception as e:
            logger.warning(f"[API_STARTUP] Intento {attempt}/14 de conexión a BD falló: {e}. Reintentando en 2s...")
            await asyncio.sleep(2)

    if not connected:
        logger.error("[API_STARTUP] Imposible conectar a la base de datos tras múltiples intentos.")
        raise RuntimeError("Fallo de conexión persistente con la base de datos PostgreSQL")

    async with AsyncSessionLocal() as session:
        try:
            await seed_initial_data(session)
        except Exception as e:
            logger.warning(f"[API_STARTUP] Error al sembrar datos iniciales: {e}")

    try:
        from services.templates import validate_templates_on_startup
        validate_templates_on_startup()
        logger.info("[API_STARTUP] Plantillas FSM verificadas exitosamente.")
    except Exception as e:
        logger.error(f"[API_STARTUP] Error al validar plantillas: {e}")
        raise e

    yield


app = FastAPI(
    title="Consorcio Seliz — API Central & Gateway",
    description="Backend central y pasarela de orquestación para atención inteligente de consorcios.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["access-token", "uid", "client", "expiry", "token-type"],
)

app.include_router(webhook_router, prefix="/api/v1", tags=["Webhooks"])
app.include_router(auth_router, prefix="/api/v1/auth", tags=["Autenticación"])
app.include_router(chatwoot_compat_router, prefix="/api/v1", tags=["Chatwoot Mobile Compatibility"])
app.include_router(consorcios_router, prefix="/api/v1/consorcios", tags=["Consorcios"])
app.include_router(contactos_router, prefix="/api/v1/contactos", tags=["Contactos"])
app.include_router(tickets_router, prefix="/api/v1/tickets", tags=["Tickets"])
app.include_router(expedientes_router, prefix="/api/v1/expedientes", tags=["Expedientes"])
app.include_router(conversaciones_router, prefix="/api/v1/conversaciones", tags=["Conversaciones & Inbox"])
app.include_router(faqs_router, prefix="/api/v1/faqs", tags=["Base de Conocimiento & FAQs"])
app.include_router(debug_router, prefix="/api/v1/debug", tags=["Debug Simulator"])
app.include_router(ws_router, tags=["WebSockets"])


@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "ok",
        "service": "consorcio_api",
        "env": settings.ENV,
        "fast_debug_mode": settings.FAST_DEBUG_MODE,
    }
