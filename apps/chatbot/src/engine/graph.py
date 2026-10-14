import re
from langgraph.graph import StateGraph, END
from engine.state import ChatState
from guardrails.schedule_evaluator import evaluate_schedule, ScheduleStatus
from guardrails.emergency_filter import detect_emergency
from services.templates import render_template
from services.rag_engine import rag_engine
from services.tev1_router import tev1_router, Tev1Decision

CORDIAL_TOKENS = {
    "ok", "okey", "oka", "dale", "listo", "gracias", "muchas", "mil", "barbaro", "bárbaro",
    "buen", "finde", "fin", "de", "semana", "saludos", "chau", "buenas", "bueno", "joya",
    "genial", "perfecto", "impecable", "entendido", "graciass", "graciasss",
    "👍", "👌", "👋", "🙏"
}

GREETING_TOKENS = {
    "hola", "buen", "bueno", "buenos", "buenas", "dia", "dias", "día", "días",
    "tarde", "tardes", "noche", "noches", "que", "tal", "como", "estas", "estás", "cómo"
}

NOISE_WORDS = {"asd", "asdf", "qwe", "qwer", "zxc", "jaja", "jeje", "zz", "zzz"}


def schedule_node(state: ChatState) -> dict:
    if state.schedule_status:
        return {"schedule_status": state.schedule_status}
    status = evaluate_schedule()
    return {"schedule_status": status.value}


def emergency_node(state: ChatState) -> dict:
    is_emergency, reasons = detect_emergency(state.user_message)
    return {
        "is_emergency": is_emergency,
        "emergency_reasons": reasons,
    }


def content_guardrails_node(state: ChatState) -> dict:
    """
    Evalúa la calidad del contenido del mensaje:
    1. Cierre cordial / Agradecimiento -> Silencio inteligente.
    2. Ruido real / Teclazos sin sentido -> Silencio inteligente.
    3. Saludo puro sin consulta -> Bienvenida humana sin crear ticket.
    """
    raw = state.user_message.strip().lower()
    tokens = re.findall(r"[\w]+|[^\w\s]", raw)
    words = [t for t in tokens if t not in {".", "!", "?", ",", ";", ":", "-", "¡", "¿", "_", "/", "\\"}]
    clean_letters = re.sub(r"[^\w]", "", raw)

    # 1. Comprobaciones de mensajes cortos legítimos (departamento con número, afirmaciones, o pb)
    # Por ejemplo: "4B", "1A", "PB", "1240", "si", "no", "dale"
    is_legit_short = bool(
        re.match(r"^(\d{1,4}[a-zA-Z]?|[a-zA-Z]{1,2}\d{1,4}|pb|si|sí|no|ok|oka|dale)$", clean_letters)
        or re.search(r"\d+", raw)
    )

    # Filtro de ruido real: solo teclazos al azar ("asdf", "qwer", "zzzz") o caracteres sueltos sin sentido
    is_noise = False
    if not is_legit_short:
        if len(clean_letters) <= 2:
            is_noise = True
        elif clean_letters in NOISE_WORDS:
            is_noise = True
        elif len(clean_letters) >= 4 and not re.search(r"[aeiouáéíóú\d]", clean_letters):
            # Secuencia larga de puras consonantes sin dígitos ("qwrty", "zxcvb")
            is_noise = True

    if is_noise:
        return {
            "is_noise": True,
            "is_cordial_close": False,
            "is_pure_greeting": False,
        }

    # 2. Cierre cordial / Prevención de bucles ("gracias", "dale listo", "👍", "buen finde")
    is_close = len(words) <= 6 and all(t in CORDIAL_TOKENS for t in words)
    if is_close:
        return {
            "is_noise": False,
            "is_cordial_close": True,
            "is_pure_greeting": False,
        }

    # 3. Saludo puro aislado ("hola", "buenas tardes", "hola buen día")
    is_greeting = len(words) <= 4 and all(t in GREETING_TOKENS for t in words)
    return {
        "is_noise": False,
        "is_cordial_close": False,
        "is_pure_greeting": is_greeting,
    }


