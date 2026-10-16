import os
import base64
import tempfile
import threading
import asyncio
import logging
from typing import Optional
import httpx

from core.config import settings

logger = logging.getLogger(__name__)

try:
    from faster_whisper import WhisperModel
    HAS_FASTER_WHISPER = True
except ImportError:
    HAS_FASTER_WHISPER = False


class AudioTranscriber:
    """
    Servicio de transcripción Speech-to-Text para notas de voz de WhatsApp.
    Prioridad: Groq Whisper API (whisper-large-v3-turbo) con latencia < 350 ms.
    Fallback: faster-whisper local (modo CPU INT8) si Groq no está disponible.
    """

    def __init__(self, model_size: str = "tiny", device: str = "cpu", compute_type: str = "int8"):
        self.groq_api_key = settings.GROQ_API_KEY or getattr(settings, "GROQ_KEY", None)
        self.groq_url = "https://api.groq.com/openai/v1/audio/transcriptions"
        self.audio_timeout = float(settings.AUDIO_TIMEOUT_SECONDS)
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self._model: Optional[WhisperModel] = None
        self._init_lock = threading.Lock()
        self._transcribe_lock = threading.Lock()
        self._download_root = os.path.join(os.getcwd(), "models", "whisper")

    async def transcribe_async(self, base64_str: str) -> Optional[str]:
        """
        Transcribe audio en Base64.
        Intenta primero Groq API (whisper-large-v3-turbo) con timeout de 3s.
        Si falla o no hay clave, conmuta a fallback local.
        """
        if not base64_str or not isinstance(base64_str, str):
            return None

        clean_b64 = base64_str.split(",", 1)[1] if "," in base64_str else base64_str

        try:
            audio_bytes = base64.b64decode(clean_b64)
        except Exception as e:
            logger.warning("[AUDIO_TRANSCRIBER] Error al decodificar Base64 de audio: %s", e)
            return None

        if len(audio_bytes) < 200:
            logger.warning("[AUDIO_TRANSCRIBER] Audio demasiado corto o vacío.")
            return None

        # Límite aproximado: 90 segundos de audio Opus PTT ronda ~300KB
        if len(audio_bytes) > 350_000:
            logger.warning("[AUDIO_TRANSCRIBER] Audio excede los 90 segundos máximos permitidos (%d bytes).", len(audio_bytes))
            return None

        # 1. Intentar Groq Whisper API si hay clave configurada
        groq_key = self.groq_api_key or settings.GROQ_API_KEY or getattr(settings, "GROQ_KEY", None)
        if groq_key:
            groq_text = await self._transcribe_groq(audio_bytes, api_key=groq_key)
            if groq_text is not None:
                return groq_text

        # 2. Fallback a modelo local si está disponible
        return await asyncio.to_thread(self._transcribe_local, audio_bytes)

    async def _transcribe_groq(self, audio_bytes: bytes, api_key: str) -> Optional[str]:
        headers = {
            "Authorization": f"Bearer {api_key}",
        }
        files = {
            "file": ("audio.ogg", audio_bytes, "audio/ogg"),
        }
        data = {
            "model": "whisper-large-v3-turbo",
            "language": "es",
            "temperature": "0.0",
            "response_format": "json",
        }

        try:
            async with httpx.AsyncClient(timeout=self.audio_timeout) as client:
                res = await client.post(self.groq_url, headers=headers, files=files, data=data)
            if res.status_code == 200:
                result_json = res.json()
                text = (result_json.get("text") or "").strip()
                if len(text) >= 3:
                    logger.info("[AUDIO_TRANSCRIBER] Transcripción Groq exitosa: '%s'", text)
                    return text
                else:
                    logger.info("[AUDIO_TRANSCRIBER] Transcripción Groq devolvió menos de 3 caracteres.")
                    return None
            else:
                logger.warning("[AUDIO_TRANSCRIBER] Error HTTP Groq %d: %s", res.status_code, res.text)
        except Exception as exc:
            logger.warning("[AUDIO_TRANSCRIBER] Fallo o timeout al consultar Groq API (%s). Pasando a fallback.", exc)

        return None

    def _get_local_model(self) -> Optional[WhisperModel]:
        if self._model is None and HAS_FASTER_WHISPER:
            with self._init_lock:
                if self._model is None:
                    try:
                        os.makedirs(self._download_root, exist_ok=True)
                        logger.info("[AUDIO_TRANSCRIBER] Inicializando WhisperModel local (%s, %s)...", self.model_size, self.compute_type)
                        self._model = WhisperModel(
                            self.model_size,
                            device=self.device,
                            compute_type=self.compute_type,
                            download_root=self._download_root,
                        )
                    except Exception as e:
                        logger.error("[AUDIO_TRANSCRIBER] Error al inicializar Whisper local: %s", e)
                        self._model = None
        return self._model

    def _transcribe_local(self, audio_bytes: bytes) -> Optional[str]:
        if not HAS_FASTER_WHISPER:
            return None

        model = self._get_local_model()
        if not model:
            return None

        temp_file = tempfile.NamedTemporaryFile(suffix=".ogg", delete=False)
        temp_path = temp_file.name
        try:
            temp_file.write(audio_bytes)
            temp_file.close()

            with self._transcribe_lock:
                segments, info = model.transcribe(
                    temp_path,
                    language="es",
                    beam_size=2,
                    vad_filter=True,
                )
                if info.duration > 90.0:
                    logger.warning("[AUDIO_TRANSCRIBER] Duración de audio local supera 90s: %.1fs", info.duration)
                    return None

                text_parts = [s.text.strip() for s in segments if s.text.strip()]
                full_text = " ".join(text_parts).strip()
                if len(full_text) >= 3:
                    logger.info("[AUDIO_TRANSCRIBER] Transcripción local exitosa (%.1fs): '%s'", info.duration, full_text)
                    return full_text
                return None
        except Exception as e:
            logger.error("[AUDIO_TRANSCRIBER] Error en transcripción local: %s", e)
            return None
        finally:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass

    def transcribe_base64_audio(self, base64_str: str) -> Optional[str]:
        """Método sincrónico de compatibilidad hacia atrás."""
        clean_b64 = base64_str.split(",", 1)[1] if "," in base64_str else base64_str
        try:
            audio_bytes = base64.b64decode(clean_b64)
            return self._transcribe_local(audio_bytes)
        except Exception:
            return None


audio_transcriber = AudioTranscriber()
