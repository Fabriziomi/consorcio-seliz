from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ChatState(BaseModel):
    phone: str
    user_name: Optional[str] = "Vecino"
    user_message: str
    
    # Evaluación de contexto y guardrails
    schedule_status: Optional[str] = None
    is_emergency: bool = False
    emergency_reasons: List[str] = Field(default_factory=list)
    is_cordial_close: bool = False
    is_pure_greeting: bool = False
    is_noise: bool = False
    
    # Datos de consorcio identificado
    consorcio_id: Optional[str] = None
    consorcio_nombre: Optional[str] = None
    unidad_funcional: Optional[str] = None
    
    # Enrutador Híbrido (Nivel 1: RAG FAQs & Nivel 2: Tev1 Decision Router)
    rag_matched: bool = False
    rag_faq_id: Optional[str] = None
    rag_score: Optional[float] = None
    tev1_decision: Optional[str] = None
    latency_metrics: Dict[str, float] = Field(default_factory=dict)

    # Decisión y salida
    intent: Optional[str] = None
    should_respond: bool = True
    response_text: Optional[str] = None
    silent_reason: Optional[str] = None
