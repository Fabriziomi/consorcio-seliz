# Project Brief — Chatbot de Consorcios (Dra. Ivana Seliz)

---

## 1. Ficha del Proyecto & Resumen Ejecutivo

| Parámetro | Detalle |
| :--- | :--- |
| **Cliente / Organización** | Administración de Consorcios — Dra. Ivana Seliz (CABA, Argentina) |
| **Consorcios Iniciales** | *Torre Corrientes, Torre Lavalle, Cocheras y Galería*, *Callao 2334* |
| **Problema a Resolver** | Vecinos envían mensajes, quejas, comprobantes y emergencias por WhatsApp a cualquier hora. El horario de atención humana es limitado y se requiere contención nocturna, derivación rápida de emergencias y cero alucinaciones sin colapsar el celular de la administradora. |
| **Propuesta de Solución** | Chatbot híbrido determinista en **Python (FastAPI + LangGraph)** ejecutado en un contenedor **LXC en Proxmox**, que opera **únicamente fuera del horario laboral**, transcribiendo audios localmente, entregando respuestas aprobadas por RAG y generando borradores asistidos para revisión humana en NocoDB. |

---

## 2. Tono de Comunicación & Voz Institucional (*Brand Persona*)

- **Registro Lingüístico:** **Rioplatense Formal** (voseo profesional argentino).
- **Tono:** Sobrio, empático, resolutivo, formal y con autoridad administrativa.
- **Identidad del Emisor:** Habla en representación de la administración de la **Dra. Ivana Seliz**.
- **Reglas de Redacción:**
  - **Uso de voseo formal:** *"Te comunicaste con la administración..."*, *"Por favor indicanos tu unidad..."*, *"Remití tu comprobante..."*.
  - **Tratamiento respetuoso:** *"Estimado/a vecino/a"*, *"Tomamos conocimiento de tu solicitud"*, *"Será evaluado por el área técnica el próximo día hábil"*.
  - **Prohibición de lunfardo o informalidad excesiva:** Prohibido el uso de *"che"*, modismos coloquiales callejeros o respuestas ambiguas. Siempre estructurado y conciso.

---

## 3. Infraestructura & Asignación de Recursos (LXC Proxmox)

- **Entorno de Ejecución:** Contenedores **LXC en Proxmox** corriendo **Ubuntu Server** (consumo base OS < 30 MB de RAM).
- **Recursos Exclusivos para Modelos de IA:**
  - **RAM:** **8 GB dedicados exclusivamente para los modelos locales** (Whisper + Sentence-Transformers + llama.cpp).
  - **CPU:** **6 núcleos/hilos dedicados a inferencia** (Sin GPU).
- **Topologías de Despliegue en Proxmox:**
  - **Opción A (2 LXCs Separados):**
    - `LXC-Modelos-AI`: 8 GB RAM + 6 Cores dedicados a inferencia local (FastAPI interno / servidor de modelos).
    - `LXC-App-Backend`: 2 GB RAM + 2 Cores para el motor del chatbot (FastAPI, LangGraph, Redis, conectores).
  - **Opción B (1 LXC Unificado con 10 GB RAM):**
    - Un solo contenedor LXC con **10 GB de RAM** y 6 Cores (8 GB para modelos IA + 2 GB para sistema, FastAPI y Redis).
- **Dimensionamiento de Modelos Locales en CPU:**
  - **Speech-to-Text (Audio):** `faster-whisper` modelo `small` cuantizado a `int8` (CTranslate2). Uso: **~500 MB RAM**. Transcribe audios de 30s en ~2 segundos con los 6 hilos dedicados.
  - **Embeddings & RAG (Nivel 1):** `sentence-transformers` (`paraphrase-multilingual-MiniLM-L12-v2`). Uso: **~250 MB RAM**. Búsqueda matemática en PostgreSQL con `pgvector` en ~15ms.
  - **Motor de Decisión Cerrado (Nivel 2):** **`Tev1 0.8B`** (Decision Model de Together AI / Qwen) cuantizado a 4 bits (`GGUF` vía `llama-cpp-python`). Uso: **~600 MB RAM**, latencia: ~50ms. Resuelve el enrutamiento en conjunto cerrado (`A, B, C, D...`) con **cero alucinaciones y debugging trivial**.
  - **LLM de Borradores Asíncronos:** `llama-cpp-python` con modelo `Qwen 2.5 3B` o `LLaMA 3.2 3B` cuantizado a 4 bits (`GGUF`). Uso: **~2.2 GB RAM**. Solo se despierta en segundo plano para redactar sugerencias en NocoDB.
  - **Consumo Total de Modelos:** ~3.5 GB de RAM. Quedan más de **4.5 GB de RAM libres** en el contenedor.
