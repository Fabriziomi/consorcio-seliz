import os
import re
import json
import time
import threading
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from core.logging import logger

try:
    from llama_cpp import Llama
    HAS_LLAMA_CPP = True
except ImportError:
    HAS_LLAMA_CPP = False


class SemanticExtractionResult(BaseModel):
    unidad_funcional: Optional[str] = None
    consorcio_mencionado: Optional[str] = None
    categoria: str = "OTRO"
    es_emergencia: bool = False
    intencion: str = "CONSULTA_GENERAL"
    resumen: str = ""
    latencia_ms: float = 0.0
    metodo: str = "FALLBACK_RULES"


SYSTEM_PROMPT_TEMPLATE = """Eres el analista de datos inteligente de la administración de consorcios "Dra. Ivana Seliz" en Buenos Aires, Argentina.
Analizas transcripciones de audio (Whisper) o mensajes de texto escritos por vecinos y extraes un JSON estructurado estricto.

Consorcios válidos administrados:
{consorcios_list}

REGLAS DE EXTRACCIÓN Y NORMALIZACIÓN:
1. "unidad_funcional": Extrae y normaliza el departamento del vecino (ej: si dice "soy de planta baja a", "vivo en el 4b", "hablo del 2c"):
   - "cuarto be", "cuarto b", "4b" -> "4° B"
   - "séptimo a", "septimo a", "7a" -> "7° A"
   - "segundo c", "2c" -> "2° C"
   - "planta baja a", "pb a" -> "PB A"
   - "planta baja", "pb" -> "PB"
   - "piso dos depto cuatro" -> "2° 4"
   - "cochera tres" -> "Cochera 3"
   - Si no se menciona ninguna unidad, devuelve null.

2. "consorcio_mencionado": Si el mensaje menciona o insinúa una calle, dirección o edificio de la lista de Consorcios válidos (ej: "callao", "corrientes al mil", "torre de pueyrredon"), devuelve el NOMBRE EXACTO de la lista. Si no coincide con ninguno o no se menciona, devuelve null.

3. "categoria": Clasifica la incidencia exactamente en una de las siguientes:
   - "ASCENSORES": fallas de cabina, botoneras, puertas trabadas, personas atrapadas.
   - "PLOMERIA": caños rotos, inundación, filtraciones, goteras, desborde cloacal, bombas, tanques.
   - "ELECTRICIDAD": lámparas, lamparitas quemadas, focos, tubos led, falta de luz en palier, tableros, chispazos, térmicas, disyuntores, cortocircuitos.
   - "GAS_CALEFACCION": fugas de gas, estufas, calderas, termotanques.
   - "PORTON_ACCESO": portón levadizo de cochera, llaves magnéticas, cerradura de entrada.
   - "LIMPIEZA_AREAS_COMUNES": palieres sucios, residuos, olores en áreas comunes.
   - "SEGURIDAD": cámaras, alarmas, intrusión o sospechosos.
   - "ADMINISTRACION_CONSULTA": expensas, CBU, comprobantes de pago, mudanzas, reglamentos.
   - "OTRO": cualquier otro asunto no clasificado.

4. "es_emergencia": boolean. DEBE ser true ÚNICAMENTE ante situaciones de peligro inminente:
   - Personas atrapadas en ascensor.
   - Fuego, humo o cables con chispazos activos.
   - Escape o fuerte olor a gas.
   - Inundación masiva o desborde cloacal afectando departamentos o palieres.
   En cualquier otro caso, DEBE ser false.

5. "intencion": Clasifica el propósito del mensaje:
   - "RECLAMO_TECNICO": reporte de desperfecto, rotura o mal funcionamiento.
   - "SOLICITUD_DATOS_PAGO": pide CBU, alias, número de cuenta para transferir expensas.
   - "CONFIRMACION_PAGO": avisa que ya pagó, transfirió ("garpé", "ya pagué", "paso comprobante").
   - "CONSULTA_MUDANZA": consulta horarios, requisitos o permisos de mudanza y fletes.
   - "CONSULTA_GENERAL": consultas informativas (horario encargado, llaves, reuniones).
   - "CIERRE_CORDIAL": saludos de despedida o agradecimiento ("gracias", "dale listo", "buen finde").
   - "SALUDO_PURO": saludo inicial sin consulta ("hola", "buenas tardes").

6. "resumen": Descripción ULTRA CONCISA de 3 a 6 palabras (ej: "Caño roto en 4B", "Ascensor trabado con gente"). NUNCA más de 6 palabras.

Responde ÚNICAMENTE con el objeto JSON válido, sin explicaciones ni rodeos.
"""


