from datetime import datetime
from guardrails.schedule_evaluator import evaluate_schedule, ScheduleStatus
from guardrails.emergency_filter import detect_emergency
from engine.graph import build_decision_graph
from engine.state import ChatState


def test_emergency_detection():
    # Caso 1: Olor a gas
    is_em, reasons = detect_emergency("Hola Ivana, hay olor a gas en el palier")
    assert is_em is True
    assert len(reasons) > 0

    # Caso 2: Atrapados en ascensor
    is_em, reasons = detect_emergency("Urgente, hay dos personas atrapadas en el ascensor de Torre Lavalle")
    assert is_em is True

    # Caso 3: Caño maestro roto
    is_em, reasons = detect_emergency("Se rompió el caño maestro roto y se inunda todo")
    assert is_em is True

    # Caso 4: Consulta normal (No es emergencia)
    is_em, reasons = detect_emergency("Buenas tardes, me pasan el CBU para transferir las expensas?")
    assert is_em is False
    assert len(reasons) == 0


def test_schedule_evaluation_quiet_hours():
    # 03:30 AM en un día de semana -> Quiet Hours
    night_time = datetime(2026, 10, 14, 3, 30, 0)
    status = evaluate_schedule(night_time)
    assert status == ScheduleStatus.QUIET_HOURS


def test_schedule_evaluation_human_hours():
    # Miércoles a las 14:30 hs -> Horario laboral humano
    human_time = datetime(2026, 10, 14, 14, 30, 0)
    status = evaluate_schedule(human_time)
    assert status == ScheduleStatus.HUMAN_OFFICE_HOURS


def test_schedule_evaluation_off_hours():
    # Miércoles a las 20:00 hs -> Fuera de horario (Bot activo)
    off_time = datetime(2026, 10, 14, 20, 0, 0)
    status = evaluate_schedule(off_time)
    assert status == ScheduleStatus.BOT_ACTIVE_OFF_HOURS


def test_decision_graph_emergency_bypass():
    graph = build_decision_graph()
    state = ChatState(phone="+5491100000000", user_message="Auxilio, hay olor a gas!")
    result = graph.invoke(state)
    assert result["is_emergency"] is True
    assert result["should_respond"] is True
    assert result["intent"] == "EMERGENCIA"
    assert "guardia" in result["response_text"].lower()
    assert "100" in result["response_text"]


def test_decision_graph_cordial_close_silence():
    graph = build_decision_graph()
    state = ChatState(phone="+5491100000000", user_message="Muchas gracias! 👍")
    result = graph.invoke(state)
    assert result["is_cordial_close"] is True
    assert result["should_respond"] is False
    assert "Cierre cordial" in result["silent_reason"]


def test_decision_graph_noise_silence():
    graph = build_decision_graph()
    # Letras sueltas o tecleos accidentales
    for noise_text in ["asd", "a", "da", "ad", "..."]:
        state = ChatState(phone="+5491100000000", user_message=noise_text)
        result = graph.invoke(state)
        assert result["is_noise"] is True
        assert result["should_respond"] is False
        assert "Ruido de teclado" in result["silent_reason"]


def test_decision_graph_pure_greeting():
    graph = build_decision_graph()
    state = ChatState(phone="+5491100000000", user_name="Carlos Méndez", user_message="hola")
    result = graph.invoke(state)
    assert result["is_pure_greeting"] is True
    assert result["should_respond"] is True
    assert result["intent"] == "SALUDO_INICIAL"
    assert "Hola Carlos" in result["response_text"]
    assert "ayudar" in result["response_text"].lower()


def test_rag_semantic_search_hit():
    from services.rag_engine import rag_engine
    faq, score, latency_ms = rag_engine.search("A qué hora se puede hacer una mudanza?")
    assert faq is not None
    assert faq.id == "faq-mudanzas-horarios"
    assert score >= 0.82
    assert latency_ms < 100.0  # Ultra-rápido en CPU (< 100ms)


def test_decision_graph_rag_faq_resolution():
    graph = build_decision_graph()
    state = ChatState(phone="+5491100000000", user_message="En qué horario se saca la basura?")
    result = graph.invoke(state)
    assert result["rag_matched"] is True
    assert result["rag_faq_id"] == "faq-basura-horarios"
    assert result["should_respond"] is True
    assert "residuos" in result["response_text"].lower()


def test_decision_graph_tev1_payment_routing():
    graph = build_decision_graph()

    # 1. Sin consorcio identificado: solicita edificio y unidad para evitar filtración de CBU
    state_unknown = ChatState(phone="+5491100000000", user_message="Por favor me pasan el CBU para transferir?")
    result_unknown = graph.invoke(state_unknown)
    assert result_unknown["should_respond"] is True
    assert result_unknown["tev1_decision"] == "B"
    assert result_unknown["intent"] == "SOLICITAR_CONSORCIO_PAGO"
    assert "edificio" in result_unknown["response_text"].lower()

    # 2. Con consorcio identificado: provee CBU y Alias exactos del consorcio
    state_known = ChatState(
        phone="+5491100000000",
        user_message="Por favor me pasan el CBU para transferir?",
        consorcio_id="cons-callao-2334",
        consorcio_nombre="Consorcio Callao 2334",
        consorcio_cbu="0140000000000000000002",
        consorcio_alias="CALLAO.2334.EXPENSAS",
    )
    result_known = graph.invoke(state_known)
    assert result_known["should_respond"] is True
    assert result_known["tev1_decision"] == "B"
    assert "0140000000000000000002" in result_known["response_text"]
    assert "CALLAO.2334.EXPENSAS" in result_known["response_text"]


def test_decision_graph_multiturn_payment_resolution():
    graph = build_decision_graph()

    # Turno 2 multi-turno: El bot esperaba edificio para pago (pending_intent) y el vecino responde "Callao 2334 7A"
    state_turn2 = ChatState(
        phone="+5491100000000",
        user_message="Callao 2334 7A",
        pending_intent="SOLICITAR_CONSORCIO_PAGO",
        consorcio_id="cons-callao-2334",
        consorcio_nombre="Consorcio Callao 2334",
        consorcio_cbu="0140000000000000000002",
        consorcio_alias="CALLAO.2334.EXPENSAS",
        unidad_funcional="7° A",
    )
    result_turn2 = graph.invoke(state_turn2)
    assert result_turn2["should_respond"] is True
    assert result_turn2["intent"] == "EXPENSAS_DATOS_PAGO"
    assert "0140000000000000000002" in result_turn2["response_text"]
    assert "CALLAO.2334.EXPENSAS" in result_turn2["response_text"]
