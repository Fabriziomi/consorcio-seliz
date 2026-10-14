import os
import time
from typing import Tuple
from enum import Enum


class Tev1Decision(str, Enum):
    A_EMERGENCY = "A"       # Emergencia Grave 24/7
    B_PAYMENTS = "B"        # Cobranzas y Datos de Pago por Email
    C_CORDIAL_SILENCE = "C" # Cierre Cordial / Silencio (No responder)
    D_TICKET_NEUTRAL = "D"  # Consulta No Catalogada (Asentar Ticket neutro para Ivana)


class Tev1Router:
    def __init__(self, model_path: str = "models/tev1-0.8b-q4_k_m.gguf"):
        self.model_path = model_path
        self._llm = None
        self._has_model = os.path.exists(self.model_path)

    def route(self, user_message: str, is_emergency: bool = False, is_cordial_close: bool = False) -> Tuple[Tev1Decision, float]:
        """
        Clasifica el mensaje entrante en un conjunto cerrado (A, B, C, D).
        Retorna: (Decision: Tev1Decision, latencia_ms: float)
        """
        t0 = time.time()

        # 1. Reglas directas de bypass de guardrails
        if is_emergency:
            latency_ms = (time.time() - t0) * 1000
            return Tev1Decision.A_EMERGENCY, latency_ms

        if is_cordial_close:
            latency_ms = (time.time() - t0) * 1000
            return Tev1Decision.C_CORDIAL_SILENCE, latency_ms

        # 2. Si el modelo GGUF local de Tev1 está presente en disco
        if self._has_model:
            try:
                from llama_cpp import Llama
                if self._llm is None:
                    self._llm = Llama(model_path=self.model_path, n_ctx=512, n_threads=6, verbose=False)
                
                prompt = (
                    f"Clasifica el siguiente mensaje en una sola letra:\n"
                    f"A: Emergencia Grave 24/7\n"
                    f"B: Cobranzas, CBU o Expensas\n"
                    f"C: Cierre Cordial o Saludo Corto\n"
                    f"D: Reclamo o Consulta Administrativa General\n\n"
                    f"Mensaje: \"{user_message}\"\n"
                    f"Respuesta (solo una letra):"
                )
                output = self._llm(prompt, max_tokens=2, stop=["\n", " "], temperature=0.0)
                letter = output["choices"][0]["text"].strip().upper()
                latency_ms = (time.time() - t0) * 1000

                if letter in ["A", "B", "C", "D"]:
                    return Tev1Decision(letter), latency_ms
            except Exception as e:
                # Fallback seguro
                pass

        # 3. Router de conjunto cerrado semántico rápido (Fallback sin GGUF en disco)
        msg_lower = user_message.lower()
        if any(w in msg_lower for w in ["cbu", "alias", "transferir", "expensa", "expensas", "cuenta", "comprobante", "pagar", "pago"]):
            latency_ms = (time.time() - t0) * 1000
            return Tev1Decision.B_PAYMENTS, latency_ms

        latency_ms = (time.time() - t0) * 1000
        return Tev1Decision.D_TICKET_NEUTRAL, latency_ms


tev1_router = Tev1Router()