- **Servicios Satélites en Proxmox:**
  - **Evolution API v2 (LXC `192.168.1.93`):** Pasarela WhatsApp Web multi-device.
  - **NocoDB (LXC `192.168.1.94`):** Panel visual para Ivana (edición de consorcios, FAQs, atributos dinámicos y aprobación de respuestas).
  - **PostgreSQL 15 + pgvector & Redis 7:** Base de datos central y buffer de mensajes.

---

## 4. Reglas de Negocio Inquebrantables (*Guardrails*)

1. **Horarios de Atención:**
   - **Horario Laboral Humano:** Lunes a Viernes de 10:00 a 18:00 hs y Sábados de 10:00 a 13:00 hs.  
     *(El bot permanece en **SILENCIO TOTAL**; Ivana atiende desde su celular físico).*
   - **Actividad del Bot:** Lunes a Viernes de 18:01 a 09:59 hs, Sábados desde las 13:01 hs, Domingos y Feriados 24 hs.
2. **Quiet Hours (Silencio Nocturno):**
   - **00:00 a 07:30 hs**. Si entra un mensaje no urgente, el bot no responde en la madrugada; apila los mensajes y despacha la respuesta a las **07:31 hs**.
   - **Bypass de Emergencias 24/7:** Si se detecta un incidente crítico (olor a gas, rotura de caño maestro/inundación, personas atrapadas en ascensor), responde **inmediatamente** con los teléfonos de guardia y alerta a la administración.
3. **Takeover Humano (Anti-Solapamiento):**
   - Antes de enviar un mensaje o procesar un borrador, el bot consulta el historial de WhatsApp. Si Ivana respondió directamente desde su teléfono físico, el bot **se silencia** y el borrador en NocoDB pasa a estado **`OMITIDA`**.
4. **Política Estricta de Cobranzas y Pagos:**
   - **Cero pasarelas de pago:** No se integran botones de pago ni pasarelas automatizadas.
   - **Canal 100% por Email:** Las expensas y comprobantes se tramitan **exclusivamente por correo electrónico** (`email_cobranzas`). El bot solo informa la cuenta bancaria oficial y la casilla de destino.
5. **Privacidad de Consorcios:**
   - Pregunta discreta con coincidencia difusa (*Fuzzy Matching*). El bot **NUNCA** lista edificios de otros clientes a un usuario no identificado.
6. **Cero Alucinaciones y Cero Falsas Promesas (Solo FAQs Aprobadas):**
   - El bot **NUNCA** debe inventar áreas técnicas inexistentes, ni prometer visitas de inspección ni tiempos de respuesta no homologados.
   - **Información Oficial de FAQs:** El bot únicamente responde si la información proviene de las **FAQs aprobadas** (score RAG >= 0.85) o datos duros (CBU, teléfonos de guardia).
   - **Si la consulta NO está en las FAQs:** El bot **no arriesga ni inventa excusas corporativas**. Emite un acuse de recibo neutro oficial:  
     > *"Tu mensaje quedó registrado para la administración de la Dra. Ivana Seliz. Será respondido en el horario habitual de atención (Lunes a Viernes de 10 a 18 hs | Sábados de 10 a 13 hs)."*  
     y deriva la consulta a segundo plano para que la administradora la revise en NocoDB.
7. **Silencio Inteligente ante Confirmaciones y Cierres (Capacidad de NO RESPONDER):**
   - Para erradicar bucles infinitos de cortesía y reducir el riesgo de alucinación a cero, el bot cuenta con la regla estricta de **permanecer en silencio** ante mensajes de cierre, confirmaciones cortas o despedidas posteriores a una consulta ya resuelta.
   - **Ejemplo de conversación:**
     - *Chatbot:* *"Dale perfecto, cualquier cosa escribinos y nos comunicamos en la semana."*
     - *Propietario:* *"Okey dale"* / *"Listo gracias"* / *"👍"* / *"Bárbaro"* / *"Buen finde"*.
     - *Chatbot:* **(NO RESPONDE / SILENCIO)**.
   - **Mecanismo técnico:** Se detecta la intención `CIERRE_CORDIAL` o `AGRADECIMIENTO_CORTO`; el mensaje se guarda en el historial de PostgreSQL para auditoría pero el grafo de LangGraph enruta directamente a `END` sin emitir ningún mensaje por Evolution API.
