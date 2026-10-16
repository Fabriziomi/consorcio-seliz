import pytest
from engine.fsm import ConversationFSM
from engine.state_models import (
    FSMState,
    FSMContext,
    DecisionResultado,
    Intencion,
)
from services.templates import render_template, validate_templates_on_startup

CONSORCIO_TEST = {
    "id": "cons-callao-2334",
    "nombre": "Consorcio Callao 2334",
    "direccion": "Av. Callao 2334",
    "cbu_bancario": "0140000000000000000002",
    "alias_bancario": "CALLAO.2334.EXPENSAS",
    "cuit": "30-71000002-2",
    "email_cobranzas": "callao2334@selizadministraciones.com.ar",
    "telefono_porteria": "+54 9 11 4801-9999",
    "emergencia_ascensores": "+54 9 11 4444-3333",
    "emergencia_plomeria": "+54 9 11 4444-4444",
}


def test_templates_validation_on_startup():
    # Valida que ninguna plantilla arroje KeyError ni errores de sintaxis
    validate_templates_on_startup()


def test_templates_round_robin_selection():
    # Variantes 0, 1 y 2 deben ser diferentes entre sí
    t0 = render_template("EXPENSAS_DATOS_BANCARIOS", historial_len=0, nombre_consorcio="Callao 2334")
    t1 = render_template("EXPENSAS_DATOS_BANCARIOS", historial_len=1, nombre_consorcio="Callao 2334")
    t2 = render_template("EXPENSAS_DATOS_BANCARIOS", historial_len=2, nombre_consorcio="Callao 2334")
    t3 = render_template("EXPENSAS_DATOS_BANCARIOS", historial_len=3, nombre_consorcio="Callao 2334")

    assert t0 != t1
    assert t1 != t2
    assert t0 == t3  # len % 3 ciclo round-robin


def test_fsm_escape_commands_force_idle():
    contact = {"nombre_completo": "Carlos", "consorcio_id": None, "unidad_funcional": None}
    decision = DecisionResultado(intencion=Intencion.OTRO.value, confidence=1.0)

    for escape_word in ["0", "menu", "reiniciar", "inicio", "cancelar", "reset"]:
        ctx = FSMContext(pending_intent="EXPENSAS", retry_count=1)
        res = ConversationFSM.process_step(
            state=FSMState.ONBOARDING_DATOS,
            context=ctx,
            decision=decision,
            contact_profile=contact,
            incoming_text=escape_word,
        )
        assert res.nuevo_estado == FSMState.IDLE
        assert res.nuevo_contexto.retry_count == 0
        assert res.nuevo_contexto.pending_intent is None


def test_fsm_quiet_hours_silence_non_emergency():
    contact = {"nombre_completo": "Carlos", "consorcio_id": "cons-callao-2334", "unidad_funcional": "4° B"}
    decision = DecisionResultado(intencion=Intencion.RECLAMO_TECNICO.value, confidence=1.0)

    res = ConversationFSM.process_step(
        state=FSMState.IDLE,
        context=FSMContext(),
        decision=decision,
        contact_profile=contact,
        consorcio_data=CONSORCIO_TEST,
        incoming_text="El ascensor hace ruido",
        is_quiet_hours=True,
    )
    assert res.silencio is True
    assert res.needs_human_review is True
    assert "Quiet Hours" in (res.razon_silencio or "")
    assert res.template_key is None


def test_fsm_quiet_hours_emergency_bypasses_silence():
    contact = {"nombre_completo": "Carlos", "consorcio_id": "cons-callao-2334", "unidad_funcional": "4° B"}
    decision = DecisionResultado(intencion=Intencion.EMERGENCIA_GRAVE.value, confidence=1.0, is_emergency=True)

    res = ConversationFSM.process_step(
        state=FSMState.IDLE,
        context=FSMContext(),
        decision=decision,
        contact_profile=contact,
        consorcio_data=CONSORCIO_TEST,
        incoming_text="Hay olor a gas tremendo",
        is_quiet_hours=True,
    )
    assert res.silencio is False
    assert res.template_key == "EMERGENCIA_CON_CONSORCIO"
    assert "4444" in (res.template_rendered or "")
    assert res.needs_human_review is True


