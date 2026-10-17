import asyncio
import time
import os
import sys
from datetime import datetime, timezone
from typing import List, Dict, Any

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CHATBOT_SRC = os.path.join(PROJECT_ROOT, "apps", "chatbot", "src")
API_SRC = os.path.join(PROJECT_ROOT, "apps", "api", "src")
for p in (CHATBOT_SRC, API_SRC):
    if p not in sys.path:
        sys.path.insert(0, p)

from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

from engine.fsm import ConversationFSM
from engine.state_models import FSMState, FSMContext, Intencion
from services.openrouter_client import OpenRouterClient
from services.templates import validate_templates_on_startup

CONSORCIOS_CATALOG = [
    {
        "id": "cons-corrientes-lavalle",
        "nombre": "Consorcio Corrientes y Lavalle",
        "direccion": "Av. Corrientes 1240 / Lavalle 1241, CABA",
        "cbu_bancario": "0140000000000000000001",
        "alias_bancario": "CONSORCIO.LAVALLE.OFICIAL",
        "cuit": "30-71122334-5",
        "email_cobranzas": "cobranzas.lavalle@selizadministraciones.com.ar",
        "telefono_porteria": "+54 9 11 4371-0001",
        "emergencia_ascensores": "+54 9 11 4444-1111",
        "emergencia_plomeria": "+54 9 11 4444-2222",
        "pautas_mudanza": "Lunes a Viernes de 9 a 17 hs y Sabados de 9 a 13 hs. Presentar seguro flete 48hs antes.",
    },
    {
        "id": "cons-callao-2334",
        "nombre": "Consorcio Callao 2334",
        "direccion": "Av. Callao 2334, Recoleta, CABA",
        "cbu_bancario": "0140000000000000000002",
        "alias_bancario": "CALLAO.2334.EXPENSAS",
        "cuit": "30-71998877-6",
        "email_cobranzas": "callao2334@selizadministraciones.com.ar",
        "telefono_porteria": "+54 9 11 4801-9999",
        "emergencia_ascensores": "+54 9 11 4444-3333",
        "emergencia_plomeria": "+54 9 11 4444-4444",
        "pautas_mudanza": "Lunes a Viernes de 10 a 16 hs exclusivamente.",
    },
]

CONVERSATION_SCENARIOS = [
    {
        "name": "Conv 1: Consulta Expensas Multi-Turno (Vecino Nuevo)",
        "initial_contact": {
            "id": "c1",
            "nombre_completo": "Agustin Rossi",
            "telefono_wa": "+5491155443322",
            "consorcio_id": None,
            "unidad_funcional": None,
        },
        "is_quiet_hours": False,
        "turns": [
            {
                "input": "Hola buenas tardes, me podrian pasar el CBU y alias para transferir las expensas?",
                "expected_intent": "CONSULTA_EXPENSAS",
                "expected_state": "SOLICITANDO_EDIFICIO",
                "check_silence": False,
            },
            {
                "input": "Es para el edificio de Callao 2334",
                "expected_intent": None,
                "expected_state": "IDLE",
                "expected_early_consorcio": "cons-callao-2334",
                "check_silence": False,
            },
            {
                "input": "Muchas gracias, impecable la atencion!",
                "expected_intent": "CIERRE_CORDIAL",
                "expected_state": "IDLE",
                "check_silence": False,
            },
        ],
    },
    {
        "name": "Conv 2: Emergencia Critica 24/7 (Atrapados en Ascensor)",
        "initial_contact": {
            "id": "c2",
            "nombre_completo": "Beatriz Lopez",
            "telefono_wa": "+5491177889900",
            "consorcio_id": "cons-corrientes-lavalle",
            "unidad_funcional": "Torre Lavalle 8 B",
        },
        "is_quiet_hours": False,
        "turns": [
            {
                "input": "Urgente, hay dos personas atrapadas en el ascensor de Torre Lavalle entre el piso 5 y 6!",
                "expected_intent": "EMERGENCIA_GRAVE",
                "expected_state": "IDLE",
                "check_emergency": True,
                "check_silence": False,
            },
            {
                "input": "Estan bien pero muy asustados, vienen los bomberos?",
                "expected_intent": None,
                "expected_state": "IDLE",
                "check_silence": False,
            },
        ],
    },
    {
        "name": "Conv 3: Reclamo Tecnico Edilicio (Filtracion en Palier)",
        "initial_contact": {
            "id": "c3",
            "nombre_completo": "Federico Gomez",
            "telefono_wa": "+5491122334455",
            "consorcio_id": "cons-corrientes-lavalle",
            "unidad_funcional": None,
        },
        "is_quiet_hours": False,
        "turns": [
            {
                "input": "Hola, en Corrientes 1240 hay una perdida de agua en el techo del palier del piso 4",
                "expected_intent": "RECLAMO_TECNICO",
                "expected_state": "ESPERANDO_SOLO_UNIDAD",
                "check_silence": False,
            },
            {
                "input": "Es frente al 4 B",
                "expected_intent": None,
                "expected_state": "IDLE",
                "expected_early_unidad": "4° B",
                "check_silence": False,
            },
        ],
    },
    {
        "name": "Conv 4: Consulta de Mudanzas (Reglamento)",
        "initial_contact": {
            "id": "c4",
            "nombre_completo": "Mariela Paez",
            "telefono_wa": "+5491199001122",
            "consorcio_id": "cons-callao-2334",
            "unidad_funcional": "3° C",
        },
        "is_quiet_hours": False,
        "turns": [
            {
                "input": "Buenas tardes, que dias y horarios estan permitidos para hacer una mudanza?",
                "expected_intent": "MUDANZA",
                "expected_state": "IDLE",
                "check_silence": False,
            },
        ],
    },
    {
        "name": "Conv 5: Quiet Hours Nocturnas (02:30 AM)",
        "initial_contact": {
            "id": "c5",
            "nombre_completo": "Damian Ortiz",
            "telefono_wa": "+5491133445566",
            "consorcio_id": "cons-callao-2334",
            "unidad_funcional": "5° D",
        },
        "is_quiet_hours": True,
        "turns": [
            {
                "input": "Hola disculpen la hora, en el 3 C tienen la musica muy fuerte y no dejan dormir a nadie",
                "expected_intent": ("RECLAMO_TECNICO", "OTRO"),
                "expected_state": "IDLE",
                "check_silence": True,
                "check_human_review": True,
            },
        ],
    },
    {
        "name": "Conv 6: Aviso de Pago con Comprobante",
        "initial_contact": {
            "id": "c6",
            "nombre_completo": "Esteban Morales",
            "telefono_wa": "+5491166554433",
            "consorcio_id": "cons-corrientes-lavalle",
            "unidad_funcional": "Torre Corrientes 2 A",
        },
        "is_quiet_hours": False,
        "turns": [
            {
                "input": "Buenas tardes, recien transferi el pago de expensas de septiembre por 92000 pesos",
                "expected_intent": "AVISO_PAGO_REALIZADO",
                "expected_state": "IDLE",
                "check_silence": False,
            },
        ],
    },
    {
        "name": "Conv 7: Ruido y Comandos de Escape",
        "initial_contact": {
            "id": "c7",
            "nombre_completo": "Vecino Indeciso",
            "telefono_wa": "+5491111223344",
            "consorcio_id": None,
            "unidad_funcional": None,
        },
        "is_quiet_hours": False,
        "turns": [
            {
                "input": "asdfghjk",
                "expected_intent": ("INTENCION_AMBIGUA", "OTRO"),
                "check_silence": False,
            },
            {
                "input": "reiniciar",
                "expected_intent": None,
                "expected_state": "IDLE",
                "check_silence": False,
            },
        ],
    },
]


