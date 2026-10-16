from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class FSMState(str, Enum):
    IDLE = "IDLE"
    ONBOARDING_DATOS = "ONBOARDING_DATOS"
    SOLICITANDO_EDIFICIO = "SOLICITANDO_EDIFICIO"
    ESPERANDO_SOLO_UNIDAD = "ESPERANDO_SOLO_UNIDAD"


class Intencion(str, Enum):
    CONSULTA_EXPENSAS = "CONSULTA_EXPENSAS"
    RECLAMO_TECNICO = "RECLAMO_TECNICO"
    EMERGENCIA_GRAVE = "EMERGENCIA_GRAVE"
    AVISO_PAGO_REALIZADO = "AVISO_PAGO_REALIZADO"
    MUDANZA = "MUDANZA"
    CIERRE_CORDIAL = "CIERRE_CORDIAL"
    INTENCION_AMBIGUA = "INTENCION_AMBIGUA"
    OTRO = "OTRO"


class DecisionResultado(BaseModel):
    intencion: str
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    probabilities: Dict[str, float] = Field(default_factory=dict)
    consorcio_mencionado: Optional[str] = None
    consorcio_confidence: float = 0.0
    contiene_unidad: bool = False
    unidad_funcional: Optional[str] = None
    is_emergency: bool = False
    model_used: str = ""
    latency_ms: float = 0.0
    is_fallback: bool = False


class FSMContext(BaseModel):
    pending_intent: Optional[str] = None
    retry_count: int = 0
    has_attachment: bool = False
    temp_consorcio_id: Optional[str] = None
    temp_unidad: Optional[str] = None
    last_template_sent: Optional[str] = None
    last_sent_at: Optional[datetime] = None


class FSMTransitionResult(BaseModel):
    nuevo_estado: FSMState
    nuevo_contexto: FSMContext
    template_key: Optional[str] = None
    template_rendered: Optional[str] = None
    template_params: Dict[str, Any] = Field(default_factory=dict)
    needs_human_review: bool = False
    early_bind_consorcio_id: Optional[str] = None
    early_bind_unidad: Optional[str] = None
    silencio: bool = False
    razon_silencio: Optional[str] = None
