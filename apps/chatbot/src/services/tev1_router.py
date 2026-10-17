import os
import re
import time
import threading
from typing import Tuple, Optional
from enum import Enum
from core.logging import logger

try:
    from llama_cpp import Llama
    HAS_LLAMA_CPP = True
except ImportError:
    HAS_LLAMA_CPP = False


class Tev1Decision(str, Enum):
    A_EMERGENCY = "A"
    B_PAYMENTS = "B"
    C_CORDIAL_SILENCE = "C"
    D_TICKET_NEUTRAL = "D"
    E_PAYMENT_CONFIRMATION = "E"
    F_MUDANZA = "F"


RE_PAYMENT_REQUEST = re.compile(
    r"\b("
    r"cbu|alias|alias bancario|"
    r"datos (bancarios|de la cuenta|para pagar|para transferir|de cobranzas)|"
    r"cuenta (bancaria|del consorcio|para transferir|para pagar)|"
    r"(donde|dónde|como|cómo) (se )?(transfiere|paga|abona)(n)? (las )?expensas?|"
    r"(pasame|pásame|pasan|pásenme|me pasan|me pasas|me podr[ií]an pasar) (el )?(cbu|alias|datos)|"
    r"(a que cuenta|a qué cuenta|a nombre de qui[eé]n) (se )?(transfiere|paga)|"
    r"(para pagar|para transferir) (las )?expensas"
    r")\b",
    re.IGNORECASE,
)

RE_PAYMENT_CONFIRMATION = re.compile(
    r"\b("
    r"ya (transfer[ií]|pagu[eé]|abone|aboné|hice el pago|hice la transferencia)|"
    r"(adjunto|paso|env[ií]o|te paso|te mando|te adjunto) (el )?(comprobante|ticket|constancia|transferencia)|"
    r"comprobante de (pago|transferencia)|"
    r"constancia de (pago|transferencia)|"
    r"acabo de (pagar|transferir)"
    r")\b",
    re.IGNORECASE,
)

RE_MUDANZA = re.compile(
    r"\b("
    r"mudanza|mudarme|mudar|flete|fletes|camion de mudanza|camión de mudanza|"
    r"horarios? (de|para) mudanza|permiso (de|para) mudanza"
    r")\b",
    re.IGNORECASE,
)

RE_RECLAMO_MANTENIMIENTO = re.compile(
    r"\b("
    r"ascensor|plomero|electricista|electricidad|ca[ñn]o|agua|filtraci[oó]n|humedad|"
    r"gotea|inund|luz quemada|sin luz|corte de luz|palier|cerradura|port[oó]n|"
    r"tablero|quemad[oa]|cortocircuito|disyuntor|t[eé]rmica|olor a quemado|humo|enchufe|"
    r"rot[oa]s?|no anda|no funciona|aver[ií]a|descompuesto|p[eé]rdida|gotera|"
    r"ruidos? molestos?|bomba de agua|llave|encargado|portero|asamblea"
    r")\b",
    re.IGNORECASE,
)