def test_fsm_idle_expensas_with_consorcio():
    contact = {"nombre_completo": "Carlos", "consorcio_id": "cons-callao-2334", "unidad_funcional": "4° B"}
    decision = DecisionResultado(intencion=Intencion.CONSULTA_EXPENSAS.value, confidence=1.0)

    res = ConversationFSM.process_step(
        state=FSMState.IDLE,
        context=FSMContext(),
        decision=decision,
        contact_profile=contact,
        consorcio_data=CONSORCIO_TEST,
        incoming_text="Hola me pasas el CBU?",
    )
    assert res.nuevo_estado == FSMState.IDLE
    assert res.template_key == "EXPENSAS_DATOS_BANCARIOS"
    assert "0140000000000000000002" in res.template_rendered
    assert "CALLAO.2334.EXPENSAS" in res.template_rendered


def test_fsm_idle_expensas_without_consorcio_requests_building():
    contact = {"nombre_completo": "Carlos", "consorcio_id": None, "unidad_funcional": None}
    decision = DecisionResultado(intencion=Intencion.CONSULTA_EXPENSAS.value, confidence=1.0)

    res = ConversationFSM.process_step(
        state=FSMState.IDLE,
        context=FSMContext(),
        decision=decision,
        contact_profile=contact,
        incoming_text="Hola quiero pagar las expensas",
    )
    assert res.nuevo_estado == FSMState.SOLICITANDO_EDIFICIO
    assert res.nuevo_contexto.pending_intent == "CONSULTA_EXPENSAS"
    assert res.template_key == "SOLICITAR_EDIFICIO_EXPENSAS"


def test_fsm_solicitando_edificio_success():
    contact = {"nombre_completo": "Carlos", "consorcio_id": None, "unidad_funcional": None}
    ctx = FSMContext(pending_intent=Intencion.CONSULTA_EXPENSAS.value, retry_count=0)
    decision = DecisionResultado(
        intencion=Intencion.OTRO.value,
        confidence=1.0,
        consorcio_mencionado="cons-callao-2334",
    )

    res = ConversationFSM.process_step(
        state=FSMState.SOLICITANDO_EDIFICIO,
        context=ctx,
        decision=decision,
        contact_profile=contact,
        consorcio_data=CONSORCIO_TEST,
        incoming_text="Es en Callao 2334",
    )
    assert res.nuevo_estado == FSMState.IDLE
    assert res.early_bind_consorcio_id == "cons-callao-2334"
    assert res.template_key == "EXPENSAS_DATOS_BANCARIOS"
    assert "CALLAO.2334.EXPENSAS" in res.template_rendered


def test_fsm_solicitando_edificio_retry_then_bailout():
    contact = {"nombre_completo": "Carlos", "consorcio_id": None, "unidad_funcional": None}
    ctx = FSMContext(pending_intent=Intencion.CONSULTA_EXPENSAS.value, retry_count=0)
    decision = DecisionResultado(intencion=Intencion.OTRO.value, confidence=1.0, consorcio_mencionado=None)

    # Intento 1 fallido
    res1 = ConversationFSM.process_step(
        state=FSMState.SOLICITANDO_EDIFICIO,
        context=ctx,
        decision=decision,
        contact_profile=contact,
        incoming_text="No me acuerdo la calle",
    )
    assert res1.nuevo_estado == FSMState.SOLICITANDO_EDIFICIO
    assert res1.nuevo_contexto.retry_count == 1
    assert res1.template_key == "SOLICITAR_EDIFICIO_REINTENTO"

    # Intento 2 fallido -> Bailout
    res2 = ConversationFSM.process_step(
        state=FSMState.SOLICITANDO_EDIFICIO,
        context=res1.nuevo_contexto,
        decision=decision,
        contact_profile=contact,
        incoming_text="Sigo sin saber",
    )
    assert res2.nuevo_estado == FSMState.IDLE
    assert res2.template_key == "ONBOARDING_BAILOUT"
    assert res2.needs_human_review is True


