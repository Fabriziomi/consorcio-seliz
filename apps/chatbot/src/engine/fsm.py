"""
Motor determinista de Máquina de Estados Finitos (ConversationFSM)
para la atención conversacional de consorcios — Dra. Ivana Seliz Administraciones.

Principios:
1. Determinismo absoluto: La lógica de negocio y las transiciones pertenecen a este código.
2. Cero alucinaciones: Solo respuestas mediante plantillas institucionales oficiales.
3. Resiliencia: Estados acotados (IDLE, ONBOARDING_DATOS, SOLICITANDO_EDIFICIO, ESPERANDO_SOLO_UNIDAD).
4. Auditoría estructurada en fsm_audit.log.
"""

import json
import logging
import os
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

from engine.state_models import (
    FSMState,
    FSMContext,
    DecisionResultado,
    FSMTransitionResult,
    Intencion,
)
from services.templates import render_template

logger = logging.getLogger(__name__)

AUDIT_LOG_FILE = "fsm_audit.log"
ESCAPE_COMMANDS = {"0", "menu", "reiniciar", "inicio", "cancelar", "reset", "salir"}


class ConversationFSM:
    """
    Máquina de Estados Finitos Pura para la gestión de conversaciones de consorcios.
    Desacoplada de I/O, Webhooks y Base de Datos.
    """

    @staticmethod
    def is_escape_command(text: str) -> bool:
        clean = text.strip().lower()
        return clean in ESCAPE_COMMANDS

    @staticmethod
    def build_telefonos_guardia(consorcio: Optional[Dict[str, Any]]) -> str:
        if not consorcio:
            return "• Guardia general administración: +54 9 11 6248-3302"

        lines = []
        porteria = consorcio.get("telefono_porteria")
        ascensores = consorcio.get("emergencia_ascensores")
        plomeria = consorcio.get("emergencia_plomeria")

        if porteria:
            lines.append(f"• Portería / Guardia: {porteria}")
        if ascensores:
            lines.append(f"• Guardia Ascensores: {ascensores}")
        if plomeria:
            lines.append(f"• Urgencias Plomería / Gas: {plomeria}")

        if not lines:
            lines.append("• Guardia general administración: +54 9 11 6248-3302")

        return "\n".join(lines)

    @classmethod
    def process_step(
        cls,
        state: FSMState,
        context: FSMContext,
        decision: DecisionResultado,
        contact_profile: Dict[str, Any],
        consorcio_data: Optional[Dict[str, Any]] = None,
        incoming_text: str = "",
        is_quiet_hours: bool = False,
        historial_len: int = 0,
        now: Optional[datetime] = None,
    ) -> FSMTransitionResult:
        current_time = now or datetime.now(timezone.utc)
        user_name = contact_profile.get("nombre_completo") or ""

        # ----------------------------------------------------------------------
        # 1. COMANDOS DE ESCAPE ('0', 'menu', 'reiniciar', 'inicio', 'cancelar')
        # ----------------------------------------------------------------------
        if cls.is_escape_command(incoming_text):
            nuevo_ctx = FSMContext()
            template_key = "INTENCION_AMBIGUA"
            rendered = render_template(template_key, historial_len=historial_len, user_name=user_name)
            res = FSMTransitionResult(
                nuevo_estado=FSMState.IDLE,
                nuevo_contexto=nuevo_ctx,
                template_key=template_key,
                template_rendered=rendered,
                needs_human_review=False,
            )
            cls._log_audit(state, res, decision, contact_profile, current_time)
            return res

        # ----------------------------------------------------------------------
        # 2. QUIET HOURS (00:00 A 07:30 HS)
        # ----------------------------------------------------------------------
        if is_quiet_hours and not decision.is_emergency:
            # Silencio nocturno total para no importunar al vecino.
            res = FSMTransitionResult(
                nuevo_estado=state,
                nuevo_contexto=context,
                template_key=None,
                template_rendered=None,
                needs_human_review=True,
                silencio=True,
                razon_silencio="Quiet Hours (00:00 a 07:30)",
            )
            cls._log_audit(state, res, decision, contact_profile, current_time)
            return res

        # Consorcio y unidad conocidos
        consorcio_id = contact_profile.get("consorcio_id") or context.temp_consorcio_id
        unidad_funcional = contact_profile.get("unidad_funcional") or context.temp_unidad

        # Si la decisión aporta datos nuevos confiables (Early Binding)
        early_bind_c = None
        early_bind_u = None

        if decision.consorcio_mencionado and decision.consorcio_mencionado not in (
            "OTRO_NO_ADMINISTRADO",
            "NINGUNO",
        ):
            early_bind_c = decision.consorcio_mencionado
            consorcio_id = early_bind_c

        if decision.contiene_unidad and decision.unidad_funcional:
            early_bind_u = decision.unidad_funcional
            unidad_funcional = early_bind_u

        # Construcción de parámetros para plantillas
        tpl_params: Dict[str, Any] = {
            "user_name": user_name,
            "nombre_contacto": user_name,
            "unidad": unidad_funcional or "tu unidad",
            "unidad_funcional": unidad_funcional or "tu unidad",
            "nombre_consorcio": consorcio_data.get("nombre") if consorcio_data else "tu consorcio",
            "cbu": consorcio_data.get("cbu_bancario") if consorcio_data else "Dato disponible en horario de oficina",
            "alias": consorcio_data.get("alias_bancario") if consorcio_data else "Dato disponible en horario de oficina",
            "cuit": consorcio_data.get("cuit") if consorcio_data else "30-00000000-0",
            "email_cobranzas": consorcio_data.get("email_cobranzas") if consorcio_data else "cobranzas@selizadministraciones.com.ar",
            "telefonos_guardia": cls.build_telefonos_guardia(consorcio_data),
            "pautas_mudanza": consorcio_data.get("pautas_mudanza") if consorcio_data else "• Días hábiles de 09:00 a 17:00 hs con previo aviso.",
        }

        # ----------------------------------------------------------------------
        # 3. DISPATCH SEGÚN ESTADO DE LA FSM
        # ----------------------------------------------------------------------
        if state == FSMState.IDLE:
            res = cls._handle_idle(
                context, decision, consorcio_id, unidad_funcional, tpl_params, historial_len, early_bind_c, early_bind_u
            )
        elif state == FSMState.ONBOARDING_DATOS:
            res = cls._handle_onboarding_datos(
                context, decision, consorcio_id, unidad_funcional, tpl_params, historial_len, early_bind_c, early_bind_u
            )
        elif state == FSMState.SOLICITANDO_EDIFICIO:
            res = cls._handle_solicitando_edificio(
                context, decision, consorcio_id, unidad_funcional, tpl_params, historial_len, early_bind_c, early_bind_u
            )
        elif state == FSMState.ESPERANDO_SOLO_UNIDAD:
            res = cls._handle_esperando_unidad(
                context, decision, consorcio_id, unidad_funcional, tpl_params, historial_len, early_bind_c, early_bind_u
            )
        else:
            # Fallback seguro a IDLE ante estado desconocido
            res = FSMTransitionResult(
                nuevo_estado=FSMState.IDLE,
                nuevo_contexto=FSMContext(),
                template_key="INTENCION_AMBIGUA",
                template_rendered=render_template("INTENCION_AMBIGUA", historial_len=historial_len, **tpl_params),
                needs_human_review=False,
            )

        cls._log_audit(state, res, decision, contact_profile, current_time)
        return res

    # --------------------------------------------------------------------------
    # MANEJADORES DE ESTADO
    # --------------------------------------------------------------------------
    @classmethod
    def _handle_idle(
        cls,
        ctx: FSMContext,
        decision: DecisionResultado,
        consorcio_id: Optional[str],
        unidad_funcional: Optional[str],
        params: Dict[str, Any],
        historial_len: int,
        early_bind_c: Optional[str],
        early_bind_u: Optional[str],
    ) -> FSMTransitionResult:
        # Adjunto mudo sin texto
        if ctx.has_attachment and decision.intencion == Intencion.INTENCION_AMBIGUA.value:
            rendered = render_template("ADJUNTO_MUDO", historial_len=historial_len, **params)
            return FSMTransitionResult(
                nuevo_estado=FSMState.IDLE,
                nuevo_contexto=FSMContext(),
                template_key="ADJUNTO_MUDO",
                template_rendered=rendered,
                needs_human_review=True,
            )

        # Cierre cordial ('gracias', 'ok', etc.)
        if decision.intencion == Intencion.CIERRE_CORDIAL.value:
            rendered = render_template("CIERRE_CORDIAL", historial_len=historial_len, **params)
            return FSMTransitionResult(
                nuevo_estado=FSMState.IDLE,
                nuevo_contexto=FSMContext(),
                template_key="CIERRE_CORDIAL",
                template_rendered=rendered,
                needs_human_review=False,
            )

        # Intención ambigua
        if decision.intencion == Intencion.INTENCION_AMBIGUA.value:
            rendered = render_template("INTENCION_AMBIGUA", historial_len=historial_len, **params)
            return FSMTransitionResult(
                nuevo_estado=FSMState.IDLE,
                nuevo_contexto=FSMContext(),
                template_key="INTENCION_AMBIGUA",
                template_rendered=rendered,
                needs_human_review=False,
            )

        # Edificio No Administrado
        if decision.consorcio_mencionado == "OTRO_NO_ADMINISTRADO":
            rendered = render_template("EDIFICIO_NO_ADMINISTRADO", historial_len=historial_len, **params)
            return FSMTransitionResult(
                nuevo_estado=FSMState.IDLE,
                nuevo_contexto=FSMContext(),
                template_key="EDIFICIO_NO_ADMINISTRADO",
                template_rendered=rendered,
                needs_human_review=False,
            )

        # Emergencia Grave 24/7
        if decision.intencion == Intencion.EMERGENCIA_GRAVE.value:
            if consorcio_id:
                rendered = render_template("EMERGENCIA_CON_CONSORCIO", historial_len=historial_len, **params)
                return FSMTransitionResult(
                    nuevo_estado=FSMState.IDLE,
                    nuevo_contexto=FSMContext(),
                    template_key="EMERGENCIA_CON_CONSORCIO",
                    template_rendered=rendered,
                    needs_human_review=True,
                    early_bind_consorcio_id=early_bind_c,
                    early_bind_unidad=early_bind_u,
                )
            else:
                rendered = render_template("SOLICITAR_EDIFICIO_EMERGENCIA", historial_len=historial_len, **params)
                return FSMTransitionResult(
                    nuevo_estado=FSMState.SOLICITANDO_EDIFICIO,
                    nuevo_contexto=FSMContext(pending_intent=Intencion.EMERGENCIA_GRAVE.value, retry_count=0),
                    template_key="SOLICITAR_EDIFICIO_EMERGENCIA",
                    template_rendered=rendered,
                    needs_human_review=True,
                )

        # Consulta Expensas / CBU
        if decision.intencion == Intencion.CONSULTA_EXPENSAS.value:
            if consorcio_id:
                rendered = render_template("EXPENSAS_DATOS_BANCARIOS", historial_len=historial_len, **params)
                return FSMTransitionResult(
                    nuevo_estado=FSMState.IDLE,
                    nuevo_contexto=FSMContext(),
                    template_key="EXPENSAS_DATOS_BANCARIOS",
                    template_rendered=rendered,
                    needs_human_review=False,
                    early_bind_consorcio_id=early_bind_c,
                    early_bind_unidad=early_bind_u,
                )
            else:
                rendered = render_template("SOLICITAR_EDIFICIO_EXPENSAS", historial_len=historial_len, **params)
                return FSMTransitionResult(
                    nuevo_estado=FSMState.SOLICITANDO_EDIFICIO,
                    nuevo_contexto=FSMContext(pending_intent=Intencion.CONSULTA_EXPENSAS.value, retry_count=0),
                    template_key="SOLICITAR_EDIFICIO_EXPENSAS",
                    template_rendered=rendered,
                    needs_human_review=False,
                )

        # Aviso de Pago Realizado
        if decision.intencion == Intencion.AVISO_PAGO_REALIZADO.value:
            rendered = render_template("AVISO_PAGO_RECORDATORIO_EMAIL", historial_len=historial_len, **params)
            return FSMTransitionResult(
                nuevo_estado=FSMState.IDLE,
                nuevo_contexto=FSMContext(),
                template_key="AVISO_PAGO_RECORDATORIO_EMAIL",
                template_rendered=rendered,
                needs_human_review=False,
                early_bind_consorcio_id=early_bind_c,
                early_bind_unidad=early_bind_u,
            )

        # Reclamos Técnicos / Mudanza / Otros
        # Si tiene perfil completo (consorcio y unidad)
        if consorcio_id and unidad_funcional:
            tpl_key = "MUDANZA_INFO" if decision.intencion == Intencion.MUDANZA.value else "ACUSE_FORMAL_RECLAMO"
            rendered = render_template(tpl_key, historial_len=historial_len, **params)
            return FSMTransitionResult(
                nuevo_estado=FSMState.IDLE,
                nuevo_contexto=FSMContext(),
                template_key=tpl_key,
                template_rendered=rendered,
                needs_human_review=True,
                early_bind_consorcio_id=early_bind_c,
                early_bind_unidad=early_bind_u,
            )

        # Si tiene consorcio pero falta unidad
        if consorcio_id and not unidad_funcional:
            rendered = render_template("SOLICITAR_SOLO_UNIDAD", historial_len=historial_len, **params)
            return FSMTransitionResult(
                nuevo_estado=FSMState.ESPERANDO_SOLO_UNIDAD,
                nuevo_contexto=FSMContext(
                    pending_intent=decision.intencion,
                    temp_consorcio_id=consorcio_id,
                    retry_count=0,
                ),
                template_key="SOLICITAR_SOLO_UNIDAD",
                template_rendered=rendered,
                needs_human_review=True,
                early_bind_consorcio_id=early_bind_c,
            )

        # Sin consorcio ni unidad
        rendered = render_template("ONBOARDING_DATOS", historial_len=historial_len, **params)
        return FSMTransitionResult(
            nuevo_estado=FSMState.ONBOARDING_DATOS,
            nuevo_contexto=FSMContext(
                pending_intent=decision.intencion,
                retry_count=0,
            ),
            template_key="ONBOARDING_DATOS",
            template_rendered=rendered,
            needs_human_review=True,
        )

    @classmethod
    def _handle_onboarding_datos(
        cls,
        ctx: FSMContext,
        decision: DecisionResultado,
        consorcio_id: Optional[str],
        unidad_funcional: Optional[str],
        params: Dict[str, Any],
        historial_len: int,
        early_bind_c: Optional[str],
        early_bind_u: Optional[str],
    ) -> FSMTransitionResult:
        if decision.consorcio_mencionado == "OTRO_NO_ADMINISTRADO":
            rendered = render_template("EDIFICIO_NO_ADMINISTRADO", historial_len=historial_len, **params)
            return FSMTransitionResult(
                nuevo_estado=FSMState.IDLE,
                nuevo_contexto=FSMContext(),
                template_key="EDIFICIO_NO_ADMINISTRADO",
                template_rendered=rendered,
                needs_human_review=False,
            )

        # Si proporcionó ambos: consorcio y unidad
        if early_bind_c and (early_bind_u or unidad_funcional):
            pending = ctx.pending_intent or Intencion.RECLAMO_TECNICO.value
            tpl_key = "EXPENSAS_DATOS_BANCARIOS" if pending == Intencion.CONSULTA_EXPENSAS.value else "ACUSE_FORMAL_RECLAMO"
            rendered = render_template(tpl_key, historial_len=historial_len, **params)
            return FSMTransitionResult(
                nuevo_estado=FSMState.IDLE,
                nuevo_contexto=FSMContext(),
                template_key=tpl_key,
                template_rendered=rendered,
                needs_human_review=(tpl_key != "EXPENSAS_DATOS_BANCARIOS"),
                early_bind_consorcio_id=early_bind_c,
                early_bind_unidad=early_bind_u or unidad_funcional,
            )

        # Si proporcionó solo consorcio pero olvidó unidad
        if early_bind_c and not early_bind_u:
            rendered = render_template("SOLICITAR_SOLO_UNIDAD", historial_len=historial_len, **params)
            return FSMTransitionResult(
                nuevo_estado=FSMState.ESPERANDO_SOLO_UNIDAD,
                nuevo_contexto=FSMContext(
                    pending_intent=ctx.pending_intent,
                    temp_consorcio_id=early_bind_c,
                    retry_count=0,
                ),
                template_key="SOLICITAR_SOLO_UNIDAD",
                template_rendered=rendered,
                needs_human_review=True,
                early_bind_consorcio_id=early_bind_c,
            )

        # Falla intento 1 (retry_count == 0)
        if ctx.retry_count == 0:
            rendered = render_template("ONBOARDING_REINTENTO_1", historial_len=historial_len, **params)
            return FSMTransitionResult(
                nuevo_estado=FSMState.ONBOARDING_DATOS,
                nuevo_contexto=FSMContext(
                    pending_intent=ctx.pending_intent,
                    retry_count=1,
                ),
                template_key="ONBOARDING_REINTENTO_1",
                template_rendered=rendered,
                needs_human_review=True,
            )

        # Falla intento 2 (retry_count >= 1) -> Bailout
        rendered = render_template("ONBOARDING_BAILOUT", historial_len=historial_len, **params)
        return FSMTransitionResult(
            nuevo_estado=FSMState.IDLE,
            nuevo_contexto=FSMContext(),
            template_key="ONBOARDING_BAILOUT",
            template_rendered=rendered,
            needs_human_review=True,
        )

    @classmethod
    def _handle_solicitando_edificio(
        cls,
        ctx: FSMContext,
        decision: DecisionResultado,
        consorcio_id: Optional[str],
        unidad_funcional: Optional[str],
        params: Dict[str, Any],
        historial_len: int,
        early_bind_c: Optional[str],
        early_bind_u: Optional[str],
    ) -> FSMTransitionResult:
        if decision.consorcio_mencionado == "OTRO_NO_ADMINISTRADO":
            rendered = render_template("EDIFICIO_NO_ADMINISTRADO", historial_len=historial_len, **params)
            return FSMTransitionResult(
                nuevo_estado=FSMState.IDLE,
                nuevo_contexto=FSMContext(),
                template_key="EDIFICIO_NO_ADMINISTRADO",
                template_rendered=rendered,
                needs_human_review=False,
            )

        if early_bind_c:
            pending = ctx.pending_intent
            if pending == Intencion.EMERGENCIA_GRAVE.value:
                tpl_key = "EMERGENCIA_CON_CONSORCIO"
                needs_rev = True
            elif pending == Intencion.CONSULTA_EXPENSAS.value:
                tpl_key = "EXPENSAS_DATOS_BANCARIOS"
                needs_rev = False
            else:
                tpl_key = "ACUSE_FORMAL_RECLAMO"
                needs_rev = True

            rendered = render_template(tpl_key, historial_len=historial_len, **params)
            return FSMTransitionResult(
                nuevo_estado=FSMState.IDLE,
                nuevo_contexto=FSMContext(),
                template_key=tpl_key,
                template_rendered=rendered,
                needs_human_review=needs_rev,
                early_bind_consorcio_id=early_bind_c,
                early_bind_unidad=early_bind_u,
            )

        # Falla intento 1
        if ctx.retry_count == 0:
            rendered = render_template("SOLICITAR_EDIFICIO_REINTENTO", historial_len=historial_len, **params)
            return FSMTransitionResult(
                nuevo_estado=FSMState.SOLICITANDO_EDIFICIO,
                nuevo_contexto=FSMContext(
                    pending_intent=ctx.pending_intent,
                    retry_count=1,
                ),
                template_key="SOLICITAR_EDIFICIO_REINTENTO",
                template_rendered=rendered,
                needs_human_review=True,
            )

        # Falla intento 2 -> Bailout
        rendered = render_template("ONBOARDING_BAILOUT", historial_len=historial_len, **params)
        return FSMTransitionResult(
            nuevo_estado=FSMState.IDLE,
            nuevo_contexto=FSMContext(),
            template_key="ONBOARDING_BAILOUT",
            template_rendered=rendered,
            needs_human_review=True,
        )

    @classmethod
    def _handle_esperando_unidad(
        cls,
        ctx: FSMContext,
        decision: DecisionResultado,
        consorcio_id: Optional[str],
        unidad_funcional: Optional[str],
        params: Dict[str, Any],
        historial_len: int,
        early_bind_c: Optional[str],
        early_bind_u: Optional[str],
    ) -> FSMTransitionResult:
        if early_bind_u:
            pending = ctx.pending_intent or Intencion.RECLAMO_TECNICO.value
            tpl_key = "EXPENSAS_DATOS_BANCARIOS" if pending == Intencion.CONSULTA_EXPENSAS.value else "ACUSE_FORMAL_RECLAMO"
            rendered = render_template(tpl_key, historial_len=historial_len, **params)
            return FSMTransitionResult(
                nuevo_estado=FSMState.IDLE,
                nuevo_contexto=FSMContext(),
                template_key=tpl_key,
                template_rendered=rendered,
                needs_human_review=(tpl_key != "EXPENSAS_DATOS_BANCARIOS"),
                early_bind_consorcio_id=early_bind_c or consorcio_id,
                early_bind_unidad=early_bind_u,
            )

        # Falla intento 1
        if ctx.retry_count == 0:
            rendered = render_template("SOLICITAR_UNIDAD_REINTENTO", historial_len=historial_len, **params)
            return FSMTransitionResult(
                nuevo_estado=FSMState.ESPERANDO_SOLO_UNIDAD,
                nuevo_contexto=FSMContext(
                    pending_intent=ctx.pending_intent,
                    temp_consorcio_id=ctx.temp_consorcio_id or consorcio_id,
                    retry_count=1,
                ),
                template_key="SOLICITAR_UNIDAD_REINTENTO",
                template_rendered=rendered,
                needs_human_review=True,
            )

        # Falla intento 2 -> Bailout
        rendered = render_template("ONBOARDING_BAILOUT", historial_len=historial_len, **params)
        return FSMTransitionResult(
            nuevo_estado=FSMState.IDLE,
            nuevo_contexto=FSMContext(),
            template_key="ONBOARDING_BAILOUT",
            template_rendered=rendered,
            needs_human_review=True,
        )

    @classmethod
    def _log_audit(
        cls,
        estado_previo: FSMState,
        resultado: FSMTransitionResult,
        decision: DecisionResultado,
        contact: Dict[str, Any],
        current_time: datetime,
    ) -> None:
        event = {
            "timestamp": current_time.isoformat(),
            "phone": contact.get("telefono_wa", "unknown"),
            "prev_state": estado_previo.value,
            "new_state": resultado.nuevo_estado.value,
            "intent": decision.intencion,
            "confidence": decision.confidence,
            "model_used": decision.model_used,
            "latency_ms": decision.latency_ms,
            "is_emergency": decision.is_emergency,
            "template_key": resultado.template_key,
            "needs_human_review": resultado.needs_human_review,
            "silencio": resultado.silencio,
            "razon_silencio": resultado.razon_silencio,
            "early_bind_consorcio": resultado.early_bind_consorcio_id,
            "early_bind_unidad": resultado.early_bind_unidad,
        }
        try:
            with open(AUDIT_LOG_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error("Error al registrar evento en %s: %s", AUDIT_LOG_FILE, e)