async def run_real_conversation_suite():
    validate_templates_on_startup()
    client = OpenRouterClient()

    results = []
    failures = []

    print("=" * 100)
    print("EJECUTANDO SUITE DE PRUEBAS DE CONVERSACIONES COMPLETAS REALES")
    print("Motor: OpenRouter (typesafe/jev-1.14 + Fallback Gemini 2.5 Flash) + ConversationFSM")
    print("Timestamp:", datetime.now(timezone.utc).isoformat())
    print("=" * 100)

    for scenario_idx, scenario in enumerate(CONVERSATION_SCENARIOS, 1):
        print(f"\n>>> INICIANDO ESCENARIO {scenario_idx}/{len(CONVERSATION_SCENARIOS)}: {scenario['name']}")
        contact = dict(scenario["initial_contact"])
        state = FSMState.IDLE
        context = FSMContext()
        historial_len = 0
        is_quiet = scenario["is_quiet_hours"]

        for turn_idx, turn in enumerate(scenario["turns"], 1):
            historial_len += 1
            user_msg = turn["input"]
            t_start = time.perf_counter()

            consorcio_info = next((c for c in CONSORCIOS_CATALOG if c["id"] == contact.get("consorcio_id")), None)
            has_c = bool(contact.get("consorcio_id"))
            has_u = bool(contact.get("unidad_funcional"))

            # 1. Llamada Real a Inferencia
            decision = await client.classify_intent(
                text=user_msg,
                has_consorcio=has_c,
                has_unidad=has_u,
                consorcios_catalog=CONSORCIOS_CATALOG,
            )

            target_c_id = contact.get("consorcio_id") or decision.consorcio_mencionado
            if target_c_id:
                consorcio_info = next((c for c in CONSORCIOS_CATALOG if c["id"] == target_c_id), None)

            # 2. Paso por FSM
            step_result = ConversationFSM.process_step(
                state=state,
                context=context,
                decision=decision,
                contact_profile=contact,
                consorcio_data=consorcio_info,
                incoming_text=user_msg,
                is_quiet_hours=is_quiet,
                historial_len=historial_len,
            )

            total_latency = (time.perf_counter() - t_start) * 1000

            # 3. Aplicar Early Binding
            if step_result.early_bind_consorcio_id and not contact["consorcio_id"]:
                contact["consorcio_id"] = step_result.early_bind_consorcio_id
                consorcio_info = next((c for c in CONSORCIOS_CATALOG if c["id"] == contact.get("consorcio_id")), None)

            if step_result.early_bind_unidad and not contact["unidad_funcional"]:
                contact["unidad_funcional"] = step_result.early_bind_unidad

            state_before = state
            state_after = step_result.nuevo_estado
            state = step_result.nuevo_estado
            context = step_result.nuevo_contexto

            # Validar expectativas
            turn_failures = []

            exp_intent = turn.get("expected_intent")
            if exp_intent:
                if isinstance(exp_intent, (list, tuple)):
                    if decision.intencion not in exp_intent:
                        turn_failures.append(f"Intencion inesperada: esperada={exp_intent}, obtenida={decision.intencion}")
                elif decision.intencion != exp_intent:
                    if not (exp_intent == "EMERGENCIA_GRAVE" and decision.is_emergency):
                        turn_failures.append(f"Intencion inesperada: esperada={exp_intent}, obtenida={decision.intencion}")

            if turn.get("expected_state") and state_after.value != turn["expected_state"]:
                turn_failures.append(f"Estado FSM inesperado: esperado={turn['expected_state']}, obtenido={state_after.value}")

            if "check_silence" in turn and step_result.silencio != turn["check_silence"]:
                turn_failures.append(f"Estado de silencio inesperado: esperado={turn['check_silence']}, obtenido={step_result.silencio} (razon={step_result.razon_silencio})")

            if turn.get("check_human_review") and not step_result.needs_human_review:
                turn_failures.append("needs_human_review debio ser True")

            if turn.get("check_emergency") and not decision.is_emergency:
                turn_failures.append("is_emergency debio ser True")

            record = {
                "scenario": scenario["name"],
                "turn": turn_idx,
                "input": user_msg,
                "intent": decision.intencion,
                "confidence": decision.confidence,
                "model": decision.model_used,
                "is_fallback": decision.is_fallback,
                "inference_ms": round(decision.latency_ms, 1),
                "total_ms": round(total_latency, 1),
                "state_before": state_before.value,
                "state_after": state_after.value,
                "template": step_result.template_key or "SILENCIO",
                "silencio": step_result.silencio,
                "human_review": step_result.needs_human_review,
                "early_consorcio": contact.get("consorcio_id"),
                "early_unidad": contact.get("unidad_funcional"),
                "failures": turn_failures,
                "response_preview": (step_result.template_rendered or step_result.razon_silencio or "")[:120].replace("\n", " "),
            }
            results.append(record)

            if turn_failures:
                failures.append({
                    "scenario": scenario["name"],
                    "turn": turn_idx,
                    "input": user_msg,
                    "issues": turn_failures,
                })
                print(f"  [FALLO EN TURNO {turn_idx}]: {turn_failures}")
            else:
                print(f"  [OK TURNO {turn_idx}] ({record['inference_ms']}ms - {record['model']}) -> {record['intent']} | FSM: {record['state_before']} -> {record['state_after']} | Template: {record['template']}")

    print("\n" + "=" * 100)
    print("RESUMEN DE RESULTADOS DE RENDIMIENTO Y PRECISIÓN")
    print("=" * 100)

    # Métricas agregadas
    total_turns = len(results)
    successful_turns = total_turns - len(failures)
    latencies = [r["inference_ms"] for r in results]
    avg_latency = sum(latencies) / len(latencies) if latencies else 0
    max_latency = max(latencies) if latencies else 0
    min_latency = min(latencies) if latencies else 0
    fallback_count = sum(1 for r in results if r["is_fallback"])

    latencies_sorted = sorted(latencies)
    p50 = latencies_sorted[int(len(latencies_sorted) * 0.50)]
    p90 = latencies_sorted[int(len(latencies_sorted) * 0.90)]

    print(f"Total de turnos ejecutados : {total_turns}")
    print(f"Turnos 100% exitosos      : {successful_turns}/{total_turns} ({successful_turns/total_turns*100:.1f}%)")
    print(f"Total fallos detectados   : {len(failures)}")
    print(f"Tasa de Fallback (Gemini) : {fallback_count}/{total_turns} ({fallback_count/total_turns*100:.1f}%)")
    print(f"Latencia Minima           : {min_latency:.1f} ms")
    print(f"Latencia Promedio         : {avg_latency:.1f} ms")
    print(f"Latencia Mediana (P50)    : {p50:.1f} ms")
    print(f"Latencia Percentil 90 (P90): {p90:.1f} ms")
    print(f"Latencia Maxima           : {max_latency:.1f} ms")

    if failures:
        print("\n" + "!" * 80)
        print("LISTADO DETALLADO DE FALLOS Y DISCREPANCIAS OBLIGATORIO:")
        print("!" * 80)
        for f in failures:
            print(f"• Escenario: {f['scenario']} (Turno {f['turn']})")
            print(f"  Input: \"{f['input']}\"")
            for issue in f["issues"]:
                print(f"  - Causa: {issue}")
    else:
        print("\nCERO FALLOS DETECTADOS. Todos los escenarios cumplieron las invariantes de negocio.")

    return results, failures


if __name__ == "__main__":
    asyncio.run(run_real_conversation_suite())
