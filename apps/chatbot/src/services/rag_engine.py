import time
import numpy as np
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass, field
from fastembed import TextEmbedding

@dataclass
class FaqItem:
    id: str
    preguntas: List[str]
    respuesta: str
    categoria: str
    consorcio: Optional[str] = None
    consorcio_id: Optional[str] = None

    @property
    def pregunta_principal(self) -> str:
        return self.preguntas[0] if self.preguntas else ""


OFFICIAL_FAQS: List[FaqItem] = [
    FaqItem(
        id="faq-expensas-cbu",
        preguntas=[
            "¿Dónde pago las expensas o cuál es el CBU y alias para transferir?",
            "¿Me pasan el CBU y alias para pagar las expensas?",
            "¿Cuáles son los datos de la cuenta bancaria para transferir expensas?",
            "¿Cómo y dónde se transfieren las expensas?",
        ],
        respuesta=(
            "Los pagos de expensas se realizan exclusivamente por transferencia bancaria a la cuenta oficial del consorcio.\n"
            "Por favor indicanos tu edificio para brindarte el CBU y alias correspondiente.\n"
            "Recordá que el comprobante debe enviarse por correo electrónico con tu unidad en el asunto."
        ),
        categoria="EXPENSAS"
    ),
    FaqItem(
        id="faq-expensas-comprobante",
        preguntas=[
            "¿A qué correo envío el comprobante de pago de expensas?",
            "¿Dónde tengo que mandar el comprobante de transferencia?",
            "¿Cuál es el email de cobranzas para enviar el comprobante?",
        ],
        respuesta=(
            "Los comprobantes de pago de expensas deben remitirse únicamente por email a la casilla de cobranzas de la administración.\n"
            "Por favor no envíes solo la foto por WhatsApp sin mandar el correo formal para que el área contable pueda imputar tu pago."
        ),
        categoria="EXPENSAS"
    ),
    FaqItem(
        id="faq-mudanzas-horarios",
        preguntas=[
            "¿Cuáles son los horarios permitidos para mudanzas y qué requisitos piden?",
            "A qué hora se puede hacer una mudanza?",
            "¿Qué días y horarios se puede hacer mudanza en el edificio?",
            "Horarios de mudanza permitidos",
            "Me quiero mudar el sábado qué necesito?",
        ],
        respuesta=(
            "Las mudanzas están permitidas de Lunes a Viernes de 09:00 a 17:00 hs y Sábados de 09:00 a 13:00 hs.\n"
            "Es obligatorio coordinar con 48 hs hábiles de anticipación y presentar el seguro de accidentes personales / ART de la empresa de fletes."
        ),
        categoria="MUDANZAS"
    ),
    FaqItem(
        id="faq-basura-horarios",
        preguntas=[
            "¿En qué horario se saca la basura y cómo funciona la portería?",
            "En qué horario se saca la basura?",
            "¿A qué hora se puede tirar la basura en el edificio?",
            "Horario para sacar la basura",
        ],
        respuesta=(
            "El horario de depósito de residuos en los conductos o canastos es de Domingo a Viernes de 19:00 a 20:00 hs (nunca los Sábados).\n"
            "Las bolsas deben estar cerradas herméticamente y separadas en reciclables y húmedos."
        ),
        categoria="CONVIVENCIA"
    ),
    FaqItem(
        id="faq-reclamo-filtracion",
        preguntas=[
            "Tengo una filtración de agua o humedad en el techo o pared",
            "Se filtra agua del departamento de arriba",
            "Hay humedad en el techo de mi baño",
            "Tengo una mancha de humedad y gotea",
        ],
        respuesta=(
            "Para asentar reclamos por filtraciones o humedad, tomamos registro del incidente.\n"
            "Por favor indicanos si proviene de una unidad superior o parte común y adjuntá una foto para que el área técnica evalúe el origen en la próxima jornada hábil."
        ),
        categoria="MANTENIMIENTO"
    ),
    FaqItem(
        id="faq-ruidos-molestos",
        preguntas=[
            "Hay ruidos molestos, fiestas o música alta en el edificio",
            "El vecino de arriba hace mucho ruido a la noche",
            "Música fuerte y ruidos molestos en horas de descanso",
        ],
        respuesta=(
            "El reglamento de copropiedad establece horario de descanso a partir de las 22:00 hs.\n"
            "Podés comunicarte con la guardia/portería en el momento. Si la situación persiste, tu reclamo quedará registrado para que la administración envíe una notificación formal a la unidad infractora."
        ),
        categoria="CONVIVENCIA"
    ),
]


