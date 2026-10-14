import pytest
import base64
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient, ASGITransport

from main import app
from services.audio_transcriber import audio_transcriber, AudioTranscriber


@pytest.mark.asyncio
async def test_audio_transcriber_empty_base64():
    """Verifica que un audio vacío o inválido no lance excepciones y retorne None."""
    res = await audio_transcriber.transcribe_async("")
    assert res is None

    res_corrupt = await audio_transcriber.transcribe_async("not-a-valid-base64-audio")
    assert res_corrupt is None


@pytest.mark.asyncio
async def test_webhook_evolution_handles_audio_message():
    """
    Verifica que cuando llega un audioMessage de WhatsApp:
    1. Se descarga/recibe el base64.
    2. Whisper lo transcribe a texto.
    3. El mensaje transcripto continúa por el pipeline de decisión y ticket.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        payload = {
            "event": "messages.upsert",
            "data": {
                "key": {
                    "remoteJid": "5491199887766@s.whatsapp.net",
                    "fromMe": False,
                    "id": "MSG-AUDIO-123",
                },
                "pushName": "Santiago Gomez",
                "messageType": "audioMessage",
                "message": {
                    "audioMessage": {
                        "url": "https://mmg.whatsapp.net/v/t62.7114-24/test.ogg",
                        "mimetype": "audio/ogg; codecs=opus",
                        "seconds": 5,
                    },
                    "base64": base64.b64encode(b"RIFFdummydata" * 25).decode("utf-8"),
                },
            },
        }

        # Mockear transcribe_async para simular la transcripción de Whisper
        with patch.object(
            audio_transcriber,
            "transcribe_async",
            new_callable=AsyncMock,
            return_value="Hola soy del 3B de Callao, no me anda el ascensor",
        ) as mock_transcribe:
            with patch("infrastructure.evolution_client.evolution_client.send_text", new_callable=AsyncMock) as mock_send_wa:
                res = await ac.post("/api/v1/webhook/evolution", json=payload)
                assert res.status_code == 200
                assert res.json()["status"] == "received"


@pytest.mark.asyncio
async def test_webhook_evolution_inaudible_audio_prompts_user():
    """
    Verifica que si la nota de voz está inaudible o en blanco,
    el bot responde amablemente solicitando texto y NO crea tickets vacíos.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        payload = {
            "event": "messages.upsert",
            "data": {
                "key": {
                    "remoteJid": "5491122334455@s.whatsapp.net",
                    "fromMe": False,
                    "id": "MSG-AUDIO-SILENT",
                },
                "pushName": "Clara Martinez",
                "messageType": "audioMessage",
                "message": {
                    "audioMessage": {
                        "url": "https://mmg.whatsapp.net/v/t62.7114-24/silent.ogg",
                        "mimetype": "audio/ogg; codecs=opus",
                        "seconds": 3,
                    },
                    "base64": base64.b64encode(b"dummysilentbytes" * 20).decode("utf-8"),
                },
            },
        }

        with patch.object(
            audio_transcriber,
            "transcribe_async",
            new_callable=AsyncMock,
            return_value=None,  # Audio inaudible
        ):
            with patch("infrastructure.evolution_client.evolution_client.send_text", new_callable=AsyncMock) as mock_send_wa:
                mock_send_wa.return_value = True
                res = await ac.post("/api/v1/webhook/evolution", json=payload)
                assert res.status_code == 200

                # Dar un instante para que el BackgroundTask se ejecute
                import asyncio
                await asyncio.sleep(0.3)

                # Verificar que se envió el mensaje solicitando texto
                mock_send_wa.assert_called_once()
                sent_text = mock_send_wa.call_args[0][1]
                assert "no logramos escucharla con claridad" in sent_text