# --- Nivel 1: Búsqueda Vectorial RAG en FAQs Aprobadas ---
def rag_faq_node(state: ChatState) -> dict:
    faq, score, latency_ms = rag_engine.search(state.user_message)
    latencies = dict(state.latency_metrics)
    latencies["rag_faq_ms"] = round(latency_ms, 2)

    if faq:
        return {
            "rag_matched": True,
            "rag_faq_id": faq.id,
            "rag_score": round(score, 4),
            "intent": f"FAQ_{faq.categoria}",
            "response_text": faq.respuesta,
            "should_respond": True,
            "latency_metrics": latencies,
        }

    return {
        "rag_matched": False,
        "rag_score": round(score, 4),
        "latency_metrics": latencies,
    }


# --- Nivel 2: Árbitro de Decisión Cerrado (Tev1 0.8B) ---
def tev1_router_node(state: ChatState) -> dict:
    decision, latency_ms = tev1_router.route(
        state.user_message,
        is_emergency=state.is_emergency,
        is_cordial_close=state.is_cordial_close,
    )
    latencies = dict(state.latency_metrics)
    latencies["tev1_router_ms"] = round(latency_ms, 2)

    return {
        "tev1_decision": decision.value,
        "latency_metrics": latencies,
    }


def generate_emergency_response(state: ChatState) -> dict:
    msg_lower = state.user_message.lower()
    telefono_guardia = None
    if "ascensor" in msg_lower and state.consorcio_emergencia_ascensores:
        telefono_guardia = state.consorcio_emergencia_ascensores
    elif any(k in msg_lower for k in ("plomero", "agua", "caño", "inund", "filtracion", "filtración")) and state.consorcio_emergencia_plomeria:
        telefono_guardia = state.consorcio_emergencia_plomeria
    else:
        telefono_guardia = state.consorcio_telefono_guardia or "+54 9 11 6248-3302"

    response = render_template(
        "EMERGENCIA_GENERAL",
        telefono_guardia=telefono_guardia,
        user_name=state.user_name,
        nombre_consorcio=state.consorcio_nombre or "tu consorcio",
    )
    return {
        "intent": "EMERGENCIA",
        "should_respond": True,
        "response_text": response,
    }


def generate_greeting_response(state: ChatState) -> dict:
    response = render_template("SALUDO_INICIAL", user_name=state.user_name)
    return {
        "intent": "SALUDO_INICIAL",
        "should_respond": True,
        "response_text": response,
    }


def generate_payment_response(state: ChatState) -> dict:
    response = render_template(
        "EXPENSAS_PAGO_INFO",
        nombre_consorcio=state.consorcio_nombre or "Administración Dra. Ivana Seliz",
        cbu=state.consorcio_cbu or "0140000000000000000001",
        alias=state.consorcio_alias or "CONSORCIO.SELIZ.OFICIAL",
        cuit=state.consorcio_cuit or "30-71122334-5",
        email_cobranzas=state.consorcio_email_cobranzas or "cobranzas@selizadministraciones.com.ar",
        user_name=state.user_name,
        unidad_funcional=state.unidad_funcional or "tu unidad",
    )
    return {
        "intent": "EXPENSAS_DATOS_PAGO",
        "should_respond": True,
        "response_text": response,
    }


def generate_payment_confirmation_response(state: ChatState) -> dict:
    response = render_template(
        "EXPENSAS_COMPROBANTE_RECIBIDO",
        nombre_consorcio=state.consorcio_nombre or "tu consorcio",
        email_cobranzas=state.consorcio_email_cobranzas or "cobranzas@selizadministraciones.com.ar",
        user_name=state.user_name,
        unidad_funcional=state.unidad_funcional or "tu unidad",
    )
    return {
        "intent": "PAGO_REALIZADO",
        "should_respond": True,
        "response_text": response,
    }