class RagEngine:
    def __init__(self, threshold: float = 0.80):
        self.threshold = threshold
        self.model_name = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        self._embedding_model: Optional[TextEmbedding] = None
        self._faq_embeddings: Optional[np.ndarray] = None
        self._index_to_faq: List[FaqItem] = []
        self.faqs: List[FaqItem] = list(OFFICIAL_FAQS)

    def _get_model(self) -> TextEmbedding:
        if self._embedding_model is None:
            self._embedding_model = TextEmbedding(self.model_name)
        return self._embedding_model

    def load_db_faqs(self, db_faqs: List[Any]):
        """
        Carga y actualiza las FAQs aprobadas en memoria desde la base de datos (FaqAprobadaModel o diccionarios).
        Preserva las oficiales como fallback base.
        """
        new_faqs: List[FaqItem] = []
        for f in db_faqs:
            f_id = getattr(f, "id", None) or (f.get("id") if isinstance(f, dict) else None)
            pregunta = getattr(f, "pregunta", None) or (f.get("pregunta") if isinstance(f, dict) else None)
            respuesta = (
                getattr(f, "respuesta_oficial", None)
                or getattr(f, "respuesta", None)
                or (f.get("respuesta_oficial") if isinstance(f, dict) else None)
                or (f.get("respuesta") if isinstance(f, dict) else None)
            )
            activo = getattr(f, "activo", True) if hasattr(f, "activo") else (f.get("activo", True) if isinstance(f, dict) else True)
            c_id = getattr(f, "consorcio_id", None) or (f.get("consorcio_id") if isinstance(f, dict) else None)

            if not activo or not pregunta or not respuesta:
                continue

            variaciones = [p.strip() for p in pregunta.split("\n") if p.strip()]
            if not variaciones:
                variaciones = [pregunta.strip()]

            new_faqs.append(
                FaqItem(
                    id=str(f_id or f"faq-db-{len(new_faqs)}"),
                    preguntas=variaciones,
                    respuesta=respuesta.strip(),
                    categoria="BASE_CONOCIMIENTO",
                    consorcio_id=c_id,
                )
            )

        existing_ids = {item.id for item in new_faqs}
        for base_faq in OFFICIAL_FAQS:
            if base_faq.id not in existing_ids:
                new_faqs.append(base_faq)

        self.faqs = new_faqs
        self._faq_embeddings = None
        self._index_to_faq = []

    def _initialize_index(self):
        """Indexa y cachea los embeddings de todas las variaciones de FAQs."""
        if self._faq_embeddings is None:
            model = self._get_model()
            textos = []
            faq_mapping = []

            for faq in self.faqs:
                for preg in faq.preguntas:
                    textos.append(preg)
                    faq_mapping.append(faq)

            if not textos:
                self._faq_embeddings = np.empty((0, 384), dtype=np.float32)
                self._index_to_faq = []
                return

            embeddings = list(model.embed(textos))
            self._faq_embeddings = np.array(embeddings, dtype=np.float32)

            norms = np.linalg.norm(self._faq_embeddings, axis=1, keepdims=True)
            self._faq_embeddings = self._faq_embeddings / np.maximum(norms, 1e-12)
            self._index_to_faq = faq_mapping

    def search(self, query: str, consorcio_id: Optional[str] = None) -> Tuple[Optional[FaqItem], float, float]:
        """
        Búsqueda vectorial Nivel 1 con filtro estricto por consorcio para evitar fugas de información.
        Retorna: (FaqItem si similitud >= threshold, score_maximo, latencia_ms)
        """
        self._initialize_index()
        t0 = time.time()

        if self._faq_embeddings is None or len(self._index_to_faq) == 0:
            return None, 0.0, 0.0

        model = self._get_model()
        query_emb = np.array(list(model.embed([query]))[0], dtype=np.float32)
        norm = np.linalg.norm(query_emb)
        if norm > 0:
            query_emb = query_emb / norm

        scores = np.dot(self._faq_embeddings, query_emb)
        sorted_indices = np.argsort(scores)[::-1]
        best_overall_score = float(scores[sorted_indices[0]]) if len(sorted_indices) > 0 else 0.0
        latency_ms = (time.time() - t0) * 1000

        for idx in sorted_indices:
            score = float(scores[idx])
            if score < self.threshold:
                break
            candidate = self._index_to_faq[idx]
            if candidate.consorcio_id:
                if consorcio_id and candidate.consorcio_id != consorcio_id:
                    continue
                if not consorcio_id:
                    continue
            return candidate, score, latency_ms

        return None, best_overall_score, latency_ms


rag_engine = RagEngine(threshold=0.80)