8. **Observabilidad Total del Pipeline y Trazabilidad en Logs (Configurable por `.env`):**
   - **Norma Obligatoria para Testeo:** Cada nodo del pipeline debe documentar en logs su comportamiento exacto, la decisión tomada, etiquetas estandarizadas y el **tiempo de respuesta (latencia en milisegundos)**.
   - **Etiquetas Claras (Tags):**  
     `[PIPELINE_START]`, `[DEBOUNCE_BUFFER]`, `[SCHEDULE_CHECK]`, `[QUIET_HOURS]`, `[STT_WHISPER]`, `[EMERGENCY_FILTER]`, `[CONSORCIO_MATCHER]`, `[TAKEOVER_CHECK]`, `[RAG_FAQ_SEARCH]`, `[TEV1_ROUTER]`, `[ACTION_APPROVED]`, `[ACTION_SILENT_NO_OP]`, `[ACTION_ASYNC_DRAFT]`, `[PIPELINE_FINISH]`.
   - **Parámetros en `.env`:**
     - `LOG_LEVEL=DEBUG` / `INFO`
     - `ENABLE_DETAILED_PIPELINE_LOGS=true`
     - `LOG_LATENCY_METRICS=true`
     - `LOG_FORMAT=CONSOLE` *(con colores y tags legibles para desarrollo)* o `JSON` *(para producción)*.
9. **Modo de Debug Rápido (Bypass de Buffers y Esperas en `.env`):**
   - **Agilidad para Desarrollo y Testing:** Para no tener que esperar 12 segundos de debounce ni pausas aleatorias de simulación humana durante pruebas locales o tests automatizados (pytest/curl), el sistema cuenta con flags en `.env` para saltear las demoras:
     - `FAST_DEBUG_MODE=true`: Master switch para respuesta inmediata.
     - `BYPASS_DEBOUNCE_BUFFER=true`: Reduce la ventana de buffer de 12s a 0s (procesamiento síncrono instantáneo).
     - `DISABLE_RANDOM_JITTER=true`: Elimina el jitter aleatorio (±3s) de escritura.
     - `OVERRIDE_SCHEDULE_OFF_HOURS=true`: Simula que el bot siempre está en horario activo (permite testear flujos fuera de hora a las 2 de la tarde sin alterar la hora del servidor).

---

## 5. Arquitectura de Software Monorepo: `/apps/`

El proyecto se estructura como un monorepo modular bajo `/apps/`, desacoplando la API gateway, el motor del chatbot y el panel web administrativo propio:

```
apps/
├── api/                       # API Central, Gateway y Webhooks (FastAPI)
│   ├── src/
│   │   ├── api/v1/            # Endpoints: Webhooks (Evolution, Chatwoot, NocoDB), Tickets, Consorcios
│   │   ├── core/              # Configuración, variables y logging
│   │   ├── domain/            # Modelos Pydantic, DTOs y entidades
│   │   └── infrastructure/    # PostgreSQL (SQLAlchemy Async), Redis, Clientes (Chatwoot, Evolution, NocoDB)
│   ├── Dockerfile
│   └── requirements.txt
│
├── chatbot/                   # Motor Inteligente y Árbol de Decisión (Python + LangGraph)
│   ├── src/
│   │   ├── engine/            # Grafo de estados (StateGraph) y nodos de decisión
│   │   ├── classifier/        # RAG FAQs (Nivel 1), Tev1 0.8B Router (Nivel 2)
│   │   ├── guardrails/        # Evaluador de horarios, Quiet Hours, filtro emergencias 24/7, anti-solapamiento
│   │   ├── services/          # Whisper STT (CPU int8), Sentence-Transformers, Async Drafts
│   │   └── worker.py          # Worker consumidor de ráfagas (Redis debounce)
│   ├── Dockerfile
│   └── requirements.txt
│
└── frontend/                  # Dashboard Propio de Administración (Next.js / React + Tailwind)
    ├── src/
    │   ├── app/               # Rutas: Inbox (Chatwoot), Consorcios, Tickets, Configuración
    │   ├── components/        # Componentes UI sobrios, tablas NocoDB-style, chat
    │   ├── lib/               # Clientes Chatwoot API (ActionCable/WS) y API Backend
    │   └── styles/            # Estilos con tipografía Montserrat y paleta monocromática
    ├── tailwind.config.ts     # Configuración con Lucide Icons y sin emojis
    └── package.json
```

