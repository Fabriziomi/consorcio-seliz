import asyncio
import time
import os
import sys
from typing import List, Dict, Any

# Asegurar path para importar desde apps/chatbot/src
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CHATBOT_SRC = os.path.join(PROJECT_ROOT, "apps", "chatbot", "src")
if CHATBOT_SRC not in sys.path:
    sys.path.insert(0, CHATBOT_SRC)

from dotenv import load_dotenv

# Cargar variables de entorno desde .env raíz
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

from services.openrouter_client import OpenRouterClient
from engine.state_models import Intencion
from core.config import settings

# Catálogo real de consorcios
CONSORCIOS_CATALOG = [
    {
        "id": "cons-corrientes-lavalle",
        "nombre": "Consorcio Corrientes y Lavalle",
        "direccion": "Av. Corrientes 1240 / Lavalle 1241, CABA",
    },
    {
        "id": "cons-callao-2334",
        "nombre": "Consorcio Callao 2334",
        "direccion": "Av. Callao 2334, Recoleta, CABA",
    },
]

# 30 Casos de prueba representativos del dialecto rioplatense
BENCHMARK_CASES: List[Dict[str, Any]] = [
    # --- Bloque 1: Expensas y Pagos ---
    {
        "id": 1,
        "text": "Hola, ¿me podrían pasar el CBU y alias para transferir las expensas?",
        "expected_intent": "CONSULTA_EXPENSAS",
        "has_consorcio": True,
        "has_unidad": True,
    },
    {
        "id": 2,
        "text": "¿Cuál es la cuenta bancaria de Callao 2334 para abonar este mes?",
        "expected_intent": "CONSULTA_EXPENSAS",
        "has_consorcio": False,
        "has_unidad": False,
        "expected_consorcio": "cons-callao-2334",
    },
    {
        "id": 3,
        "text": "Buen día, necesito los datos de transferencia para pagar las expensas del 4° B",
        "expected_intent": "CONSULTA_EXPENSAS",
        "has_consorcio": True,
        "has_unidad": False,
        "expected_unit": True,
    },
    {
        "id": 4,
        "text": "Hola, ya transferí las expensas de la unidad 2A, les adjunto el comprobante",
        "expected_intent": "AVISO_PAGO_REALIZADO",
        "has_consorcio": True,
        "has_unidad": True,
    },
    {
        "id": 5,
        "text": "Acabo de hacer la transferencia bancaria por las expensas de este mes.",
        "expected_intent": "AVISO_PAGO_REALIZADO",
        "has_consorcio": True,
        "has_unidad": True,
    },
    # --- Bloque 2: Emergencias Críticas 24/7 ---
    {
        "id": 6,
        "text": "Urgente, hay olor a gas fuertísimo en el palier del piso 3, parece una fuga seria",
        "expected_intent": "EMERGENCIA_GRAVE",
        "has_consorcio": True,
        "has_unidad": True,
    },
    {
        "id": 7,
        "text": "Se trabó el ascensor y hay una vecina atrapada adentro gritando, manden a alguien ya",
        "expected_intent": "EMERGENCIA_GRAVE",
        "has_consorcio": True,
        "has_unidad": True,
    },
    {
        "id": 8,
        "text": "Se rompió el caño maestro del edificio y se está inundando la entrada de Callao 2334",
        "expected_intent": "EMERGENCIA_GRAVE",
        "has_consorcio": False,
        "has_unidad": False,
        "expected_consorcio": "cons-callao-2334",
    },
    {
        "id": 9,
        "text": "Hay humo saliendo del tablero de electricidad del sótano, parece que hace chispas",
        "expected_intent": "EMERGENCIA_GRAVE",
        "has_consorcio": True,
        "has_unidad": True,
    },
    # --- Bloque 3: Reclamos Técnicos Ordinarios ---
    {
        "id": 10,
        "text": "Hola, el ascensor principal hace un chirrido insoportable cuando frena en el piso 5",
        "expected_intent": "RECLAMO_TECNICO",
        "has_consorcio": True,
        "has_unidad": True,
    },
    {
        "id": 11,
        "text": "Tengo una filtración de humedad en el techo del living que viene del piso de arriba",
        "expected_intent": "RECLAMO_TECNICO",
        "has_consorcio": True,
        "has_unidad": True,
    },
    {
        "id": 12,
        "text": "La luz de emergencia de la escalera de servicio del 2do piso no prende",
        "expected_intent": "RECLAMO_TECNICO",
        "has_consorcio": True,
        "has_unidad": True,
    },
    {
        "id": 13,
        "text": "Buenas tardes, la cerradura del portón de la cochera está falseada y no traba",
        "expected_intent": "RECLAMO_TECNICO",
        "has_consorcio": True,
        "has_unidad": True,
    },
    {
        "id": 14,
        "text": "El portero eléctrico de mi departamento (5° C) no suena cuando tocan timbre",
        "expected_intent": "RECLAMO_TECNICO",
        "has_consorcio": True,
        "has_unidad": False,
        "expected_unit": True,
    },
    # --- Bloque 4: Mudanzas y Normativa ---
    {
        "id": 15,
        "text": "¿Qué días y en qué horario se puede usar el ascensor montacargas para una mudanza?",
        "expected_intent": "MUDANZA",
        "has_consorcio": True,
        "has_unidad": True,
    },
    {
        "id": 16,
        "text": "Hola, quiero saber qué documentación me van a pedir para ingresar un flete el sábado",
        "expected_intent": "MUDANZA",
        "has_consorcio": True,
        "has_unidad": True,
    },
    {
        "id": 17,
        "text": "Quería consultar las normas del edificio para hacer una mudanza este fin de semana",
        "expected_intent": "MUDANZA",
        "has_consorcio": True,
        "has_unidad": True,
    },
    # --- Bloque 5: Cierre Cordial y Agradecimientos ---
    {
        "id": 18,
        "text": "Muchas gracias por la información, que tengas buen día",
        "expected_intent": "CIERRE_CORDIAL",
        "has_consorcio": True,
        "has_unidad": True,
    },
    {
        "id": 19,
        "text": "Excelente, muy claro. Saludos cordiales.",
        "expected_intent": "CIERRE_CORDIAL",
        "has_consorcio": True,
        "has_unidad": True,
    },
    {
        "id": 20,
        "text": "Ok, perfecto, gracias por avisar.",
        "expected_intent": "CIERRE_CORDIAL",
        "has_consorcio": True,
        "has_unidad": True,
    },
    # --- Bloque 6: Onboarding y Ubicación Edilicia ---
    {
        "id": 21,
        "text": "Soy del consorcio Callao 2334, departamento 8 B",
        "expected_intent": "OTRO",  # Puede ser OTRO o clasificado si trae intención implícita
        "has_consorcio": False,
        "has_unidad": False,
        "expected_consorcio": "cons-callao-2334",
        "expected_unit": True,
    },
    {
        "id": 22,
        "text": "Vivo en Av Corrientes 1240 en el 10° A",
        "expected_intent": "OTRO",
        "has_consorcio": False,
        "has_unidad": False,
        "expected_consorcio": "cons-corrientes-lavalle",
        "expected_unit": True,
    },
    {
        "id": 23,
        "text": "Hola, les escribo desde Lavalle 1241 por el depto 1 B",
        "expected_intent": "OTRO",
        "has_consorcio": False,
        "has_unidad": False,
        "expected_consorcio": "cons-corrientes-lavalle",
        "expected_unit": True,
    },
    {
        "id": 24,
        "text": "Escribo desde Rivadavia 4500, piso 4 depto A",
        "expected_intent": "OTRO",
        "has_consorcio": False,
        "has_unidad": False,
        "expected_consorcio": "OTRO_NO_ADMINISTRADO",
        "expected_unit": True,
    },
    {
        "id": 25,
        "text": "Mi departamento es el 6° C",
        "expected_intent": "OTRO",
        "has_consorcio": True,
        "has_unidad": False,
        "expected_unit": True,
    },
    # --- Bloque 7: Casos Borde y Ambigüedad ---
    {
        "id": 26,
        "text": "Hola",
        "expected_intent": "INTENCION_AMBIGUA",
        "has_consorcio": True,
        "has_unidad": True,
    },
    {
        "id": 27,
        "text": "¿?",
        "expected_intent": "INTENCION_AMBIGUA",
        "has_consorcio": True,
        "has_unidad": True,
    },
    {
        "id": 28,
        "text": "Necesito saber si ya pasaron a limpiar",
        "expected_intent": "RECLAMO_TECNICO",
        "has_consorcio": True,
        "has_unidad": True,
    },
    {
        "id": 29,
        "text": "Tengan en cuenta que voy a llegar tarde hoy",
        "expected_intent": "OTRO",
        "has_consorcio": True,
        "has_unidad": True,
    },
    {
        "id": 30,
        "text": "Hola, ¿quién es el encargado del edificio de Callao?",
        "expected_intent": "OTRO",
        "has_consorcio": False,
        "has_unidad": True,
        "expected_consorcio": "cons-callao-2334",
    },
]