class SemanticExtractor:
    """
    Extractor semántico basado en el modelo local Qwen 2.5 3B (GGUF).
    Interpreta lenguaje oral argentino, transcripciones Whisper con números en palabras,
    modismos locales y apodos de edificios, abstrayendo entidades para el backend.
    """

    def __init__(self, model_path: str = "models/qwen2.5-3b-instruct-q4_k_m.gguf"):
        self.model_path = model_path
        self._llm: Optional[Llama] = None
        self._has_model = os.path.exists(self.model_path) and HAS_LLAMA_CPP
        self._init_lock = threading.Lock()
        self._inference_lock = threading.Lock()

    def _get_llm(self) -> Optional[Llama]:
        """Carga perezosa y segura en multithread del modelo GGUF en memoria RAM."""
        if self._llm is None and self._has_model:
            with self._init_lock:
                if self._llm is None and self._has_model:
                    try:
                        t0 = time.time()
                        self._llm = Llama(
                            model_path=self.model_path,
                            n_ctx=2048,
                            n_threads=6,
                            verbose=False,
                        )
                        logger.info(f"[SEMANTIC_EXTRACTOR] Modelo Qwen 2.5 3B cargado exitosamente en {(time.time() - t0):.2f}s")
                    except Exception as e:
                        logger.warning(f"[SEMANTIC_EXTRACTOR] Error al cargar modelo 3B: {e}. Se utilizarán reglas deterministas.")
                        self._has_model = False
        return self._llm

    def _fallback_rules(
        self,
        message: str,
        valid_consorcios: Optional[List[str]] = None,
    ) -> SemanticExtractionResult:
        """Reglas de contingencia si el modelo LLM no está disponible."""
        m_lower = message.lower().strip()
        
        # 1. Unidad funcional básica (números o palabras "cuarto b", "planta baja")
        unit = None
        ORDINAL_MAP = {
            "primero": "1°", "primer": "1°",
            "segundo": "2°", "tercero": "3°", "tercer": "3°",
            "cuarto": "4°", "quinto": "5°",
            "sexto": "6°", "septimo": "7°", "séptimo": "7°",
            "octavo": "8°", "noveno": "9°", "decimo": "10°", "décimo": "10°",
        }
        LETTER_MAP = {
            "a": "A", "be": "B", "b": "B", "ce": "C", "c": "C",
            "de": "D", "d": "D", "e": "E", "efe": "F", "f": "F",
        }
        
        # Mapeo de números hablados como "cuarto be", "cuarto b"
        m_spoken = re.search(r"\b(" + "|".join(ORDINAL_MAP.keys()) + r")\s+([a-zA-Z]{1,2})\b", m_lower)
        if m_spoken:
            piso = ORDINAL_MAP.get(m_spoken.group(1).lower())
            letra_raw = m_spoken.group(2).lower()
            letra = LETTER_MAP.get(letra_raw, letra_raw.upper())
            unit = f"{piso} {letra}"
        elif "planta baja" in m_lower or "pb" in m_lower:
            m_pb = re.search(r"(?:planta\s*baja|pb)\s*([a-zA-Z]|\d{1,2})?", m_lower)
            if m_pb and m_pb.group(1):
                unit = f"PB {m_pb.group(1).upper()}"
            else:
                unit = "PB"
        else:
            m_unit = re.search(r"\b(\d{1,2}[°º]?\s*[a-zA-Z]|cochera\s*\d{1,3})\b", m_lower)
            if m_unit:
                unit = m_unit.group(1).upper()

        # 2. Consorcio por coincidencia de palabras clave
        consorcio_match = None
        if valid_consorcios:
            for c_name in valid_consorcios:
                words = [w for w in re.findall(r"\w+", c_name.lower()) if len(w) >= 5 and w not in ("consorcio", "edificio")]
                if any(w in m_lower for w in words):
                    consorcio_match = c_name
                    break

        # 3. Categoría y Emergencia
        categoria = "OTRO"
        es_emergencia = False
        if any(w in m_lower for w in ("ascensor", "atrapad", "cabina")):
            categoria = "ASCENSORES"
            if any(w in m_lower for w in ("atrapad", "encerrad", "trabad")):
                es_emergencia = True
        elif any(w in m_lower for w in ("inund", "caño", "agua", "filtrac", "cloaca", "desbord")):
            categoria = "PLOMERIA"
            if any(w in m_lower for w in ("inund", "desbord", "revient", "revent", "cloaca")):
                es_emergencia = True
        elif any(w in m_lower for w in ("luz", "corte", "tablero", "chisp", "termica", "térmica")):
            categoria = "ELECTRICIDAD"
            if any(w in m_lower for w in ("chispa", "chispazo", "fuego", "humo", "incendio")):
                es_emergencia = True
        elif any(w in m_lower for w in ("gas", "caldera", "estufa", "termotanque")):
            categoria = "GAS_CALEFACCION"
            if "olor a gas" in m_lower or "fuga" in m_lower:
                es_emergencia = True
        elif any(w in m_lower for w in ("porton", "portón", "cerradura", "llave")):
            categoria = "PORTON_ACCESO"
        elif any(w in m_lower for w in ("limpieza", "basura", "palier", "olor")):
            categoria = "LIMPIEZA_AREAS_COMUNES"
        elif any(w in m_lower for w in ("cbu", "alias", "transfer", "pago", "expensa", "comprobante", "garp")):
            categoria = "ADMINISTRACION_CONSULTA"

        # 4. Intención
        intencion = "RECLAMO_TECNICO"
        if any(w in m_lower for w in ("cbu", "alias", "datos de la cuenta", "donde pagar")):
            intencion = "SOLICITUD_DATOS_PAGO"
        elif any(w in m_lower for w in ("ya pague", "ya pagué", "garpé", "garpe", "comprobante", "constancia")):
            intencion = "CONFIRMACION_PAGO"
        elif any(w in m_lower for w in ("mudanza", "mudar", "flete")):
            intencion = "CONSULTA_MUDANZA"
        elif m_lower in ("hola", "buen dia", "buenos dias", "buenas"):
            intencion = "SALUDO_PURO"
        elif m_lower in ("gracias", "dale listo", "chau", "buen finde"):
            intencion = "CIERRE_CORDIAL"

        return SemanticExtractionResult(
            unidad_funcional=unit,
            consorcio_mencionado=consorcio_match,
            categoria=categoria,
            es_emergencia=es_emergencia,
            intencion=intencion,
            resumen=message[:60],
            latencia_ms=0.5,
            metodo="FALLBACK_RULES",
        )

    def extract(
        self,
        message: str,
        valid_consorcios: Optional[List[str]] = None,
    ) -> SemanticExtractionResult:
        """
        Extrae datos estructurados a partir del mensaje del vecino.
        Usa Qwen 2.5 3B si está disponible; en caso contrario recurre a reglas.
        """
        t0 = time.time()
        llm = self._get_llm()

        if not llm:
            res = self._fallback_rules(message, valid_consorcios)
            res.latencia_ms = (time.time() - t0) * 1000
            return res

        consorcios_str = json.dumps(valid_consorcios or [], ensure_ascii=False)
        system_content = SYSTEM_PROMPT_TEMPLATE.format(consorcios_list=consorcios_str)
        user_content = f"Mensaje del vecino: \"{message}\""

        # Adquisición thread-safe del lock con timeout de 2.0s
        acquired = self._inference_lock.acquire(timeout=2.0)
        if not acquired:
            logger.info("[SEMANTIC_EXTRACTOR] Modelo 3B ocupado por otra solicitud. Despachando por motor determinista.")
            res = self._fallback_rules(message, valid_consorcios)
            res.latencia_ms = (time.time() - t0) * 1000
            return res

        try:
            response = llm.create_chat_completion(
                messages=[
                    {"role": "system", "content": system_content},
                    {"role": "user", "content": user_content},
                ],
                response_format={"type": "json_object"},
                temperature=0.0,
                max_tokens=150,
            )
            raw_json = response["choices"][0]["message"]["content"]
            parsed = json.loads(raw_json)

            latency_ms = (time.time() - t0) * 1000
            
            # Fusión híbrida de seguridad: si el LLM omitió un dato claro, el motor determinista lo rescata
            uf_val = parsed.get("unidad_funcional")
            cons_val = parsed.get("consorcio_mencionado")
            cat_val = parsed.get("categoria", "OTRO")
            em_val = bool(parsed.get("es_emergencia", False))
            int_val = parsed.get("intencion", "CONSULTA_GENERAL")
            
            if not uf_val or not cons_val or cat_val == "OTRO":
                safety = self._fallback_rules(message, valid_consorcios)
                if not uf_val and safety.unidad_funcional:
                    uf_val = safety.unidad_funcional
                if not cons_val and safety.consorcio_mencionado:
                    cons_val = safety.consorcio_mencionado
            # Validación y normalización estricta de categorías válidas
            VALID_CATEGORIAS = {
                "ASCENSORES", "PLOMERIA", "ELECTRICIDAD", "GAS_CALEFACCION",
                "PORTON_ACCESO", "LIMPIEZA_AREAS_COMUNES", "SEGURIDAD",
                "ADMINISTRACION_CONSULTA", "OTRO"
            }
            cat_clean = cat_val.strip().upper()
            if cat_clean not in VALID_CATEGORIAS:
                if any(k in cat_clean for k in ("LÁMP", "LAMP", "LUZ", "ELEC", "FOCO")):
                    cat_val = "ELECTRICIDAD"
                elif any(k in cat_clean for k in ("AGUA", "PLOM", "CAÑO", "INUND", "CLOAC")):
                    cat_val = "PLOMERIA"
                elif any(k in cat_clean for k in ("ASC", "ELEV")):
                    cat_val = "ASCENSORES"
                elif any(k in cat_clean for k in ("GAS", "CALD", "CALEF")):
                    cat_val = "GAS_CALEFACCION"
                else:
                    cat_val = "OTRO"
            else:
                cat_val = cat_clean

            return SemanticExtractionResult(
                unidad_funcional=uf_val,
                consorcio_mencionado=cons_val,
                categoria=cat_val,
                es_emergencia=em_val,
                intencion=int_val,
                resumen=parsed.get("resumen", ""),
                latencia_ms=round(latency_ms, 2),
                metodo="QWEN_3B",
            )
        except Exception as e:
            logger.warning(f"[SEMANTIC_EXTRACTOR] Error durante inferencia LLM: {e}. Aplicando contingencia.")
            res = self._fallback_rules(message, valid_consorcios)
            res.latencia_ms = (time.time() - t0) * 1000
            return res
        finally:
            self._inference_lock.release()


# Instancia singleton para reutilización eficiente
semantic_extractor = SemanticExtractor()
