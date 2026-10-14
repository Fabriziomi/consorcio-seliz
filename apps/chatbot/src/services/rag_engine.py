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

    @property
    def pregunta_principal(self) -> str:
        return self.preguntas[0] if self.preguntas else ""


# Catálogo inicial de FAQs oficiales aprobadas para Consorcios Seliz
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
        self.faqs = OFFICIAL_FAQS

    def _get_model(self) -> TextEmbedding:
        if self._embedding_model is None:
            self._embedding_model = TextEmbedding(self.model_name)
        return self._embedding_model

    def _initialize_index(self):
        """Indexa y cachea los embeddings de todas las variaciones de FAQs oficiales."""
        if self._faq_embeddings is None:
            model = self._get_model()
            textos = []
            faq_mapping = []

            for faq in self.faqs:
                for preg in faq.preguntas:
                    textos.append(preg)
                    faq_mapping.append(faq)

            embeddings = list(model.embed(textos))
            self._faq_embeddings = np.array(embeddings, dtype=np.float32)

            # Normalizar L2 para que el coseno sea producto punto
            norms = np.linalg.norm(self._faq_embeddings, axis=1, keepdims=True)
            self._faq_embeddings = self._faq_embeddings / np.maximum(norms, 1e-12)
            self._index_to_faq = faq_mapping

    def search(self, query: str) -> Tuple[Optional[FaqItem], float, float]:
        """
        Búsqueda vectorial Nivel 1.
        Retorna: (FaqItem si similitud >= threshold, score_maximo, latencia_ms)
        """
        self._initialize_index()
        t0 = time.time()

        model = self._get_model()
        query_emb = np.array(list(model.embed([query]))[0], dtype=np.float32)
        norm = np.linalg.norm(query_emb)
        if norm > 0:
            query_emb = query_emb / norm

        # Producto punto contra todas las variaciones indexadas (~10ms)
        scores = np.dot(self._faq_embeddings, query_emb)
        best_idx = int(np.argmax(scores))
        best_score = float(scores[best_idx])
        latency_ms = (time.time() - t0) * 1000

        matched_faq = self._index_to_faq[best_idx]
        if best_score >= self.threshold:
            return matched_faq, best_score, latency_ms

        return None, best_score, latency_ms


rag_engine = RagEngine(threshold=0.80)