### 💬 Chatwoot como Intermediario y UI Propia:
- **Chatwoot API como motor conversacional:** Gestiona los canales de mensajería (WhatsApp a través de Evolution API), presencia de agentes, hilos de conversación y eventos en tiempo real.
- **Frontend Personalizado:** En lugar de utilizar la interfaz genérica de Chatwoot, el frontend en `apps/frontend` consume sus APIs para unificar en una sola pantalla la atención de chats, la aprobación de borradores de IA y las tablas operativas de consorcios/tickets (NocoDB).
- **Directrices de UI:** Tipografía Montserrat con variación de pesos, paleta sobria y monocromática (Slate/Charcoal), sin emojis en interfaz y con iconos minimalistas de `lucide-react`. Más detalles en [docs/frontend_guidelines.md](file:///run/media/fabrizio/Almacenamiento/Works/Proyects/consorcio-seliz/docs/frontend_guidelines.md).

### 🎯 Enrutador Híbrido en Dos Niveles (Simple, Robusto y Fácil de Debuguear):
1. **Nivel 1 — Hit Directo en FAQs (Matemático / ~10ms):**
   - Búsqueda vectorial con `pgvector` sobre `faqs_aprobadas`.
   - Si la similitud coseno es `>= 0.85`, despacha la respuesta oficial textual de inmediato. Cero LLMs y cero cómputo.
2. **Nivel 2 — Árbitro de Decisión con Tev1 0.8B (Conjunto Cerrado / ~50ms):**
   - Si no hay match exacto en FAQs, entra **Tev1 0.8B**.
   - Clasifica el mensaje contra un conjunto cerrado de opciones fijas:
     - `A`: Emergencia Grave 24/7
     - `B`: Cobranzas e Info de Pagos por Email
     - `C`: Cierre Cordial / Silencio (No responder)
     - `D`: Consulta No Catalogada (Asentar Ticket neutro para Ivana)
   - **Por qué hace el debugging trivial:** Tev1 solo devuelve una letra (`A`, `B`, `C` o `D`). En los logs queda registrado exactamente `Decision: B`. No hay JSONs rotos, no hay sintaxis que interpretar ni alucinaciones posibles.

---

## 6. Modelo de Datos y Opción B (Atributos Dinámicos)

### Tablas Centrales en PostgreSQL:
1. `consorcios_datos_operativos`: CBU, CUIT, teléfonos de guardia, portería, horarios de basura.
2. `consorcios_atributos_dinamicos` (**Opción B**):
   - `consorcio_id`, `clave`, `etiqueta_visible`, `valor`, `tipo_dato`, `es_publico_vecinos`.
   - Permite a Ivana agregar datos particulares de cada edificio desde NocoDB con un clic.
   - El flag `es_publico_vecinos` protege datos confidenciales de la administración.
3. `faqs_aprobadas`: Preguntas, respuestas oficiales y columna `embedding vector(384)`.
4. `tickets_consultas`: Historial, adjuntos multimedia, prioridad y estado.
5. `respuestas_pendientes`: Borradores generados por la IA en segundo plano (`PENDIENTE`, `APROBADO`, `MODIFICADO`, `OMITIDA`).
6. `sesiones_activas`: Estado y slots de la conversación.

---

## 7. Plan de Implementación SMART (Roadmap)

### Fase 1: MVP Determinístico y Conectividad (Semana 1)
- [ ] Configuración del contenedor LXC en Proxmox (Ubuntu Server con Python 3.11, Redis y dependencias CTranslate2).
- [ ] Configuración de la base de datos PostgreSQL con extensión `pgvector` y tablas iniciales.
- [ ] Implementación del endpoint receptor de webhooks de Evolution API en FastAPI.
- [ ] Worker de Debounce (12s + jitter aleatorio) en Redis.
- [ ] Transcripción local con `faster-whisper small int8` en CPU.
- [ ] Árbol de decisión determinista en LangGraph: Horarios, Quiet Hours, emergencias 24/7 y datos bancarios por consorcio.
- [ ] Creación de tickets en NocoDB y verificación de mensajes del celular de Ivana.

### Fase 2: RAG Semántico y Human-in-the-Loop (Semana 2)
- [ ] Integración de `sentence-transformers` para búsqueda semántica en `faqs_aprobadas` (umbral >= 0.85).
- [ ] Menú determinista de desambiguación.
- [ ] Worker asíncrono con LLM local (`llama-cpp-python`) para redactar borradores en `respuestas_pendientes`.
- [ ] Sincronización automática de estado `OMITIDA` al contestar Ivana desde su celular.
- [ ] Soporte para la sub-tabla `consorcios_atributos_dinamicos` (Opción B).

### Fase 3: Pruebas Piloto y Puesta en Producción (Semana 3)
- [ ] Carga masiva de datos reales de *Torre Corrientes y Lavalle* y *Callao 2334*.
- [ ] Pruebas en vivo con vecinos seleccionados fuera de horario.
- [ ] Ajustes finos de prompts rioplatenses formales y métricas de atención en NocoDB.
