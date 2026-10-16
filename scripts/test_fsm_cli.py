import asyncio
import os
import sys
from datetime import datetime, timezone

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CHATBOT_SRC = os.path.join(PROJECT_ROOT, "apps", "chatbot", "src")
if CHATBOT_SRC not in sys.path:
    sys.path.insert(0, CHATBOT_SRC)

from dotenv import load_dotenv

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

from engine.fsm import ConversationFSM
from engine.state_models import FSMState, FSMContext
from services.openrouter_client import OpenRouterClient
from services.templates import validate_templates_on_startup

CONSORCIOS_CATALOG = [
    {
        "id": "cons-corrientes-lavalle",
        "nombre": "Consorcio Corrientes y Lavalle",
        "direccion": "Av. Corrientes 1240 / Lavalle 1241, CABA",
        "cbu_bancario": "0140000000000000000001",
        "alias_bancario": "CONSORCIO.LAVALLE.OFICIAL",
        "cuit": "30-71000001-1",
        "email_cobranzas": "cobranzas.lavalle@selizadministraciones.com.ar",
        "telefono_porteria": "+54 9 11 4371-0001",
        "emergencia_ascensores": "+54 9 11 4444-1111",
        "emergencia_plomeria": "+54 9 11 4444-2222",
        "pautas_mudanza": "• Días hábiles de 09:00 a 17:00 hs con reserva previa de 48 hs.",
    },
    {
        "id": "cons-callao-2334",
        "nombre": "Consorcio Callao 2334",
        "direccion": "Av. Callao 2334, Recoleta, CABA",
        "cbu_bancario": "0140000000000000000002",
        "alias_bancario": "CALLAO.2334.EXPENSAS",
        "cuit": "30-71000002-2",
        "email_cobranzas": "callao2334@selizadministraciones.com.ar",
        "telefono_porteria": "+54 9 11 4801-9999",
        "emergencia_ascensores": "+54 9 11 4444-3333",
        "emergencia_plomeria": "+54 9 11 4444-4444",
        "pautas_mudanza": "• Lunes a viernes de 10:00 a 16:00 hs. Flete con seguro obligatorio.",
    },
]


async def interactive_simulator():
    print("=" * 80)
    print("SIMULADOR CLI DE CONVERSACIÓN — CONVERSATION FSM + JEV 1.14")
    print("Administración Dra. Ivana Seliz")
    print("=" * 80)

    validate_templates_on_startup()
    client = OpenRouterClient()

    # Estado inicial de la simulación
    state = FSMState.IDLE
    context = FSMContext()
    contact = {
        "id": "test-user-1",
        "telefono_wa": "+5491199887766",
        "nombre_completo": "Vecino Prueba",
        "consorcio_id": None,
        "unidad_funcional": None,
    }
    is_quiet_hours = False
    historial_len = 0

    print("Comandos disponibles en el simulador:")
    print("  /perfil <vacio|parcial|completo> : Cambiar perfil de contacto simulado")
    print("  /quiet                           : Alternar franja nocturna Quiet Hours")
    print("  /reset                           : Reiniciar FSM y contexto a IDLE")
    print("  /exit                            : Salir")
    print("-" * 80)

    while True:
        consorcio_info = next((c for c in CONSORCIOS_CATALOG if c["id"] == contact.get("consorcio_id")), None)

        print(f"\n[ESTADO: {state.value}] | [EDIFICIO: {contact.get('consorcio_id') or '-'}] | [UNIDAD: {contact.get('unidad_funcional') or '-'}] | [QUIET: {is_quiet_hours}]")
        user_input = input("Vecino > ").strip()

        if not user_input:
            continue

        if user_input.lower() == "/exit":
            print("Cerrando simulador.")
            break

        if user_input.lower() == "/reset":
            state = FSMState.IDLE
            context = FSMContext()
            print("FSM reiniciada a IDLE.")
            continue

        if user_input.lower() == "/quiet":
            is_quiet_hours = not is_quiet_hours
            print(f"Quiet Hours alternado a: {is_quiet_hours}")
            continue

        if user_input.lower().startswith("/perfil"):
            parts = user_input.split()
            mode = parts[1] if len(parts) > 1 else "vacio"
            if mode == "completo":
                contact["consorcio_id"] = "cons-callao-2334"
                contact["unidad_funcional"] = "4° B"
            elif mode == "parcial":
                contact["consorcio_id"] = "cons-callao-2334"
                contact["unidad_funcional"] = None
            else:
                contact["consorcio_id"] = None
                contact["unidad_funcional"] = None
            print(f"Perfil cambiado a: consorcio={contact['consorcio_id']}, unidad={contact['unidad_funcional']}")
            continue

        historial_len += 1

        # 1. Clasificación con Jev (o Gemini Fallback)
        has_c = bool(contact.get("consorcio_id"))
        has_u = bool(contact.get("unidad_funcional"))

        decision = await client.classify_intent(
            text=user_input,
            has_consorcio=has_c,
            has_unidad=has_u,
            consorcios_catalog=CONSORCIOS_CATALOG,
        )

        print(f"-> Jev Decision: intent={decision.intencion} (conf={decision.confidence:.2f}, lat={decision.latency_ms:.0f}ms, fallback={decision.is_fallback})")
        if decision.consorcio_mencionado:
            print(f"-> Consorcio detectado: {decision.consorcio_mencionado}")
        if decision.contiene_unidad:
            print(f"-> Unidad detectada: {decision.unidad_funcional}")

        # 2. Transición FSM
        resultado = ConversationFSM.process_step(
            state=state,
            context=context,
            decision=decision,
            contact_profile=contact,
            consorcio_data=consorcio_info,
            incoming_text=user_input,
            is_quiet_hours=is_quiet_hours,
            historial_len=historial_len,
        )

        # Aplicar Early Binding si hubo datos nuevos
        if resultado.early_bind_consorcio_id:
            contact["consorcio_id"] = resultado.early_bind_consorcio_id
            consorcio_info = next((c for c in CONSORCIOS_CATALOG if c["id"] == contact.get("consorcio_id")), None)
            print(f"-> [Early Binding] Consorcio persistido: {resultado.early_bind_consorcio_id}")

        if resultado.early_bind_unidad:
            contact["unidad_funcional"] = resultado.early_bind_unidad
            print(f"-> [Early Binding] Unidad persistida: {resultado.early_bind_unidad}")

        # Actualizar estado de la conversación
        state = resultado.nuevo_estado
        context = resultado.nuevo_contexto

        print("-" * 40)
        if resultado.silencio:
            print(f"Bot (Silencio): [NO RESPONDE - {resultado.razon_silencio}]")
        else:
            print(f"Bot (Plantilla '{resultado.template_key}'):\n{resultado.template_rendered}")
        print(f"Needs Human Review: {resultado.needs_human_review}")
        print("-" * 40)


if __name__ == "__main__":
    asyncio.run(interactive_simulator())
