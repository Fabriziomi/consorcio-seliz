import pytest
from services.tev1_router import tev1_router, Tev1Decision
from engine.graph import build_decision_graph
from engine.state import ChatState


def test_tev1_payment_request_explicit():
    decision, _ = tev1_router.route("Hola, ¿me podrían pasar el CBU y alias para pagar las expensas?")
    assert decision == Tev1Decision.B_PAYMENTS

    decision2, _ = tev1_router.route("¿Cuál es la cuenta bancaria donde se transfiere?")
    assert decision2 == Tev1Decision.B_PAYMENTS


def test_tev1_cuenta_word_not_falsely_payments():
    # Mensajes con la palabra "cuenta" que son reclamos técnicos NO deben ser B_PAYMENTS
    msg = "Tengan en cuenta que el ascensor del piso 4 hace un ruido terrible y no anda bien"
    decision, _ = tev1_router.route(msg)
    assert decision != Tev1Decision.B_PAYMENTS
    assert decision == Tev1Decision.D_TICKET_NEUTRAL


def test_tev1_pagar_word_not_falsely_payments():
    # Mensajes con "pagar" en contexto de queja o reclamo NO deben ser B_PAYMENTS
    msg = "No puedo pagar un flete por escalera si el ascensor sigue roto, arréglenlo urgente"
    decision, _ = tev1_router.route(msg)
    assert decision != Tev1Decision.B_PAYMENTS
    assert decision == Tev1Decision.D_TICKET_NEUTRAL


def test_tev1_payment_confirmation():
    msg = "Hola, ya transferí las expensas de la unidad 4B, te adjunto el comprobante de transferencia"
    decision, _ = tev1_router.route(msg)
    assert decision == Tev1Decision.E_PAYMENT_CONFIRMATION


def test_tev1_mudanza_intent():
    msg = "¿Qué días y horarios se puede hacer mudanza con flete en el edificio?"
    decision, _ = tev1_router.route(msg)
    assert decision == Tev1Decision.F_MUDANZA


def test_decision_graph_legit_short_apartment_not_noise():
    graph = build_decision_graph()
    # Unidades funcionales cortas o confirmaciones NO deben descartarse como ruido
    for short_valid in ["4B", "1A", "PB", "1240", "si", "no"]:
        state = ChatState(phone="+5491100000000", user_message=short_valid)
        result = graph.invoke(state)
        assert result["is_noise"] is False, f"'{short_valid}' no debería ser considerado ruido"


def test_decision_graph_complaint_does_not_trigger_random_attribute():
    graph = build_decision_graph()
    state = ChatState(
        phone="+5491100000000",
        user_message="En el palier del 3ero hay una bolsa de basura rota que deja un olor tremendo",
        atributos_dinamicos={
            "horario_retiro_basura": {
                "etiqueta": "Horario de Basura",
                "valor": "De 20 a 21 hs",
                "es_publico": True,
            }
        },
    )
    result = graph.invoke(state)
    # No debe disparar CONSULTA_ATRIBUTO_PUBLICO porque es una queja/reclamo
    assert result.get("intent") != "CONSULTA_ATRIBUTO_PUBLICO"
