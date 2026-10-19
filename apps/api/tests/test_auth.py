import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from main import app
from infrastructure.database import Base, get_db
from infrastructure.models import UsuarioModel
from domain.schemas import RolUsuario
from core.security import hash_password

TEST_AUTH_DB = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(TEST_AUTH_DB, echo=False)
TestSession = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_db():
    async with TestSession() as session:
        yield session


@pytest_asyncio.fixture(autouse=True)
async def setup_auth_db():
    app.dependency_overrides[get_db] = override_get_db

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with TestSession() as session:
        admin_user = UsuarioModel(
            id="user-admin-seliz",
            email="admin@selizadministraciones.com.ar",
            password_hash=hash_password("AdminSeliz2026!"),
            nombre_completo="Dra. Ivana Seliz",
            rol=RolUsuario.SUPER_ADMIN,
            activo=True,
        )
        session.add(admin_user)
        await session.commit()

    yield

    app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_auth_login_success():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/auth/login",
            json={"email": "admin@selizadministraciones.com.ar", "password": "AdminSeliz2026!"},
        )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "admin@selizadministraciones.com.ar"
    assert data["user"]["rol"] == "SUPER_ADMIN"


@pytest.mark.asyncio
async def test_auth_login_invalid_password():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/auth/login",
            json={"email": "admin@selizadministraciones.com.ar", "password": "PasswordIncorrecta!"},
        )
    assert response.status_code == 401
    assert "incorrectos" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_auth_login_nonexistent_user():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/auth/login",
            json={"email": "noexiste@seliz.com", "password": "Cualquiera123!"},
        )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_auth_get_me_flow():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Sin token
        no_auth = await ac.get("/api/v1/auth/me")
        assert no_auth.status_code == 401

        # 2. Login para obtener token
        login_res = await ac.post(
            "/api/v1/auth/login",
            json={"email": "admin@selizadministraciones.com.ar", "password": "AdminSeliz2026!"},
        )
        token = login_res.json()["access_token"]

        # 3. Consulta /me con token
        me_res = await ac.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert me_res.status_code == 200
        me_data = me_res.json()
        assert me_data["email"] == "admin@selizadministraciones.com.ar"
        assert me_data["nombre_completo"] == "Dra. Ivana Seliz"


@pytest.mark.asyncio
async def test_auth_create_operator_user():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Login de admin
        login_res = await ac.post(
            "/api/v1/auth/login",
            json={"email": "admin@selizadministraciones.com.ar", "password": "AdminSeliz2026!"},
        )
        token = login_res.json()["access_token"]

        # Crear nuevo operador
        new_user = {
            "email": "auxiliar.nocturno@seliz.com",
            "password": "Auxiliar2026!",
            "nombre_completo": "Luciano Guarda Nocturna",
            "rol": "OPERADOR",
            "activo": True,
        }
        res = await ac.post(
            "/api/v1/auth/usuarios",
            json=new_user,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 201
        created = res.json()
        assert created["email"] == "auxiliar.nocturno@seliz.com"
        assert created["rol"] == "OPERADOR"

        # Login con el nuevo operador
        op_login = await ac.post(
            "/api/v1/auth/login",
            json={"email": "auxiliar.nocturno@seliz.com", "password": "Auxiliar2026!"},
        )
        assert op_login.status_code == 200
        assert op_login.json()["user"]["rol"] == "OPERADOR"


@pytest.mark.asyncio
async def test_auth_pin_two_factor_flow():
    """Verifica el flujo completo de autenticación de dos factores con PIN de 6 dígitos."""
    # 1. Configurar un usuario con contraseña y PIN
    async with TestSession() as session:
        user_with_pin = UsuarioModel(
            id="user-pin-test",
            email="pin.test@selizadministraciones.com.ar",
            password_hash=hash_password("PinPass2026!"),
            pin_hash=hash_password("654321"),
            nombre_completo="Usuario con PIN",
            rol=RolUsuario.ADMINISTRADOR,
            activo=True,
        )
        session.add(user_with_pin)
        await session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 2. Paso 1: Ingreso sin PIN -> Debe responder desafío con requires_pin=True y temp_token
        res_step1 = await ac.post(
            "/api/v1/auth/login",
            json={"email": "pin.test@selizadministraciones.com.ar", "password": "PinPass2026!"},
        )
        assert res_step1.status_code == 200
        data1 = res_step1.json()
        assert data1["requires_pin"] is True
        assert "temp_token" in data1
        temp_token = data1["temp_token"]

        # 3. Paso 2 con PIN erróneo -> 401
        res_bad_pin = await ac.post(
            "/api/v1/auth/verify-pin",
            json={"temp_token": temp_token, "pin": "000000"},
        )
        assert res_bad_pin.status_code == 401
        assert "incorrecto" in res_bad_pin.json()["detail"].lower()

        # 4. Paso 2 con PIN correcto -> 200 y access_token emitido
        res_good_pin = await ac.post(
            "/api/v1/auth/verify-pin",
            json={"temp_token": temp_token, "pin": "654321"},
        )
        assert res_good_pin.status_code == 200
        data_final = res_good_pin.json()
        assert "access_token" in data_final
        assert data_final["token_type"] == "bearer"
        assert data_final["user"]["email"] == "pin.test@selizadministraciones.com.ar"


@pytest.mark.asyncio
async def test_auth_login_with_direct_pin():
    """Verifica que si el cliente envía directamente email, contraseña y PIN, la autenticación es inmediata."""
    async with TestSession() as session:
        user_direct = UsuarioModel(
            id="user-direct-pin",
            email="direct.pin@selizadministraciones.com.ar",
            password_hash=hash_password("DirectPass2026!"),
            pin_hash=hash_password("998877"),
            nombre_completo="Usuario Directo",
            rol=RolUsuario.ADMINISTRADOR,
            activo=True,
        )
        session.add(user_direct)
        await session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # PIN incorrecto en request directo
        bad_direct = await ac.post(
            "/api/v1/auth/login",
            json={
                "email": "direct.pin@selizadministraciones.com.ar",
                "password": "DirectPass2026!",
                "pin": "111111",
            },
        )
        assert bad_direct.status_code == 401

        # PIN correcto en request directo
        ok_direct = await ac.post(
            "/api/v1/auth/login",
            json={
                "email": "direct.pin@selizadministraciones.com.ar",
                "password": "DirectPass2026!",
                "pin": "998877",
            },
        )
        assert ok_direct.status_code == 200
        assert "access_token" in ok_direct.json()