async def run_benchmark():
    print("=" * 80)
    print("BENCHMARK FASE 0: VALIDACIÓN DE MOTOR JEV 1.14 & FALLBACK GEMINI 2.5 FLASH")
    print("Administración Dra. Ivana Seliz — Dialecto Rioplatense")
    print("=" * 80)

    client = OpenRouterClient()
    print(f"Modelo Principal: {client.base_url} -> {settings.JEV_MODEL}")
    print(f"Modelo Fallback:  {settings.GEMINI_FALLBACK_MODEL}")
    print(f"Umbral Confianza: {client.confidence_threshold}")
    print(f"Total Casos:      {len(BENCHMARK_CASES)}")
    print("-" * 80)

    results = []
    latencies = []
    correct_intents = 0
    correct_consorcios = 0
    consorcio_checks = 0

    for case in BENCHMARK_CASES:
        cid = case["id"]
        text = case["text"]
        exp_intent = case["expected_intent"]
        has_c = case.get("has_consorcio", False)
        has_u = case.get("has_unidad", False)

        try:
            decision = await client.classify_intent(
                text=text,
                has_consorcio=has_c,
                has_unidad=has_u,
                consorcios_catalog=CONSORCIOS_CATALOG,
            )

            latencies.append(decision.latency_ms)

            # Evaluar coincidencia de intención
            is_intent_ok = (decision.intencion == exp_intent) or (
                exp_intent == "INTENCION_AMBIGUA"
                and decision.intencion in ("INTENCION_AMBIGUA", "CIERRE_CORDIAL", "OTRO")
            )
            if is_intent_ok:
                correct_intents += 1

            # Evaluar consorcio si aplica
            is_consorcio_ok = True
            if "expected_consorcio" in case:
                consorcio_checks += 1
                exp_c = case["expected_consorcio"]
                if decision.consorcio_mencionado == exp_c:
                    correct_consorcios += 1
                else:
                    is_consorcio_ok = False

            # Evaluar unidad si aplica
            unit_info = decision.unidad_funcional if decision.contiene_unidad else "-"

            status_mark = "OK" if (is_intent_ok and is_consorcio_ok) else "REVISAR"

            results.append(
                {
                    "id": cid,
                    "text": text[:40] + ("..." if len(text) > 40 else ""),
                    "intent": decision.intencion,
                    "exp_intent": exp_intent,
                    "conf": f"{decision.confidence:.2f}",
                    "consorcio": decision.consorcio_mencionado or "-",
                    "unidad": unit_info or "-",
                    "latency": f"{decision.latency_ms:.0f}ms",
                    "status": status_mark,
                    "fallback": decision.is_fallback,
                }
            )

            print(
                f"[{cid:02d}/30] Lat: {decision.latency_ms:4.0f}ms | Intención: {decision.intencion:<20} | Conf: {decision.confidence:.2f} | Status: {status_mark}"
            )

        except Exception as e:
            print(f"[{cid:02d}/30] ERROR: {e}")
            results.append({"id": cid, "status": "ERROR", "error": str(e)})

    # Calcular Percentiles de Latencia
    latencies.sort()
    n = len(latencies)
    p50 = latencies[int(n * 0.50)] if n else 0
    p90 = latencies[int(n * 0.90)] if n else 0
    p95 = latencies[int(n * 0.95)] if n else 0
    p99 = latencies[int(n * 0.99)] if n else 0
    avg_lat = sum(latencies) / n if n else 0
    min_lat = latencies[0] if n else 0
    max_lat = latencies[-1] if n else 0

    intent_acc = (correct_intents / len(BENCHMARK_CASES)) * 100
    consorcio_acc = (correct_consorcios / consorcio_checks * 100) if consorcio_checks else 100

    print("=" * 80)
    print("RESUMEN EJECUTIVO DEL BENCHMARK")
    print("=" * 80)
    print(f"• Casos Evaluados:            {len(BENCHMARK_CASES)}")
    print(f"• Precisión de Intención:     {correct_intents}/{len(BENCHMARK_CASES)} ({intent_acc:.1f}%)")
    print(f"• Precisión de Consorcio:     {correct_consorcios}/{consorcio_checks} ({consorcio_acc:.1f}%)")
    print(f"• Latencia Mínima:            {min_lat:.1f} ms")
    print(f"• Latencia Promedio (Mean):   {avg_lat:.1f} ms")
    print(f"• Latencia Mediana (P50):     {p50:.1f} ms")
    print(f"• Latencia Percentil 90 (P90):{p90:.1f} ms")
    print(f"• Latencia Percentil 95 (P95):{p95:.1f} ms")
    print(f"• Latencia Máxima:            {max_lat:.1f} ms")
    print("=" * 80)

    # Validar cumplimiento de SLAs de producción
    cumple_sla_latencia = p90 < 2500.0
    cumple_sla_precision = intent_acc >= 85.0

    if cumple_sla_latencia and cumple_sla_precision:
        print("RESULTADO: APROBADO para Fase 1 (SLA de latencia sub-segundo / 2.5s y precisión > 85%)")
    else:
        print("RESULTADO: REQUIERE AJUSTE DE PROMPT O UMBRAL")

    return results


if __name__ == "__main__":
    asyncio.run(run_benchmark())
