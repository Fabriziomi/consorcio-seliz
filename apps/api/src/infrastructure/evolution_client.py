import httpx
from typing import Optional, Dict, Any
from core.config import settings
from core.logging import logger


class EvolutionClient:
    def __init__(self):
        self.base_url = settings.EVOLUTION_API_URL
        self.api_key = settings.EVOLUTION_API_KEY
        self.instance = settings.EVOLUTION_INSTANCE_NAME

    @property
    def headers(self) -> Dict[str, str]:
        return {
            "apikey": self.api_key,
            "Content-Type": "application/json",
        }

    async def send_text(self, remote_jid: str, text: str) -> bool:
        """Envía un mensaje de texto plano a través de Evolution API v2."""
        url = f"{self.base_url}/message/sendText/{self.instance}"
        payload = {
            "number": remote_jid.split("@")[0],
            "text": text,
        }
        async with httpx.AsyncClient(timeout=settings.HTTP_CLIENT_TIMEOUT) as client:
            try:
                res = await client.post(url, json=payload, headers=self.headers)
                if res.status_code in (200, 201):
                    logger.debug(f"[EVOLUTION_CLIENT] Mensaje enviado exitosamente a {remote_jid}")
                    return True
                logger.error(f"[EVOLUTION_CLIENT] Fallo envío a {remote_jid}: {res.status_code} {res.text}")
            except Exception as e:
                logger.error(f"[EVOLUTION_CLIENT] Error de conexión con Evolution API: {e}")
        return False

    async def set_presence(self, remote_jid: str, presence: str = "composing", delay_ms: int = 1500) -> bool:
        """Simula presencia de digitación (composing) en WhatsApp."""
        url = f"{self.base_url}/chat/sendPresence/{self.instance}"
        payload = {
            "number": remote_jid.split("@")[0],
            "presence": presence,
            "delay": delay_ms,
        }
        async with httpx.AsyncClient(timeout=min(settings.HTTP_CLIENT_TIMEOUT, 30.0)) as client:
            try:
                res = await client.post(url, json=payload, headers=self.headers)
                return res.status_code == 200
            except Exception as e:
                logger.warning(f"[EVOLUTION_CLIENT] No se pudo enviar presencia a {remote_jid}: {e}")
                return False


evolution_client = EvolutionClient()
