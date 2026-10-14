import threading
import time
from services.semantic_extractor import semantic_extractor


def test_semantic_extractor_concurrent_thread_safety():
    """
    Simula 5 vecinos enviando mensajes al mismo milisegundo exacto.
    Verifica que:
    1. Ningún hilo genera Segmentation Fault ni excepciones no controladas.
    2. Todos los hilos reciben un resultado válido (sea por LLM o por contingencia instantánea).
    3. El lock se libera adecuadamente sin deadlocks.
    """
    messages = [
        "Hola soy del 4B de Callao, se me rompio un caño",
        "Buenas, me pasan el cbu de expensas?",
        "Aviso que ya pague lo de este mes",
        "Aca en corrientes nos quedamos trabados en el ascensor",
        "Hola que tal buen dia",
    ]
    consorcios = ["Consorcio Callao 2334", "Consorcio Corrientes 1240"]

    results = []
    errors = []

    def worker(msg):
        try:
            res = semantic_extractor.extract(msg, consorcios)
            results.append(res)
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=worker, args=(m,)) for m in messages]

    t0 = time.time()
    for t in threads:
        t.start()

    for t in threads:
        t.join(timeout=30.0)

    total_time = time.time() - t0

    # 1. Cero excepciones
    assert len(errors) == 0, f"Ocurrieron errores en hilos concurrentes: {errors}"
    
    # 2. Todos los mensajes recibieron respuesta estructurada
    assert len(results) == len(messages)
    for r in results:
        assert r is not None
        assert r.categoria is not None
        assert r.intencion is not None
        assert r.metodo in ("QWEN_3B", "FALLBACK_RULES")

    # 3. El lock debe quedar libre tras finalizar todos los hilos
    assert not semantic_extractor._inference_lock.locked()


def test_semantic_extractor_fallback_when_lock_held():
    """
    Verifica que si el lock de inferencia está ocupado por una tarea larga,
    otra solicitud no se cuelga y recurre de inmediato al motor determinista.
    """
    # Adquirir el lock manualmente simulando una inferencia pesada en curso
    acquired = semantic_extractor._inference_lock.acquire(timeout=2.0)
    assert acquired is True

    try:
        t0 = time.time()
        # Esta llamada debe detectar que el lock está retenido y despachar por contingencia
        res = semantic_extractor.extract("Soy del 2A y se corto la luz", ["Consorcio Callao 2334"])
        elapsed = time.time() - t0

        # Debe responder en menos de 3.0s (timeout del lock + fallback)
        assert elapsed < 3.5
        assert res.metodo == "FALLBACK_RULES"
        assert res.unidad_funcional == "2A"
        assert res.categoria == "ELECTRICIDAD"
    finally:
        semantic_extractor._inference_lock.release()
