import pytest
from httpx import AsyncClient, ASGITransport
from main import app


@pytest.mark.asyncio
async def test_chatwoot_mobile_auth_and_profile():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Sign in compatible con Chatwoot Mobile (Devise Token Auth)
        login_res = await ac.post(
            "/api/v1/auth/sign_in",
            json={
                "email": "admin@selizadministraciones.com.ar",
                "password": "AdminSeliz2026!",
            },
        )
        assert login_res.status_code == 200
        assert "access-token" in login_res.headers
        assert login_res.headers["uid"] == "admin@selizadministraciones.com.ar"
        assert login_res.headers["client"] == "chatwoot-mobile-app"

        body = login_res.json()
        assert "data" in body
        user_data = body["data"]
        assert user_data["email"] == "admin@selizadministraciones.com.ar"
        assert user_data["account_id"] == 1
        assert len(user_data["accounts"]) >= 1

        token = login_res.headers["access-token"]
        auth_headers = {
            "access-token": token,
            "uid": user_data["email"],
            "client": "chatwoot-mobile-app",
        }

        # 2. Get Profile
        profile_res = await ac.get("/api/v1/profile", headers=auth_headers)
        assert profile_res.status_code == 200
        assert profile_res.json()["email"] == "admin@selizadministraciones.com.ar"


@pytest.mark.asyncio
async def test_chatwoot_mobile_conversations_flow():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Auth
        login_res = await ac.post(
            "/api/v1/auth/sign_in",
            json={
                "email": "admin@selizadministraciones.com.ar",
                "password": "AdminSeliz2026!",
            },
        )
        auth_headers = {"access-token": login_res.headers["access-token"]}

        # 1. List conversations (accounts/1/conversations)
        convs_res = await ac.get("/api/v1/accounts/1/conversations", headers=auth_headers)
        assert convs_res.status_code == 200
        convs_data = convs_res.json()
        assert "data" in convs_data
        assert "payload" in convs_data["data"]
        payload = convs_data["data"]["payload"]
        assert len(payload) > 0

        conv_target = payload[0]
        conv_id = conv_target["id"]
        assert "meta" in conv_target
        assert "sender" in conv_target["meta"]

        # 2. List messages for conversation
        msgs_res = await ac.get(f"/api/v1/accounts/1/conversations/{conv_id}/messages", headers=auth_headers)
        assert msgs_res.status_code == 200
        msgs_data = msgs_res.json()
        assert "payload" in msgs_data
        assert len(msgs_data["payload"]) > 0

        # 3. Send message from mobile app
        send_res = await ac.post(
            f"/api/v1/accounts/1/conversations/{conv_id}/messages",
            json={"content": "Mensaje enviado desde la app móvil de Chatwoot.", "private": False},
            headers=auth_headers,
        )
        assert send_res.status_code == 200
        sent_data = send_res.json()
        assert sent_data["content"] == "Mensaje enviado desde la app móvil de Chatwoot."
        assert sent_data["message_type"] == 1  # outgoing

        # 4. Toggle conversation status
        toggle_res = await ac.post(
            f"/api/v1/accounts/1/conversations/{conv_id}/toggle_status",
            json={"status": "resolved"},
            headers=auth_headers,
        )
        assert toggle_res.status_code == 200
        assert toggle_res.json()["payload"]["current_status"] == "resolved"

        # 5. Metadata endpoints: inboxes and agents
        inboxes_res = await ac.get("/api/v1/accounts/1/inboxes", headers=auth_headers)
        assert inboxes_res.status_code == 200
        assert inboxes_res.json()["payload"][0]["channel_type"] == "Channel::Whatsapp"

        agents_res = await ac.get("/api/v1/accounts/1/agents", headers=auth_headers)
        assert agents_res.status_code == 200
        assert len(agents_res.json()["payload"]) >= 1