def generate_mudanza_response(state: ChatState) -> dict:
    pautas = state.consorcio_pautas_mudanza or "Lunes a Viernes de 09:00 a 17:00 hs y Sábados de 09:00 a 13:00 hs. Presentar seguro del flete con 48 hs de antelación."
    response = render_template(
        "MUDANZA_INFO",
        nombre_consorcio=state.consorcio_nombre or "tu consorcio",
        pautas_mudanza=pautas,
        user_name=state.user_name,
    )
    return {
        "intent": "CONSULTA_MUDANZA",
        "should_respond": True,
        "response_text": response,
    }


def generate_off_hours_response(state: ChatState) -> dict:
    msg_lower = state.user_message.lower()

    # 1. Si el mensaje es una queja, avería o reclamo técnico, NO devolver atributos informativos al azar
    is_complaint = any(
        term in msg_lower
        for term in (
            "roto", "rotos", "rota", "rotas", "no anda", "no funciona",
            "olor", "sucio", "sucia", "tirada", "tirado", "perdida", "pérdida",
            "gotea", "filtracion", "filtración", "humedad", "inund", "desborde",
            "queja", "molesto", "molesta", "ruido", "averi", "falta", "reclamo",
            "no limpian", "no limpiaron", "no anda bien", "descompuesto"
        )
    )

    # 2. Solo evaluar atributos dinámicos si NO es reclamo y contiene intención de consulta informativa
    if not is_complaint and state.atributos_dinamicos:
        is_query = any(q in msg_lower for q in ("que", "qué", "cual", "cuál", "donde", "dónde", "como", "cómo", "cuando", "cuándo", "hora", "horario", "quien", "quién", "saber", "consulta", "info"))
        for clave, info in state.atributos_dinamicos.items():
            etiqueta = info.get("etiqueta", clave).lower()
            palabras = [w for w in (clave.split("_") + etiqueta.split()) if len(w) >= 4 and w not in ("para", "este", "esta", "codigo", "código", "ubicacion", "ubicación")]
            if is_query and any(p in msg_lower for p in palabras):
                if info.get("es_publico", False):
                    resp = render_template(
                        "ATRIBUTO_DINAMICO_INFO",
                        user_name=state.user_name,
                        nombre_consorcio=state.consorcio_nombre or "tu consorcio",
                        etiqueta_atributo=info.get("etiqueta", clave),
                        valor_atributo=info.get("valor", ""),
                    )
                    return {
                        "intent": "CONSULTA_ATRIBUTO_PUBLICO",
                        "should_respond": True,
                        "response_text": resp,
                    }
                else:
                    resp = render_template(
                        "ATRIBUTO_SEGURIDAD_RESTRINGIDO",
                        user_name=state.user_name,
                        nombre_consorcio=state.consorcio_nombre or "tu consorcio",
                        etiqueta_atributo=info.get("etiqueta", clave),
                        unidad=state.unidad_funcional or "tu unidad",
                    )
                    return {
                        "intent": "CONSULTA_ATRIBUTO_RESTRINGIDO",
                        "should_respond": True,
                        "response_text": resp,
                    }

    if not state.consorcio_id and not state.consorcio_nombre:
        response = render_template(
            "FUERA_HORARIO_SOLICITAR_EDIFICIO",
            user_name=state.user_name,
        )
        return {
            "intent": "FUERA_HORARIO_TICKET",
            "should_respond": True,
            "response_text": response,
        }

    response = render_template(
        "FUERA_HORARIO",
        user_name=state.user_name,
        nombre_consorcio=state.consorcio_nombre or "tu consorcio",
    )
    return {
        "intent": "FUERA_HORARIO_TICKET",
        "should_respond": True,
        "response_text": response,
    }


