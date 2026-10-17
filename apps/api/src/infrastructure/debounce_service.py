import asyncio
import time
from typing import Dict, List, Callable, Awaitable, Optional
from core.config import settings
from core.logging import logger


class DebounceBufferService:
    """
    Consolidador de ráfagas de mensajes (Debounce Buffer).
    Evita responder múltiples veces cuando el vecino envía oraciones fragmentadas en pocos segundos.
    Agrupa los mensajes de un mismo remitente durante un intervalo (ej. 4-6 segundos)
    antes de ejecutar la evaluación del LangGraph engine.
    """

    def __init__(self, window_seconds: float = 4.0):
        self.window_seconds = window_seconds
        self._buffers: Dict[str, List[str]] = {}
        self._tasks: Dict[str, asyncio.Task] = {}

    async def add_message(
        self,
        key: str,
        message_text: str,
        callback: Callable[[str, str], Awaitable[None]]
    ):
        """
        Agrega un mensaje al buffer del remitente. Si ya hay un timer corriendo, lo extiende.
        Al finalizar la ventana, invoca el callback con el texto consolidado.
        """
        if settings.BYPASS_DEBOUNCE_BUFFER or settings.FAST_DEBUG_MODE:
            await callback(key, message_text)
            return

        if key not in self._buffers:
            self._buffers[key] = []

        self._buffers[key].append(message_text.strip())

        if key in self._tasks and not self._tasks[key].done():
            self._tasks[key].cancel()

        async def _delayed_flush():
            try:
                await asyncio.sleep(self.window_seconds)
                messages = self._buffers.pop(key, [])
                self._tasks.pop(key, None)
                if messages:
                    consolidated = "\n".join(messages)
                    logger.info(f"[DEBOUNCE] Consolidando {len(messages)} mensaje(s) para {key}: '{consolidated}'")
                    await callback(key, consolidated)
            except asyncio.CancelledError:
                pass
            except Exception as e:
                logger.error(f"[DEBOUNCE] Error al procesar buffer diferido para {key}: {e}")

        self._tasks[key] = asyncio.create_task(_delayed_flush())


debounce_service = DebounceBufferService()
