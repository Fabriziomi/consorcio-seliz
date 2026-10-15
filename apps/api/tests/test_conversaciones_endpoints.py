import pytest
from httpx import AsyncClient, ASGITransport
from main import app
from core.security import create_access_token


@pytest.fixture
def auth_headers():
    token = create_access_token({"sub": "user-admin-seliz", "email": "admin@selizadministraciones.com.ar", "rol": "SUPER_ADMIN"})
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_faqs_crud(auth_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Crear FAQ
        create_res = await ac.post(
            "/api/v1/faqs",
            json={
                "pregunta": "¿Cómo solicitar una llave de entrada?",
                "respuesta_oficial": "Debe solicitarla al encargado mediante nota firmada.",
                "activo": True,
            },
            headers=auth_headers,
        )
        assert create_res.status_code == 201
        faq_data = create_res.json()
        faq_id = faq_data["id"]
        assert faq_data["pregunta"] == "¿Cómo solicitar una llave de entrada?"

        # 2. Listar FAQs
        list_res = await ac.get("/api/v1/faqs", headers=auth_headers)
        assert list_res.status_code == 200
        faqs = list_res.json()
        assert any(f["id"] == faq_id for f in faqs)

        # 3. Actualizar FAQ
        update_res = await ac.put(
            f"/api/v1/faqs/{faq_id}",
            json={"respuesta_oficial": "Debe solicitarla al encargado con 24 hs de anticipación."},
            headers=auth_headers,
        )
        assert update_res.status_code == 200
        assert update_res.json()["respuesta_oficial"] == "Debe solicitarla al encargado con 24 hs de anticipación."

        # 4. Toggle activo
        toggle_res = await ac.patch(f"/api/v1/faqs/{faq_id}/toggle", headers=auth_headers)
        assert toggle_res.status_code == 200
        assert toggle_res.json()["activo"] is False

        # 5. Eliminar FAQ
        del_res = await ac.delete(f"/api/v1/faqs/{faq_id}", headers=auth_headers)
        assert del_res.status_code == 204


@pytest.mark.asyncio
async def test_consorcios_and_atributos(auth_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Listar consorcios
        list_res = await ac.get("/api/v1/consorcios", headers=auth_headers)
        assert list_res.status_code == 200
        consorcios = list_res.json()
        assert len(consorcios) > 0
        cid = consorcios[0]["id"]

        # 2. Actualizar consorcio
        up_res = await ac.put(
            f"/api/v1/consorcios/{cid}",
            json={"pautas_mudanza": "Lunes a viernes de 8 a 16 hs."},
            headers=auth_headers,
        )
        assert up_res.status_code == 200
        assert up_res.json()["pautas_mudanza"] == "Lunes a viernes de 8 a 16 hs."

        # 3. Crear atributo dinámico
        attr_res = await ac.post(
            f"/api/v1/consorcios/{cid}/atributos",
            json={
                "clave": "clave_wifi_sum",
                "etiqueta_visible": "Wi-Fi SUM",
                "valor": "SelizSum2026",
                "es_publico_vecinos": True,
            },
            headers=auth_headers,
        )
        assert attr_res.status_code == 201
        attr_id = attr_res.json()["id"]

        # 4. Listar atributos
        attrs_list = await ac.get(f"/api/v1/consorcios/{cid}/atributos", headers=auth_headers)
        assert attrs_list.status_code == 200
        assert any(a["id"] == attr_id for a in attrs_list.json())

        # 5. Eliminar atributo
        del_attr = await ac.delete(f"/api/v1/consorcios/{cid}/atributos/{attr_id}", headers=auth_headers)
        assert del_attr.status_code == 204


@pytest.mark.asyncio
async def test_conversaciones_flow(auth_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        import uuid
        phone = f"+54911{uuid.uuid4().hex[:8]}"
        # 1. Crear un contacto de prueba
        cont_res = await ac.post(
            "/api/v1/contactos",
            json={
                "telefono_wa": phone,
                "nombre_completo": "Test Vecino",
                "unidad_funcional": "5° B",
                "rol": "PROPIETARIO",
            },
            headers=auth_headers,
        )
        assert cont_res.status_code == 201
        contact_id = cont_res.json()["id"]

        # 2. Crear conversación
        conv_res = await ac.post(
            "/api/v1/conversaciones",
            json={"contacto_id": contact_id, "etiquetas": ["TEST"]},
            headers=auth_headers,
        )
        assert conv_res.status_code == 201
        conv_id = conv_res.json()["id"]
        assert conv_res.json()["contacto_nombre"] == "Test Vecino"

        # 3. Enviar nota interna privada
        note_res = await ac.post(
            f"/api/v1/conversaciones/{conv_id}/messages",
            json={"contenido": "Nota interna de prueba del operador.", "privado": True},
            headers=auth_headers,
        )
        assert note_res.status_code == 201
        assert note_res.json()["privado"] is True

        # 4. Enviar mensaje público al vecino
        msg_res = await ac.post(
            f"/api/v1/conversaciones/{conv_id}/messages",
            json={"contenido": "Estimado vecino, confirmamos recepción de su consulta.", "privado": False},
            headers=auth_headers,
        )
        assert msg_res.status_code == 201
        assert msg_res.json()["privado"] is False

        # 5. Obtener detalle de conversación con mensajes
        detail_res = await ac.get(f"/api/v1/conversaciones/{conv_id}", headers=auth_headers)
        assert detail_res.status_code == 200
        detail = detail_res.json()
        assert len(detail["mensajes"]) >= 2

        # 6. Cambiar estado a RESUELTO
        status_res = await ac.patch(
            f"/api/v1/conversaciones/{conv_id}/status?nuevo_estado=resolved",
            headers=auth_headers,
        )
        assert status_res.status_code == 200
        assert status_res.json()["estado"] == "resolved"

        # 7. Asignar etiquetas
        lbl_res = await ac.post(
            f"/api/v1/conversaciones/{conv_id}/labels",
            json=["URGENTE", "EXPENSAS"],
            headers=auth_headers,
        )
        assert lbl_res.status_code == 200
        assert "URGENTE" in lbl_res.json()["etiquetas"]
