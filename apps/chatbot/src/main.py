from engine.graph import decision_graph
from engine.state import ChatState


def test_scenario(phone: str, message: str):
    initial_state = ChatState(phone=phone, user_message=message)
    result = decision_graph.invoke(initial_state)

    print("\n" + "="*70)
    print(f"📩 MENSAJE ENTRANTE: \"{message}\"")
    print("="*70)
    print(f"• Horario Evaluado  : {result.get('schedule_status')}")
    print(f"• Emergencia 24/7   : {result.get('is_emergency')}")
    print(f"• Cierre Cordial    : {result.get('is_cordial_close')}")
    print(f"• Match RAG Nivel 1 : {result.get('rag_matched')} (FAQ: {result.get('rag_faq_id')}, Score: {result.get('rag_score')})")
    print(f"• Decisión Tev1 (N2): {result.get('tev1_decision')}")
    print(f"• Latencias (ms)    : {result.get('latency_metrics')}")
    print(f"• Debe Responder    : {result.get('should_respond')}")
    
    if result.get("should_respond"):
        print(f"\n💬 RESPUESTA DESPACHADA:\n{result.get('response_text')}")
    else:
        print(f"\n🤫 SILENCIO APLICADO: {result.get('silent_reason')}")


if __name__ == "__main__":
    print("\n🚀 EJECUTANDO PRUEBAS LOCALES DEL STACK HÍBRIDO (RAG + TEV1 + LANGGRAPH)...")
    
    # 1. Hit Directo RAG en FAQs (Mudanzas)
    test_scenario("+5491100001111", "¿Cuáles son los horarios permitidos para mudanzas el fin de semana?")

    # 2. Hit Directo RAG en FAQs (Basura)
    test_scenario("+5491100001111", "¿En qué horario se puede sacar la basura?")

    # 3. Tev1 Nivel 2: Cobranzas y Datos de Pago
    test_scenario("+5491100001111", "Hola, me podrían pasar el CBU y alias para transferir las expensas?")

    # 4. Emergencia Grave 24/7 (Bypass inmediato)
    test_scenario("+5491100001111", "Urgente, hay dos personas atrapadas en el ascensor de Torre Corrientes!")

    # 5. Cierre Cordial (Silencio inteligente / Anti-bucle)
    test_scenario("+5491100001111", "Bárbaro muchas gracias, buen finde! 👍")

    # 6. Consulta No Catalogada (Asentar ticket neutro)
    test_scenario("+5491100001111", "Quisiera consultar cuándo convocan a la próxima asamblea ordinaria de consorcio")

    print("\n✅ Pruebas locales completadas con éxito. Motor Chatbot activo en modo espera.")
    import time
    try:
        while True:
            time.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        print("\n🛑 Deteniendo Motor Chatbot...")
