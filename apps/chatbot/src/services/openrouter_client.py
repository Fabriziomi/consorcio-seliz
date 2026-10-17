import time
import json
import logging
from typing import Optional, Dict, Any, List
import httpx

from core.config import settings
from engine.state_models import DecisionResultado, Intencion

logger = logging.getLogger(__name__)


class OpenRouterClient:
    """
    Cliente asíncrono para OpenRouter con motor de decisión tipado Jev 1.14
    y conmutación automática por fallback a Gemini 2.5 Flash con Structured Outputs.
    """

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or settings.OPENROUTER_KEY
        self.base_url = (base_url or settings.OPENROUTER_BASE_URL).rstrip("/")
        self.timeout = float(settings.DECISION_TIMEOUT_SECONDS)
        self.confidence_threshold = float(settings.CONFIDENCE_THRESHOLD)

    def _get_headers(self) -> Dict[str, str]:
        if not self.api_key:
            raise ValueError("OPENROUTER_KEY no está configurada en el entorno.")
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://consorcio-seliz.admin.ar",
            "X-Title": "Consorcio Seliz Bot",
        }

    async def classify_intent(
        self,
        text: str,
        has_consorcio: bool = False,
        has_unidad: bool = False,
        consorcios_catalog: Optional[List[Dict[str, Any]]] = None,
    ) -> DecisionResultado:
        """
        Clasifica la intención del usuario y extrae consorcio/unidad según la regla de cortocircuito.
        """
        start_time = time.perf_counter()

        clean_text = text.strip()
        if not clean_text:
            return DecisionResultado(
                intencion=Intencion.INTENCION_AMBIGUA.value,
                confidence=1.0,
                latency_ms=0.0,
                model_used="early_rule",
            )

        ask_consorcio = not has_consorcio
        ask_unidad = not has_unidad

        try:
            return await self._call_jev_decision(
                text=clean_text,
                ask_consorcio=ask_consorcio,
                ask_unidad=ask_unidad,
                consorcios_catalog=consorcios_catalog or [],
                start_time=start_time,
            )
        except Exception as exc:
            logger.warning(
                "Fallo o timeout en llamada a Jev 1.14 (%s). Conmutando a fallback Gemini 2.5 Flash.",
                exc,
            )
            return await self._call_gemini_fallback(
                text=clean_text,
                ask_consorcio=ask_consorcio,
                ask_unidad=ask_unidad,
                consorcios_catalog=consorcios_catalog or [],
                start_time=start_time,
            )

    async def _call_jev_decision(
        self,
        text: str,
        ask_consorcio: bool,
        ask_unidad: bool,
        consorcios_catalog: List[Dict[str, Any]],
        start_time: float,
    ) -> DecisionResultado:
        endpoint = f"{self.base_url}/api/alpha/decisions"

        questions: Dict[str, Any] = {
            "intencion": {
                "type": "choice",
                "instructions": "Clasificar la intención del vecino del consorcio en una de las categorías disponibles.",
                "criteria": {
                    "CONSULTA_EXPENSAS": "Pide datos bancarios, CBU, alias, liquidación o importe para pagar las expensas",
                    "RECLAMO_TECNICO": "Reporta rotura, humedad, ascensor fuera de servicio, corte de luz/agua, cañería o problema edilicio",
                    "EMERGENCIA_GRAVE": "Riesgo inminente: escape de gas, principio de incendio, inundación masiva o personas atrapadas en ascensor",
                    "AVISO_PAGO_REALIZADO": "Avisa que ya pagó o adjunta comprobante de transferencia bancaria",
                    "MUDANZA": "Consulta por normas, días u horarios de mudanza o flete",
                    "CIERRE_CORDIAL": "Agradecimiento o despedida breve como gracias, muchas gracias, ok, saludos",
                    "OTRO": "Cualquier otra consulta general no listada",
                },
            }
        }

        if ask_consorcio:
            criteria_consorcios: Dict[str, str] = {}
            for c in consorcios_catalog:
                c_id = c.get("id")
                c_nombre = c.get("nombre", "")
                c_dir = c.get("direccion", "")
                criteria_consorcios[c_id] = f"Menciona el edificio {c_nombre} en {c_dir}"

            criteria_consorcios["OTRO_NO_ADMINISTRADO"] = "Menciona una calle o edificio que no pertenece a la administración Seliz"
            criteria_consorcios["NINGUNO"] = "No menciona ningún edificio, calle ni dirección"

            questions["consorcio_mencionado"] = {
                "type": "choice",
                "instructions": "Identificar si el vecino menciona alguno de los consorcios administrados.",
                "criteria": criteria_consorcios,
            }

        if ask_unidad:
            questions["contiene_unidad"] = {
                "type": "choice",
                "instructions": "¿El mensaje contiene una unidad funcional, piso, departamento, cochera o local?",
                "criteria": {
                    "SI": "Menciona explícitamente piso y depto, ej: 4B, 8° C, depto 2, PB A, cochera 14, local 1",
                    "NO": "No menciona unidad funcional, piso ni depto",
                },
            }

        payload = {
            "model": settings.JEV_MODEL,
            "state": f"Mensaje del vecino: {text}",
            "questions": questions,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(endpoint, headers=self._get_headers(), json=payload)

        if response.status_code != 200:
            raise RuntimeError(f"Error Jev HTTP {response.status_code}: {response.text}")

        data = response.json()
        answers = data.get("answers", {})

        ans_intencion = answers.get("intencion", {})
        raw_intent = ans_intencion.get("choice", "OTRO")
        intent_confidence = float(ans_intencion.get("confidence", 1.0))
        probabilities = ans_intencion.get("probabilities", {})

        if intent_confidence < self.confidence_threshold:
            resolved_intent = Intencion.INTENCION_AMBIGUA.value
        else:
            resolved_intent = raw_intent

        consorcio_mencionado = None
        consorcio_confidence = 0.0
        if ask_consorcio and "consorcio_mencionado" in answers:
            ans_consorcio = answers["consorcio_mencionado"]
            consorcio_choice = ans_consorcio.get("choice")
            consorcio_confidence = float(ans_consorcio.get("confidence", 1.0))
            if consorcio_choice and consorcio_choice != "NINGUNO":
                consorcio_mencionado = consorcio_choice

        contiene_unidad_flag = False
        unidad_normalizada = None
        if ask_unidad and "contiene_unidad" in answers:
            ans_unidad = answers["contiene_unidad"]
            if ans_unidad.get("choice") == "SI":
                contiene_unidad_flag = True
                unidad_normalizada = await self.extract_normalized_unit(text)

        latency = (time.perf_counter() - start_time) * 1000.0

        return DecisionResultado(
            intencion=resolved_intent,
            confidence=intent_confidence,
            probabilities=probabilities,
            consorcio_mencionado=consorcio_mencionado,
            consorcio_confidence=consorcio_confidence,
            contiene_unidad=contiene_unidad_flag,
            unidad_funcional=unidad_normalizada,
            is_emergency=(resolved_intent == Intencion.EMERGENCIA_GRAVE.value),
            model_used=settings.JEV_MODEL,
            latency_ms=round(latency, 2),
            is_fallback=False,
        )

    async def _call_gemini_fallback(
        self,
        text: str,
        ask_consorcio: bool,
        ask_unidad: bool,
        consorcios_catalog: List[Dict[str, Any]],
        start_time: float,
    ) -> DecisionResultado:
        endpoint = f"{self.base_url}/api/v1/chat/completions"

        catalog_desc = "\n".join(
            [f"- ID '{c.get('id')}': {c.get('nombre')} ({c.get('direccion')})" for c in consorcios_catalog]
        )

        system_prompt = (
            "Sos el motor de clasificación estricto del Chatbot Consorcio Seliz. "
            "Debés analizar el mensaje del vecino y devolver UNICAMENTE un JSON válido con esta estructura:\n"
            "{\n"
            '  "intencion": "CONSULTA_EXPENSAS" | "RECLAMO_TECNICO" | "EMERGENCIA_GRAVE" | "AVISO_PAGO_REALIZADO" | "MUDANZA" | "CIERRE_CORDIAL" | "OTRO",\n'
            '  "confidence": float entre 0.0 y 1.0,\n'
            '  "consorcio_mencionado": string con el ID exacto del catálogo, "OTRO_NO_ADMINISTRADO" o null,\n'
            '  "contiene_unidad": boolean,\n'
            '  "unidad_funcional": string normalizado (ej: "4° B", "PB A") o null\n'
            "}\n\n"
            f"Catálogo de consorcios administrados:\n{catalog_desc}\n"
        )

        payload = {
            "model": settings.GEMINI_FALLBACK_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Mensaje del vecino: {text}"},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.0,
            "max_tokens": 150,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(endpoint, headers=self._get_headers(), json=payload)

        if response.status_code != 200:
            latency = (time.perf_counter() - start_time) * 1000.0
            logger.error("Fallback Gemini falló con código HTTP %s: %s", response.status_code, response.text)
            return DecisionResultado(
                intencion=Intencion.INTENCION_AMBIGUA.value,
                confidence=0.0,
                latency_ms=round(latency, 2),
                model_used=settings.GEMINI_FALLBACK_MODEL,
                is_fallback=True,
            )

        data = response.json()
        content = data["choices"][0]["message"]["content"]
        parsed = json.loads(content)

        raw_intent = parsed.get("intencion", "OTRO")
        confidence = float(parsed.get("confidence", 1.0))
        if confidence < self.confidence_threshold:
            resolved_intent = Intencion.INTENCION_AMBIGUA.value
        else:
            resolved_intent = raw_intent

        latency = (time.perf_counter() - start_time) * 1000.0

        consorcio = parsed.get("consorcio_mencionado") if ask_consorcio else None
        if consorcio in ("NINGUNO", "null", ""):
            consorcio = None

        contiene_unidad = bool(parsed.get("contiene_unidad")) if ask_unidad else False
        unidad = parsed.get("unidad_funcional") if (ask_unidad and contiene_unidad) else None

        return DecisionResultado(
            intencion=resolved_intent,
            confidence=confidence,
            consorcio_mencionado=consorcio,
            consorcio_confidence=confidence,
            contiene_unidad=contiene_unidad,
            unidad_funcional=unidad,
            is_emergency=(resolved_intent == Intencion.EMERGENCIA_GRAVE.value),
            model_used=settings.GEMINI_FALLBACK_MODEL,
            latency_ms=round(latency, 2),
            is_fallback=True,
        )

    async def extract_normalized_unit(self, text: str) -> Optional[str]:
        """
        Micro-llamada a Gemini 2.5 Flash (temperature 0.0) para normalizar la unidad funcional (ej: '4° B').
        """
        endpoint = f"{self.base_url}/api/v1/chat/completions"
        system_prompt = (
            "Extrae la unidad funcional (piso y depto, local o cochera) del mensaje en formato argentino estándar "
            '(ej: "4° B", "PB A", "Cochera 14", "Local 2"). Devuelve únicamente un JSON: {"unidad": "..."}. '
            'Si no hay unidad comprensible, devuelve {"unidad": null}.'
        )

        payload = {
            "model": settings.GEMINI_FALLBACK_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.0,
            "max_tokens": 40,
        }

        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.post(endpoint, headers=self._get_headers(), json=payload)
            if res.status_code == 200:
                parsed = json.loads(res.json()["choices"][0]["message"]["content"])
                return parsed.get("unidad")
        except Exception as exc:
            logger.warning("Fallo al normalizar unidad con Gemini: %s", exc)

        return None
