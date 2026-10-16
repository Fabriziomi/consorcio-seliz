import asyncio
import random
import httpx
from typing import Optional, Dict, Any
from core.config import settings
from core.logging import logger


def calculate_human_typing_delay(
    text: str,
    min_seconds: float = 1.3,
    max_seconds: float = 4.2,
    base_chars_per_sec: float = 35.0,
    bypass_in_debug: bool = True,
) -> float:
    """
    Calcula un retardo de tipeo humano dinámico, proporcional a la longitud del texto
    pero con aleatoriedad (jitter) para quebrar patrones consistentes y evitar bloqueos de WhatsApp.

    - Velocidad base: ~30-40 caracteres por segundo (tps/s).
    - Piso mínimo: garantiza que incluso respuestas cortas simulen lectura y digitación humana (min 1.3s).
    - Techo máximo: acota respuestas largas para no demorar la atención al vecino (max 4.2s).
    - Jitter aleatorio: agrega variación no determinista (-0.30s a +0.45s) en cada ejecución.
    - Modo debug/testing: si FAST_DEBUG_MODE o DISABLE_RANDOM_JITTER están activos, retorna 0.0s.
    """
    if bypass_in_debug and (getattr(settings, "FAST_DEBUG_MODE", False) or getattr(settings, "DISABLE_RANDOM_JITTER", False)):
        return 0.0

    length = len(text.strip()) if text else 0

    # Piso mínimo dinámico con jitter (garantiza siempre >= min_seconds, con variación de 0.02s a 0.35s)
    min_floor = min_seconds + random.uniform(0.02, 0.35)
    # Techo máximo dinámico con jitter
    max_ceiling = max_seconds + random.uniform(-0.10, 0.25)

    # Velocidad de digitación ágil (28 a 42 caracteres por segundo)
    effective_cps = random.uniform(base_chars_per_sec * 0.85, base_chars_per_sec * 1.15)
    calculated_time = (length / effective_cps) if length > 0 else 0.0

    # Jitter aleatorio de tipeo
    jitter = random.uniform(-0.25, 0.35)
    total_delay = calculated_time + jitter

    # Acotación dinámica
    clamped_delay = max(min_floor, min(total_delay, max_ceiling))
    return round(clamped_delay, 2)


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
                    try:
                        data = res.json()
                        msg_id = data.get("key", {}).get("id") or data.get("id")
                        if msg_id:
                            from infrastructure.takeover_service import takeover_service
                            await takeover_service.register_bot_message_id(msg_id)
                    except Exception:
                        pass
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

    async def send_text_with_typing(
        self,
        remote_jid: str,
        text: str,
        min_seconds: float = 1.3,
        max_seconds: float = 4.2,
        base_chars_per_sec: float = 35.0,
    ) -> bool:
        """
        Emite presencia 'composing' con retardo dinámico anti-ban calculado según
        la longitud del texto, respetando un piso mínimo y agregando variación aleatoria (jitter).
        """
        delay = calculate_human_typing_delay(
            text,
            min_seconds=min_seconds,
            max_seconds=max_seconds,
            base_chars_per_sec=base_chars_per_sec,
        )

        if delay > 0:
            delay_ms = int(delay * 1000)
            logger.info(
                f"[ANTI_BAN] Simulando tipeo humano para {remote_jid}: {delay}s ({len(text)} caracteres)"
            )
            await self.set_presence(remote_jid, presence="composing", delay_ms=delay_ms)
            await asyncio.sleep(delay)

        return await self.send_text(remote_jid, text)

    async def get_media_base64(self, message_dict: dict) -> Optional[str]:
        """Obtiene el contenido en base64 de un mensaje multimedia (ej. audioMessage) desde Evolution API v2."""
        url = f"{self.base_url}/chat/getBase64FromMediaMessage/{self.instance}"
        payload = {
            "message": message_dict,
            "convertToMp3": False,
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                res = await client.post(url, json=payload, headers=self.headers)
                if res.status_code in (200, 201):
                    data = res.json()
                    b64 = data.get("base64")
                    if b64:
                        if "," in b64:
                            b64 = b64.split(",", 1)[1]
                        return b64
                logger.warning(f"[EVOLUTION_CLIENT] Fallo al obtener base64 de audio: {res.status_code} {res.text[:100]}")
            except Exception as e:
                logger.error(f"[EVOLUTION_CLIENT] Error al solicitar base64 a Evolution API: {e}")
        return None

    async def fetch_profile_picture_url(self, phone: str) -> Optional[str]:
        """Obtiene la URL original de la foto de perfil del contacto desde Evolution API."""
        url = f"{self.base_url}/chat/fetchProfilePictureUrl/{self.instance}"
        clean_num = phone.split("@")[0].replace("+", "").strip()
        payload = {"number": clean_num}
        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                res = await client.post(url, json=payload, headers=self.headers)
                if res.status_code in (200, 201):
                    data = res.json()
                    return data.get("profilePictureUrl") or data.get("picture")
            except Exception as e:
                logger.debug(f"[EVOLUTION_CLIENT] No se pudo obtener foto de perfil para {phone}: {e}")
        return None


evolution_client = EvolutionClient()

