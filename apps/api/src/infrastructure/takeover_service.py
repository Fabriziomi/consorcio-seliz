import time
from typing import Dict, Optional
from core.config import settings
from core.logging import logger

try:
    import redis.asyncio as redis
except ImportError:
    redis = None


class TakeoverService:
    """
    Gestiona el Takeover Humano (intervención de la administración).
    Cuando un operador humano (Dra. Ivana Seliz) interviene en una conversación,
    el bot inteligente se silencia para ese número durante un período determinado
    (por defecto 12 horas) para no interrumpir la atención personalizada.
    """

    def __init__(self):
        self.default_ttl = 43200
        self._memory_cache: Dict[str, float] = {}
        self._redis_client: Optional[object] = None
        self._redis_available: bool = False

    async def _get_redis(self):
        if not self._redis_available and redis and settings.REDIS_URL:
            try:
                client = redis.from_url(settings.REDIS_URL, decode_responses=True)
                await client.ping()
                self._redis_client = client
                self._redis_available = True
            except Exception as e:
                self._redis_available = False
                logger.debug(f"[TAKEOVER] Redis no disponible en {settings.REDIS_URL}, usando fallback en memoria: {e}")
        return self._redis_client if self._redis_available else None

    def _normalize_key(self, remote_jid_or_phone: str) -> str:
        clean = remote_jid_or_phone.split("@")[0].replace("+", "").strip()
        return f"takeover:{clean}"

    async def set_takeover(self, remote_jid_or_phone: str, duration_seconds: Optional[int] = None) -> bool:
        """Activa el bloqueo de takeover para un número telefónico."""
        key = self._normalize_key(remote_jid_or_phone)
        ttl = duration_seconds or self.default_ttl

        r = await self._get_redis()
        if r:
            try:
                await r.setex(key, ttl, "active")
                logger.info(f"[TAKEOVER] Bloqueo activado en Redis para {key} ({ttl}s)")
                return True
            except Exception as e:
                logger.warning(f"[TAKEOVER] Error en Redis setex, usando memoria: {e}")

        expire_at = time.time() + ttl
        self._memory_cache[key] = expire_at
        logger.info(f"[TAKEOVER] Bloqueo activado en memoria para {key} ({ttl}s)")
        return True

    async def is_takeover_active(self, remote_jid_or_phone: str) -> bool:
        """Verifica si el takeover humano se encuentra activo."""
        key = self._normalize_key(remote_jid_or_phone)

        r = await self._get_redis()
        if r:
            try:
                val = await r.get(key)
                if val:
                    return True
            except Exception as e:
                logger.warning(f"[TAKEOVER] Error en Redis get: {e}")

        expire_at = self._memory_cache.get(key)
        if expire_at:
            if time.time() < expire_at:
                return True
            else:
                del self._memory_cache[key]

        return False

    async def release_takeover(self, remote_jid_or_phone: str) -> bool:
        """Libera el takeover para que el bot pueda responder nuevamente."""
        key = self._normalize_key(remote_jid_or_phone)

        r = await self._get_redis()
        if r:
            try:
                await r.delete(key)
            except Exception as e:
                logger.warning(f"[TAKEOVER] Error al liberar en Redis: {e}")

        if key in self._memory_cache:
            del self._memory_cache[key]

        logger.info(f"[TAKEOVER] Bloqueo liberado para {key}")
        return True

    async def register_bot_message_id(self, message_id: str, ttl: int = 60) -> None:
        """Registra el ID de un mensaje emitido por el bot con TTL de 60s para evitar falso Takeover."""
        if not message_id:
            return
        key = f"bot_msg:{message_id}"
        r = await self._get_redis()
        if r:
            try:
                await r.setex(key, ttl, "1")
                return
            except Exception as e:
                logger.warning(f"[TAKEOVER] Error en Redis setex para bot_msg: {e}")

        self._memory_cache[key] = time.time() + ttl

    async def is_bot_message_id(self, message_id: str) -> bool:
        """Verifica si un ID de mensaje fue emitido por el bot en los últimos 60 segundos."""
        if not message_id:
            return False
        key = f"bot_msg:{message_id}"
        r = await self._get_redis()
        if r:
            try:
                val = await r.get(key)
                if val:
                    return True
            except Exception as e:
                logger.warning(f"[TAKEOVER] Error en Redis get para bot_msg: {e}")

        expire_at = self._memory_cache.get(key)
        if expire_at:
            if time.time() < expire_at:
                return True
            else:
                del self._memory_cache[key]

        return False


takeover_service = TakeoverService()
