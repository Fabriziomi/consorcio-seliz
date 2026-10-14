import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from main import app
from infrastructure.database import Base, get_db
from infrastructure.models import ConsorcioModel, ContactoModel, TicketConsultaModel
from domain.schemas import RolContacto, PrioridadTicket, EstadoTicket

TEST_DB_URL = "sqlite+aiosqlite:///./test_api.db"
test_engine = create_async_engine(TEST_DB_URL, echo=False)
TestSessionLocal = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_db():
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture(autouse=True)
async def setup_test_db():
    app.dependency_overrides[get_db] = override_get_db

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        # Poblar datos para pruebas si no existen
        c1 = await session.get(ConsorcioModel, "cons-corrientes-lavalle")
        if not c1:
            session.add(ConsorcioModel(
                id="cons-corrientes-lavalle",
                nombre="Consorcio Corrientes y Lavalle",
                direccion="Av. Corrientes 1240",
                activo=True
            ))
            session.add(ConsorcioModel(
                id="cons-callao-2334",
                nombre="Consorcio Callao 2334",
                direccion="Av. Callao 2334",
                activo=True
            ))
            session.add(ContactoModel(
                id="cont-1",
                telefono_wa="+5491144558899",
                nombre_completo="Carlos Méndez",
                consorcio_id="cons-corrientes-lavalle",
                unidad_funcional="Torre Corrientes 4° B",
                rol=RolContacto.PROPIETARIO
            ))
            session.add(TicketConsultaModel(
                id="tick-1042",
                contacto_id="cont-1",
                intencion="RECLAMO",
                descripcion="Prueba reclamo",
                prioridad=PrioridadTicket.NORMAL,
                estado=EstadoTicket.EN_REVISION
            ))
            await session.commit()

    yield

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_health_check_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "ok"
        assert data["service"] == "consorcio_api"


@pytest.mark.asyncio
async def test_consorcios_list_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/consorcios/")
        assert res.status_code == 200
        data = res.json()
        assert len(data) >= 2
        nombres = [c["nombre"] for c in data]
        assert any("Corrientes y Lavalle" in n for n in nombres)
        assert any("Callao 2334" in n for n in nombres)


@pytest.mark.asyncio
async def test_tickets_list_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/tickets/")
        assert res.status_code == 200
        data = res.json()
        assert len(data) >= 1
        ticket_ids = [t["id"] for t in data]
        assert "tick-1042" in ticket_ids


@pytest.mark.asyncio
async def test_evolution_webhook_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "event": "messages.upsert",
            "instance": "ivana_seliz_whatsapp",
            "data": {
                "key": {
                    "remoteJid": "5491144558899@s.whatsapp.net",
                    "fromMe": False
                },
                "pushName": "Carlos Méndez",
                "message": {
                    "conversation": "Hola, quería consultar sobre el ascensor"
                }
            }
        }
        res = await client.post("/api/v1/webhook/evolution", json=payload)
        assert res.status_code == 200
        assert res.json()["status"] == "received"


