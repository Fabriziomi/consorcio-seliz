import re
from typing import Tuple, List

EMERGENCY_PATTERNS = [
    r"\b(olor a gas|fuga de gas|escape de gas)\b",
    r"\b(atrapad[oa]s? en el ascensor|encerrad[oa]s? en el ascensor|ascensor trabado con gente)\b",
    r"\b(inundaci[oó]n|ca[ñn]o maestro roto|brote de agua|se inunda todo)\b",
    r"\b(incendio|fuego|humo saliendo)\b",
    r"\b(peligro de derrumbe|desprendimiento|electrocutad[oa]|chispas en medidor)\b",
]

COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in EMERGENCY_PATTERNS]


def detect_emergency(text: str) -> Tuple[bool, List[str]]:
    """
    Evalúa de forma determinista e inmediata si el mensaje entrante
    contiene una emergencia crítica edilicia para bypass 24/7.
    Retorna: (es_emergencia: bool, motivos: List[str])
    """
    if not text:
        return False, []

    matched = []
    for pattern in COMPILED_PATTERNS:
        match = pattern.search(text)
        if match:
            matched.append(match.group(0))

    is_emergency = len(matched) > 0
    return is_emergency, matched
