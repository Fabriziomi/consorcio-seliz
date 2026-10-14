from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from core.logging import logger
from api.v1.webhook_evolution import router as webhook_router
from api.v1.consorcios import router as consorcios_router
from api.v1.tickets import router as tickets_router
from api.v1.debug import router as debug_router
from infrastructure.database import engine, Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"[API_STARTUP] Inicializando base de datos en entorno {settings.ENV}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("[API_STARTUP] Tablas sincronizadas correctamente.")
    yield


app = FastAPI(
    title="Consorcio Seliz — API Central & Gateway",
    description="Backend central y pasarela de orquestación para atención inteligente de consorcios.",
    version="1.0.0",
    lifespan=lifespan,
)

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusión de Routers
app.include_router(webhook_router, prefix="/api/v1", tags=["Webhooks"])
app.include_router(consorcios_router, prefix="/api/v1/consorcios", tags=["Consorcios"])
app.include_router(tickets_router, prefix="/api/v1/tickets", tags=["Tickets"])
app.include_router(debug_router, prefix="/api/v1/debug", tags=["Debug Simulator"])


@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "ok",
        "service": "consorcio_api",
        "env": settings.ENV,
        "fast_debug_mode": settings.FAST_DEBUG_MODE,
    }