@pytest.mark.asyncio
async def test_debug_chat_endpoint_payment_faq():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "message": "Hola, ¿cuál es el CBU o alias para abonar las expensas?",
            "phone": "+5491144558899",
            "override_schedule": "BOT_ACTIVE_OFF_HOURS"
        }
        res = await client.post("/api/v1/debug/chat", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["should_respond"] is True
        assert data["response_text"] is not None
        assert "CONSORCIO" in data["response_text"] or "CBU" in data["response_text"] or "alias" in data["response_text"].lower()
        assert "total_pipeline_ms" in data


@pytest.mark.asyncio
async def test_debug_chat_endpoint_emergency():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "message": "Urgente, hay olor a gas muy fuerte en el palier y tememos una explosión",
            "phone": "+5491144558899"
        }
        res = await client.post("/api/v1/debug/chat", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["is_emergency"] is True
        assert data["should_respond"] is True
        assert "guardia" in data["response_text"].lower() or "6248-3302" in data["response_text"]
        assert data["ticket_created"] is not None
        assert data["ticket_created"]["prioridad"] == "CRITICA"


@pytest.mark.asyncio
async def test_debug_chat_endpoint_office_hours_silence():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "message": "Hola, una consulta sobre la reunión de consorcio",
            "phone": "+5491144558899",
            "override_schedule": "HUMAN_OFFICE_HOURS"
        }
        res = await client.post("/api/v1/debug/chat", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["should_respond"] is False
        assert data["response_text"] is None
        assert "Horario laboral humano activo" in data["silent_reason"]


@pytest.mark.asyncio
async def test_debug_chat_endpoint_greeting_no_ticket():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "message": "hola",
            "phone": "+5491144558899",
            "override_schedule": "BOT_ACTIVE_OFF_HOURS"
        }
        res = await client.post("/api/v1/debug/chat", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["is_pure_greeting"] is True
        assert data["should_respond"] is True
        assert "Carlos" in data["response_text"]
        assert data["ticket_created"] is None


@pytest.mark.asyncio
async def test_debug_chat_endpoint_noise_silence_no_ticket():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "message": "asd",
            "phone": "+5491144558899",
            "override_schedule": "BOT_ACTIVE_OFF_HOURS"
        }
        res = await client.post("/api/v1/debug/chat", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["is_noise"] is True
        assert data["should_respond"] is False
        assert "Ruido de teclado" in data["silent_reason"]
        assert data["ticket_created"] is None


@pytest.mark.asyncio
async def test_debug_chat_endpoint_burst_consolidation():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload1 = {
            "message": "Se cortó la luz en el palier del 4to piso",
            "phone": "+5491144558899",
            "override_schedule": "BOT_ACTIVE_OFF_HOURS"
        }
        res1 = await client.post("/api/v1/debug/chat", json=payload1)
        assert res1.status_code == 200
        data1 = res1.json()
        assert data1["ticket_created"] is not None
        ticket_id = data1["ticket_created"]["id"]
        assert data1["ticket_created"]["accion"] == "NUEVO_TICKET_CREADO"

        payload2 = {
            "message": "También hay olor a quemado cerca del tablero",
            "phone": "+5491144558899",
            "override_schedule": "BOT_ACTIVE_OFF_HOURS"
        }
        res2 = await client.post("/api/v1/debug/chat", json=payload2)
        assert res2.status_code == 200
        data2 = res2.json()
        assert data2["ticket_created"] is not None
        assert data2["ticket_created"]["id"] == ticket_id
        assert data2["ticket_created"]["accion"] == "CONSOLIDADO_EN_TICKET_EXISTENTE"


@pytest.mark.asyncio
async def test_list_contactos_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/contactos/")
        assert res.status_code == 200
        data = res.json()
        assert len(data) >= 1
        assert data[0]["nombre_completo"] == "Carlos Méndez"
        assert data[0]["consorcio_nombre"] == "Consorcio Corrientes y Lavalle"


@pytest.mark.asyncio
async def test_takeover_endpoints():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        test_phone = "+5491199887766"
        # 1. Chequear status inicial (debe ser inactivo)
        res = await client.get(f"/api/v1/takeover/{test_phone}/status")
        assert res.status_code == 200
        assert res.json()["takeover_active"] is False

        # 2. Activar bloqueo (lock)
        res_lock = await client.post(f"/api/v1/takeover/{test_phone}/lock?duration_seconds=3600")
        assert res_lock.status_code == 200
        assert res_lock.json()["takeover_active"] is True

        # 3. Verificar que ahora está activo
        res_status = await client.get(f"/api/v1/takeover/{test_phone}/status")
        assert res_status.status_code == 200
        assert res_status.json()["takeover_active"] is True

        # 4. Liberar bloqueo (release)
        res_release = await client.post(f"/api/v1/takeover/{test_phone}/release")
        assert res_release.status_code == 200
        assert res_release.json()["takeover_active"] is False

        # 5. Verificar que vuelve a estar inactivo
        res_final = await client.get(f"/api/v1/takeover/{test_phone}/status")
        assert res_final.status_code == 200
        assert res_final.json()["takeover_active"] is False


@pytest.mark.asyncio
async def test_webhook_evolution_from_me_activates_takeover():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        target_phone = "5491122334455"
        payload = {
            "event": "messages.upsert",
            "data": {
                "key": {
                    "remoteJid": f"{target_phone}@s.whatsapp.net",
                    "fromMe": True,
                    "id": "MSG-IVANA-001"
                },
                "pushName": "Ivana Seliz",
                "message": {
                    "conversation": "Hola, ya me encargo personalmente del tema."
                }
            }
        }
        res = await client.post("/api/v1/webhook/evolution", json=payload)
        assert res.status_code == 200
        assert res.json()["status"] == "received"

        # Verificar que el takeover para este teléfono se activó
        status_res = await client.get(f"/api/v1/takeover/{target_phone}/status")
        assert status_res.status_code == 200
        assert status_res.json()["takeover_active"] is True


@pytest.mark.asyncio
async def test_webhook_chatwoot_operator_message():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        target_phone = "5491177665544"
        payload = {
            "event": "message_created",
            "message_type": "outgoing",
            "private": False,
            "content": "Estimado vecino, enviamos técnico mañana.",
            "conversation": {
                "meta": {
                    "sender": {
                        "phone_number": f"+{target_phone}"
                    }
                }
            }
        }
        res = await client.post("/api/v1/webhook/chatwoot", json=payload)
        assert res.status_code == 200
        assert res.json()["status"] == "received"

        # El background task activa el takeover
        status_res = await client.get(f"/api/v1/takeover/{target_phone}/status")
        assert status_res.status_code == 200
        assert status_res.json()["takeover_active"] is True