def test_fsm_onboarding_datos_provides_both():
    contact = {"nombre_completo": "Carlos", "consorcio_id": None, "unidad_funcional": None}
    ctx = FSMContext(pending_intent=Intencion.RECLAMO_TECNICO.value, retry_count=0)
    decision = DecisionResultado(
        intencion=Intencion.RECLAMO_TECNICO.value,
        confidence=1.0,
        consorcio_mencionado="cons-callao-2334",
        contiene_unidad=True,
        unidad_funcional="4° B",
    )

    res = ConversationFSM.process_step(
        state=FSMState.ONBOARDING_DATOS,
        context=ctx,
        decision=decision,
        contact_profile=contact,
        consorcio_data=CONSORCIO_TEST,
        incoming_text="Soy de Callao 2334 4B",
    )
    assert res.nuevo_estado == FSMState.IDLE
    assert res.early_bind_consorcio_id == "cons-callao-2334"
    assert res.early_bind_unidad == "4° B"
    assert res.template_key == "ACUSE_FORMAL_RECLAMO"
    assert res.needs_human_review is True


def test_fsm_onboarding_datos_consorcio_only_transitions_to_esperando_unidad():
    contact = {"nombre_completo": "Carlos", "consorcio_id": None, "unidad_funcional": None}
    ctx = FSMContext(pending_intent=Intencion.RECLAMO_TECNICO.value, retry_count=0)
    decision = DecisionResultado(
        intencion=Intencion.OTRO.value,
        confidence=1.0,
        consorcio_mencionado="cons-callao-2334",
        contiene_unidad=False,
    )

    res = ConversationFSM.process_step(
        state=FSMState.ONBOARDING_DATOS,
        context=ctx,
        decision=decision,
        contact_profile=contact,
        consorcio_data=CONSORCIO_TEST,
        incoming_text="Vivo en Callao 2334",
    )
    assert res.nuevo_estado == FSMState.ESPERANDO_SOLO_UNIDAD
    assert res.early_bind_consorcio_id == "cons-callao-2334"
    assert res.template_key == "SOLICITAR_SOLO_UNIDAD"


def test_fsm_esperando_unidad_success():
    contact = {"nombre_completo": "Carlos", "consorcio_id": "cons-callao-2334", "unidad_funcional": None}
    ctx = FSMContext(pending_intent=Intencion.RECLAMO_TECNICO.value, temp_consorcio_id="cons-callao-2334", retry_count=0)
    decision = DecisionResultado(
        intencion=Intencion.OTRO.value,
        confidence=1.0,
        contiene_unidad=True,
        unidad_funcional="6° A",
    )

    res = ConversationFSM.process_step(
        state=FSMState.ESPERANDO_SOLO_UNIDAD,
        context=ctx,
        decision=decision,
        contact_profile=contact,
        consorcio_data=CONSORCIO_TEST,
        incoming_text="6A",
    )
    assert res.nuevo_estado == FSMState.IDLE
    assert res.early_bind_unidad == "6° A"
    assert res.template_key == "ACUSE_FORMAL_RECLAMO"
    assert res.needs_human_review is True


def test_fsm_edificio_no_administrado():
    contact = {"nombre_completo": "Carlos", "consorcio_id": None, "unidad_funcional": None}
    ctx = FSMContext()
    decision = DecisionResultado(
        intencion=Intencion.OTRO.value,
        confidence=1.0,
        consorcio_mencionado="OTRO_NO_ADMINISTRADO",
    )

    res = ConversationFSM.process_step(
        state=FSMState.IDLE,
        context=ctx,
        decision=decision,
        contact_profile=contact,
        incoming_text="Escribo desde Rivadavia 4500",
    )
    assert res.nuevo_estado == FSMState.IDLE
    assert res.template_key == "EDIFICIO_NO_ADMINISTRADO"
    assert res.needs_human_review is False
