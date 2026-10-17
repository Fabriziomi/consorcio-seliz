import pytest
import logging
from engine.fsm import ConversationFSM
from engine.state_models import (
    FSMState,
    FSMContext,
    DecisionResultado,
    Intencion,
)
from services.templates import render_template
from core.config import settings


def test_no_hardcoded_quiet_hours_dynamic_env(monkeypatch):
    """Verifica que la razón de silencio se compute dinámicamente desde el entorno."""
    monkeypatch.setattr(settings, "QUIET_HOURS_START", "01:30")
    monkeypatch.setattr(settings, "QUIET_HOURS_END", "06:45")

    res = ConversationFSM.process_step(
        state=FSMState.IDLE,
        context=FSMContext(),
        decision=DecisionResultado(intencion=Intencion.RECLAMO_TECNICO.value, confidence=1.0),
        contact_profile={"nombre_completo": "Test User", "consorcio_id": "c1"},
        is_quiet_hours=True,
    )
    assert res.silencio is True
    assert res.razon_silencio == "Quiet Hours (01:30 a 06:45)"
    assert "00:00 a 07:30" not in (res.razon_silencio or "")


def test_missing_telefonos_guardia_logs_error_and_no_fictitious_phone(monkeypatch, caplog):
    """Verifica que sin consorcio ni ADMIN_TELEFONO_GUARDIA, se loguea error y NO se inventa +54 9 11 6248-3302."""
    monkeypatch.setattr(settings, "ADMIN_TELEFONO_GUARDIA", None)

    with caplog.at_level(logging.ERROR):
        result = ConversationFSM.build_telefonos_guardia(None)

    assert result == ""
    assert "6248-3302" not in result
    assert any("FSM_GUARDIA_MISSING" in r.message for r in caplog.records)


def test_telefonos_guardia_uses_env_when_configured(monkeypatch):
    """Verifica que ADMIN_TELEFONO_GUARDIA configurado en entorno se utilice limpiamente."""
    monkeypatch.setattr(settings, "ADMIN_TELEFONO_GUARDIA", "+54 9 11 9999-8888")

    result = ConversationFSM.build_telefonos_guardia(None)
    assert result == "• Guardia general administración: +54 9 11 9999-8888"


def test_missing_email_cobranzas_logs_error_and_no_fictitious_email(monkeypatch, caplog):
    """Verifica que sin consorcio ni ADMIN_EMAIL_COBRANZAS, se loguea error y NO se usa cobranzas@selizadministraciones.com.ar."""
    monkeypatch.setattr(settings, "ADMIN_EMAIL_COBRANZAS", None)

    with caplog.at_level(logging.ERROR):
        res = ConversationFSM.process_step(
            state=FSMState.IDLE,
            context=FSMContext(),
            decision=DecisionResultado(intencion=Intencion.CONSULTA_EXPENSAS.value, confidence=1.0),
            contact_profile={"nombre_completo": "Test User", "consorcio_id": "cons-test"},
            consorcio_data={"id": "cons-test", "nombre": "Consorcio Test", "cbu_bancario": "123"},
            incoming_text="Quiero pagar las expensas",
        )

    assert "cobranzas@selizadministraciones.com.ar" not in (res.template_rendered or "")
    assert any("FSM_CONFIG_MISSING" in r.message and "email_cobranzas" in r.message for r in caplog.records)


def test_email_cobranzas_uses_env_when_consorcio_data_lacks_it(monkeypatch):
    """Verifica que se tome ADMIN_EMAIL_COBRANZAS si el consorcio no tiene email particular."""
    monkeypatch.setattr(settings, "ADMIN_EMAIL_COBRANZAS", "admingeneral@test.com")

    res = ConversationFSM.process_step(
        state=FSMState.IDLE,
        context=FSMContext(),
        decision=DecisionResultado(intencion=Intencion.CONSULTA_EXPENSAS.value, confidence=1.0),
        contact_profile={"nombre_completo": "Test User", "consorcio_id": "cons-test"},
        consorcio_data={"id": "cons-test", "nombre": "Consorcio Test", "cbu_bancario": "123"},
        incoming_text="Quiero pagar las expensas",
    )

    assert "admingeneral@test.com" in (res.template_rendered or "")


def test_template_render_no_hardcoded_defaults(monkeypatch, caplog):
    """Verifica que render_template no inyecte valores falsos ante parámetros faltantes."""
    monkeypatch.setattr(settings, "ADMIN_EMAIL_COBRANZAS", None)
    monkeypatch.setattr(settings, "ADMIN_TELEFONO_GUARDIA", None)

    with caplog.at_level(logging.ERROR):
        rendered = render_template("EXPENSAS_DATOS_BANCARIOS", historial_len=0)

    assert "cobranzas@selizadministraciones.com.ar" not in rendered
    assert "30-00000000-0" not in rendered
    assert "Dato disponible en horario de oficina" not in rendered
    assert any("Falta parámetro 'email_cobranzas'" in r.message for r in caplog.records)
