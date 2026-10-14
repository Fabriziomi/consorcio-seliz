import os
import base64
import tempfile
import threading
import asyncio
from typing import Optional
from core.logging import logger

try:
    from faster_whisper import WhisperModel
    HAS_FASTER_WHISPER = True
except ImportError:
    HAS_FASTER_WHISPER = False


class AudioTranscriber:
    """
    Servicio de transcripción Speech-to-Text de notas de voz de WhatsApp (PTT)
    utilizando faster-whisper (CTranslate2) optimizado para CPU en modo INT8.
    """

    def __init__(self, model_size: str = "tiny", device: str = "cpu", compute_type: str = "int8"):
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self._model: Optional[WhisperModel] = None
        self._init_lock = threading.Lock()
        self._transcribe_lock = threading.Lock()
        self._download_root = os.path.join(os.getcwd(), "models", "whisper")

    def _get_model(self) -> Optional[WhisperModel]:
        """Carga perezosa del modelo Whisper en RAM/CPU."""
        if self._model is None and HAS_FASTER_WHISPER:
            with self._init_lock:
                if self._model is None:
                    try:
                        os.makedirs(self._download_root, exist_ok=True)
                        logger.info(f"[AUDIO_TRANSCRIBER] Inicializando WhisperModel ({self.model_size}, {self.compute_type})...")
                        self._model = WhisperModel(
                            self.model_size,
                            device=self.device,
                            compute_type=self.compute_type,
                            download_root=self._download_root,
                        )
                        logger.info("[AUDIO_TRANSCRIBER] Modelo Whisper cargado exitosamente.")
                    except Exception as e:
                        logger.error(f"[AUDIO_TRANSCRIBER] Error al inicializar Whisper: {e}")
                        self._model = None
        return self._model

    def transcribe_base64_audio(self, base64_str: str) -> Optional[str]:
        """
        Decodifica un audio en Base64 (formato WhatsApp OGG/Opus o MP3)
        y lo transcribe a texto en español.
        """
        if not base64_str or not HAS_FASTER_WHISPER:
            return None

        # Limpiar posibles encabezados data URI
        if "," in base64_str:
            base64_str = base64_str.split(",", 1)[1]

        try:
            audio_bytes = base64.b64decode(base64_str)
        except Exception as e:
            logger.warning(f"[AUDIO_TRANSCRIBER] Error al decodificar Base64 de audio: {e}")
            return None

        if len(audio_bytes) < 200:
            logger.warning("[AUDIO_TRANSCRIBER] Audio demasiado corto o vacío.")
            return None

        model = self._get_model()
        if not model:
            logger.warning("[AUDIO_TRANSCRIBER] WhisperModel no disponible para transcripción.")
            return None

        temp_file = tempfile.NamedTemporaryFile(suffix=".ogg", delete=False)
        temp_path = temp_file.name
        try:
            temp_file.write(audio_bytes)
            temp_file.close()

            # Thread-safety: lock de inferencia CTranslate2
            with self._transcribe_lock:
                segments, info = model.transcribe(
                    temp_path,
                    language="es",
                    beam_size=2,
                    vad_filter=True,  # Filtro de detección de actividad vocal
                )
                text_parts = [s.text.strip() for s in segments if s.text.strip()]
                full_text = " ".join(text_parts).strip()

                if full_text:
                    logger.info(f"[AUDIO_TRANSCRIBER] Transcripción exitosa ({info.duration:.1f}s): '{full_text}'")
                    return full_text
                else:
                    logger.info("[AUDIO_TRANSCRIBER] Audio sin habla inteligible.")
                    return None

        except Exception as e:
            logger.error(f"[AUDIO_TRANSCRIBER] Error durante transcripción: {e}")
            return None
        finally:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass

    async def transcribe_async(self, base64_str: str) -> Optional[str]:
        """Ejecuta la transcripción en un hilo secundario sin bloquear el Event Loop."""
        return await asyncio.to_thread(self.transcribe_base64_audio, base64_str)


# Instancia singleton para reutilización eficiente
audio_transcriber = AudioTranscriber()