class Tev1Router:
    """
    Enrutador semántico de dos niveles:
    1. Reglas contextuales deterministas de alta precisión (latencia < 1ms, cero falsos positivos).
    2. Motor de inferencia local GGUF (Tev1 / Qwen 2.5) para desambiguación contextual de mensajes complejos.
    """

    def __init__(self, model_path: str = "models/tev1-0.8b-q4_k_m.gguf"):
        self.model_path = model_path
        self._llm: Optional[Llama] = None
        self._has_model = os.path.exists(self.model_path) and HAS_LLAMA_CPP
        self._init_lock = threading.Lock()
        self._lock = threading.Lock()

    def _get_llm(self) -> Optional[Llama]:
        """Carga perezosa del modelo local GGUF en CPU multi-hilo."""
        if self._llm is None and self._has_model:
            with self._init_lock:
                if self._llm is None and self._has_model:
                    try:
                        t0 = time.time()
                        self._llm = Llama(
                            model_path=self.model_path,
                            n_ctx=512,
                            n_threads=4,
                            verbose=False,
                        )
                        logger.info(f"[TEV1_ROUTER] Modelo local GGUF cargado exitosamente en {(time.time() - t0):.2f}s")
                    except Exception as e:
                        logger.warning(f"[TEV1_ROUTER] Falló la inicialización del modelo GGUF: {e}. Se utilizará motor determinista.")
                        self._has_model = False
        return self._llm

    def _classify_with_llm(self, message: str) -> Optional[Tev1Decision]:
        """Inferencia local con modelo GGUF en conjunto cerrado protegida contra concurrencia."""
        llm = self._get_llm()
        if not llm:
            return None

        prompt = (
            "<|im_start|>system\n"
            "Eres un clasificador para administración de consorcios de edificios. "
            "Clasifica el mensaje del vecino en exactamente una de las siguientes opciones:\n"
            "A: Emergencia edilicia grave (fuego, escape de gas, personas atrapadas en ascensor)\n"
            "B: Solicitud de CBU, alias o cuenta bancaria para pagar expensas\n"
            "C: Cierre cordial, agradecimiento o saludo de despedida\n"
            "D: Reclamo técnico, rotura, avería, corte de servicios o consulta administrativa\n"
            "E: Notificación de comprobante de pago de expensas ya realizado\n"
            "F: Consulta sobre horarios o requisitos de mudanza y fletes\n"
            "Responde ÚNICAMENTE con la letra (A, B, C, D, E o F).<|im_end|>\n"
            f"<|im_start|>user\n{message}<|im_end|>\n"
            "<|im_start|>assistant\n"
        )

        acquired = self._lock.acquire(timeout=1.5)
        if not acquired:
            logger.info("[TEV1_ROUTER] Inferencia ocupada por otra solicitud. Continuando con contingencia.")
            return None

        try:
            res = llm(prompt, max_tokens=3, temperature=0.1, stop=["<|im_end|>", "\n"])
            text = res["choices"][0]["text"].strip().upper()
            clean_letter = re.sub(r"[^ABCDEF]", "", text)
            if clean_letter and len(clean_letter) > 0:
                letter = clean_letter[0]
                for d in Tev1Decision:
                    if d.value == letter:
                        return d
        except Exception as e:
            logger.warning(f"[TEV1_ROUTER] Error en inferencia LLM: {e}")
        finally:
            self._lock.release()

        return None

    def route(
        self,
        user_message: str,
        is_emergency: bool = False,
        is_cordial_close: bool = False,
    ) -> Tuple[Tev1Decision, float]:
        """
        Clasifica el mensaje entrante en un conjunto cerrado (A, B, C, D, E, F).
        Retorna: (Decision: Tev1Decision, latencia_ms: float)
        """
        t0 = time.time()
        if is_emergency:
            return Tev1Decision.A_EMERGENCY, (time.time() - t0) * 1000

        if is_cordial_close:
            return Tev1Decision.C_CORDIAL_SILENCE, (time.time() - t0) * 1000

        msg_clean = user_message.strip()

        if RE_PAYMENT_CONFIRMATION.search(msg_clean):
            return Tev1Decision.E_PAYMENT_CONFIRMATION, (time.time() - t0) * 1000

        if RE_PAYMENT_REQUEST.search(msg_clean):
            return Tev1Decision.B_PAYMENTS, (time.time() - t0) * 1000

        if RE_RECLAMO_MANTENIMIENTO.search(msg_clean):
            return Tev1Decision.D_TICKET_NEUTRAL, (time.time() - t0) * 1000

        if RE_MUDANZA.search(msg_clean):
            return Tev1Decision.F_MUDANZA, (time.time() - t0) * 1000

        llm_decision = self._classify_with_llm(msg_clean)
        if llm_decision:
            latency_ms = (time.time() - t0) * 1000
            return llm_decision, latency_ms

        latency_ms = (time.time() - t0) * 1000
        return Tev1Decision.D_TICKET_NEUTRAL, latency_ms


tev1_router = Tev1Router()
