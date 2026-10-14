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
    2. Ruido / Caracteres sueltos / Spam -> Silencio inteligente.
    3. Saludo puro sin consulta -> Bienvenida humana sin crear ticket.
    """
    raw = state.user_message.strip().lower()
    tokens = re.findall(r"[\w]+|[^\w\s]", raw)
    words = [t for t in tokens if t not in {".", "!", "?", ",", ";", ":", "-", "¡", "¿", "_", "/", "\\"}]
    clean_letters = re.sub(r"[^\w]", "", raw)

    # 1. Filtro de ruido / Teclazos al azar ("a", "asd", "da", "...")
    is_noise = False
    if len(clean_letters) < 3:
        is_noise = True
    elif clean_letters in NOISE_WORDS:
        is_noise = True
    elif len(clean_letters) >= 3 and not re.search(r"[aeiouáéíóú]", clean_letters):
        is_noise = True

    if is_noise:
        return {
            "is_noise": True,
            "is_cordial_close": False,
            "is_pure_greeting": False,
        }

    # 2. Cierre cordial / Prevención de bucles ("gracias", "dale listo", "👍")
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
    telefono_guardia = "+54 9 11 6248-3302"
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
        cbu="0140000000000000000001",
        alias="CONSORCIO.SELIZ.OFICIAL",
        cuit="30-71122334-5",
        email_cobranzas="cobranzas@selizadministraciones.com.ar",
        user_name=state.user_name,
        unidad_funcional=state.unidad_funcional or "tu unidad",
    )
    return {
        "intent": "EXPENSAS_DATOS_PAGO",
        "should_respond": True,
        "response_text": response,
    }


def generate_off_hours_response(state: ChatState) -> dict:
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
            "silent_action": "silent_action",
            "off_hours_response": "off_hours_response",
        }
    )

    builder.add_edge("emergency_response", END)
    builder.add_edge("greeting_response", END)
    builder.add_edge("payment_response", END)
    builder.add_edge("off_hours_response", END)
    builder.add_edge("silent_action", END)

    return builder.compile()


decision_graph = build_decision_graph()
