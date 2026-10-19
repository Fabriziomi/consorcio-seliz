import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from main import app
from infrastructure.database import Base, get_db
from infrastructure.models import ConsorcioModel, ContactoModel, TicketConsultaModel, ExpedienteIncidenciaModel, UsuarioModel
from domain.schemas import RolContacto, PrioridadTicket, EstadoTicket, EstadoExpediente, CategoriaIncidencia, RolUsuario
from api.deps import get_current_user

mock_admin = UsuarioModel(
    id="user-mock-admin-exp",
    email="admin.exp@seliz.com",
    nombre_completo="Admin Expedientes",
    rol=RolUsuario.SUPER_ADMIN,
    activo=True,
)


async def override_get_current_user():
    return mock_admin


TEST_DB_URL = "sqlite+aiosqlite:///./test_expedientes.db"
test_engine = create_async_engine(TEST_DB_URL, echo=False)
TestSessionLocal = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_db():
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture(autouse=True)
async def setup_test_db(monkeypatch):
    import infrastructure.database as db_mod
    import api.v1.webhook_evolution as webhook_mod

    monkeypatch.setattr(db_mod, "AsyncSessionLocal", TestSessionLocal)
    monkeypatch.setattr(webhook_mod, "AsyncSessionLocal", TestSessionLocal)

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        c1 = ConsorcioModel(
            id="cons-callao-2334",
            nombre="Consorcio Callao 2334",
            direccion="Av. Callao 2334, Recoleta",
            activo=True,
        )
        cont1 = ContactoModel(
            id="cont-lucia",
            telefono_wa="+5491166778899",
            nombre_completo="Lucía Rossi",
            consorcio_id="cons-callao-2334",
            unidad_funcional="7° A",
            rol=RolContacto.INQUILINO,
        )
        cont2 = ContactoModel(
            id="cont-marcos",
            telefono_wa="+5491122334455",
            nombre_completo="Marcos Paz",
            consorcio_id="cons-callao-2334",
            unidad_funcional="3° B",
            rol=RolContacto.PROPIETARIO,
        )
        session.add_all([c1, cont1, cont2])
        await session.commit()

    yield

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_and_list_expediente():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Crear expediente
        payload = {
            "consorcio_id": "cons-callao-2334",
            "titulo": "Ascensor principal fuera de servicio",
            "categoria": "ASCENSORES",
            "prioridad": "ALTA",
            "estado": "ABIERTO",
            "descripcion_consolidada": "Avería reportada en botonera y freno",
            "proveedor_asignado": "Otis Mantenimiento",
        }
        res = await client.post("/api/v1/expedientes/", json=payload)
        assert res.status_code == 201
        data = res.json()
        assert data["codigo"].startswith("EXP-")
        assert data["titulo"] == "Ascensor principal fuera de servicio"
        exp_id = data["id"]

        # 2. Listar expedientes
        list_res = await client.get("/api/v1/expedientes/")
        assert list_res.status_code == 200
        items = list_res.json()
        assert len(items) >= 1
        assert any(e["id"] == exp_id for e in items)

        # 3. Filtrar por estado
        filtered = await client.get("/api/v1/expedientes/?estado=ABIERTO")
        assert filtered.status_code == 200
        assert len(filtered.json()) >= 1


@pytest.mark.asyncio
async def test_update_expediente_status_to_resolved():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Crear expediente inicial
        payload = {
            "consorcio_id": "cons-callao-2334",
            "titulo": "Pérdida de agua en sala de calderas",
            "categoria": "PLOMERIA",
            "prioridad": "CRITICA",
            "estado": "ABIERTO",
            "descripcion_consolidada": "Agua acumulada en subsuelo",
        }
        c_res = await client.post("/api/v1/expedientes/", json=payload)
        exp_id = c_res.json()["id"]

        # Actualizar a EN_CURSO
        patch1 = await client.patch(f"/api/v1/expedientes/{exp_id}", json={"estado": "EN_CURSO"})
        assert patch1.status_code == 200
        assert patch1.json()["estado"] == "EN_CURSO"
        assert patch1.json()["resuelto_el"] is None

        # Resolver
        patch2 = await client.patch(f"/api/v1/expedientes/{exp_id}", json={"estado": "RESUELTO"})
        assert patch2.status_code == 200
        assert patch2.json()["estado"] == "RESUELTO"
        assert patch2.json()["resuelto_el"] is not None


@pytest.mark.asyncio
async def test_automatic_expediente_grouping_prevents_duplicate_reports():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Vecina 1 reporta ascensor roto
        p1 = {
            "message": "Hola, se trabó el ascensor en el piso 7 y no baja",
            "phone": "+5491166778899",
            "override_schedule": "BOT_ACTIVE_OFF_HOURS",
        }
        res1 = await client.post("/api/v1/debug/chat", json=p1)
        assert res1.status_code == 200
        t1 = res1.json()["ticket_created"]
        assert t1 is not None
        assert t1["accion"] == "NUEVO_TICKET_CREADO"
        assert t1["expediente_id"] is not None
        first_exp_id = t1["expediente_id"]

        # Vecino 2 del mismo edificio reporta la misma falla en el ascensor
        p2 = {
            "message": "El ascensor principal no funciona, hace un ruido raro",
            "phone": "+5491122334455",
            "override_schedule": "BOT_ACTIVE_OFF_HOURS",
        }
        res2 = await client.post("/api/v1/debug/chat", json=p2)
        assert res2.status_code == 200
        t2 = res2.json()["ticket_created"]
        assert t2 is not None
        # Ambos tickets se agrupan bajo el MISMO expediente sin duplicar el caso edilicio
        assert t2["expediente_id"] == first_exp_id

        # Verificar detalle del expediente consolidado
        detail_res = await client.get(f"/api/v1/expedientes/{first_exp_id}")
        assert detail_res.status_code == 200
        exp_data = detail_res.json()
        assert exp_data["id"] == first_exp_id
        assert len(exp_data["tickets"]) == 2
        # Verificar que la descripción consolidada contiene ambos reportes
        assert "Lucía Rossi" in exp_data["descripcion_consolidada"]
        assert "Marcos Paz" in exp_data["descripcion_consolidada"]