def generate_silent_response(state: ChatState) -> dict:
    reason = "Silencio programado"
    if state.schedule_status == ScheduleStatus.HUMAN_OFFICE_HOURS.value:
        reason = "Horario laboral humano activo (Ivana atiende en persona)"
    elif state.schedule_status == ScheduleStatus.QUIET_HOURS.value:
        reason = "Quiet Hours activas (00:00 - 07:30 hs)"
    elif state.is_noise:
        reason = "Ruido de teclado o mensaje no sustantivo (Silencio inteligente)"
    elif state.is_cordial_close or state.tev1_decision == Tev1Decision.C_CORDIAL_SILENCE.value:
        reason = "Cierre cordial / Despedida (Prevención de bucles)"

    return {
        "should_respond": False,
        "response_text": None,
        "silent_reason": reason,
    }


# Router inicial de guardrails
def route_after_guardrails(state: ChatState) -> str:
    if state.is_emergency:
        return "emergency_response"

    if state.schedule_status in (ScheduleStatus.HUMAN_OFFICE_HOURS.value, ScheduleStatus.QUIET_HOURS.value):
        return "silent_action"

    if state.is_cordial_close or state.is_noise:
        return "silent_action"

    if state.is_pure_greeting:
        return "greeting_response"

    # Si está fuera de horario hábil y el bot está activo, pasar a RAG Nivel 1
    return "rag_faq_node"


# Router después de RAG
def route_after_rag(state: ChatState) -> str:
    if state.rag_matched:
        return END  # Respuesta aprobada despachada directamente
    return "tev1_router_node"


# Router después de Tev1
def route_after_tev1(state: ChatState) -> str:
    decision = state.tev1_decision
    if decision == Tev1Decision.A_EMERGENCY.value:
        return "emergency_response"
    elif decision == Tev1Decision.B_PAYMENTS.value:
        return "payment_response"
    elif decision == Tev1Decision.E_PAYMENT_CONFIRMATION.value:
        return "payment_confirmation_response"
    elif decision == Tev1Decision.F_MUDANZA.value:
        return "mudanza_response"
    elif decision == Tev1Decision.C_CORDIAL_SILENCE.value:
        return "silent_action"
    else:
        return "off_hours_response"


# Construcción del StateGraph
def build_decision_graph():
    builder = StateGraph(ChatState)

    builder.add_node("check_schedule", schedule_node)
    builder.add_node("check_emergency", emergency_node)
    builder.add_node("check_content", content_guardrails_node)
    builder.add_node("rag_faq_node", rag_faq_node)
    builder.add_node("tev1_router_node", tev1_router_node)
    builder.add_node("emergency_response", generate_emergency_response)
    builder.add_node("greeting_response", generate_greeting_response)
    builder.add_node("payment_response", generate_payment_response)
    builder.add_node("payment_confirmation_response", generate_payment_confirmation_response)
    builder.add_node("mudanza_response", generate_mudanza_response)
    builder.add_node("off_hours_response", generate_off_hours_response)
    builder.add_node("silent_action", generate_silent_response)

    builder.set_entry_point("check_schedule")
    builder.add_edge("check_schedule", "check_emergency")
    builder.add_edge("check_emergency", "check_content")

    builder.add_conditional_edges(
        "check_content",
        route_after_guardrails,
        {
            "emergency_response": "emergency_response",
            "silent_action": "silent_action",
            "greeting_response": "greeting_response",
            "rag_faq_node": "rag_faq_node",
        }
    )

    builder.add_conditional_edges(
        "rag_faq_node",
        route_after_rag,
        {
            END: END,
            "tev1_router_node": "tev1_router_node",
        }
    )

    builder.add_conditional_edges(
        "tev1_router_node",
        route_after_tev1,
        {
            "emergency_response": "emergency_response",
            "payment_response": "payment_response",
            "payment_confirmation_response": "payment_confirmation_response",
            "mudanza_response": "mudanza_response",
            "silent_action": "silent_action",
            "off_hours_response": "off_hours_response",
        }
    )

    builder.add_edge("emergency_response", END)
    builder.add_edge("greeting_response", END)
    builder.add_edge("payment_response", END)
    builder.add_edge("payment_confirmation_response", END)
    builder.add_edge("mudanza_response", END)
    builder.add_edge("off_hours_response", END)
    builder.add_edge("silent_action", END)

    return builder.compile()


decision_graph = build_decision_graph()
