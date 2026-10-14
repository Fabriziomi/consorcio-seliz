# Guía de Inicio Rápido del MVP — Consorcio Seliz

Esta guía permite poner en marcha y probar localmente todos los componentes del sistema (Chatbot IA, API Gateway y Frontend Web) en menos de 2 minutos.

---

## 🏗️ 1. Estructura de las Aplicaciones

| Componente | Ruta | Tecnología | Puerto / URL | Función |
| :--- | :--- | :--- | :--- | :--- |
| **API Core** | `apps/api` | FastAPI + SQLAlchemy Async + SQLite/Postgres | `http://localhost:8000` | Webhooks de WhatsApp, gestión de consorcios, tickets y sincronización con Chatwoot. |
| **Chatbot Engine** | `apps/chatbot` | LangGraph + FastEmbed (MiniLM) + Tev1 Router | Inferencia local CPU | Enrutador semántico de 2 niveles, guardrails de horarios y emergencias 24/7. |
| **Frontend UI** | `apps/frontend` | Vite + React (JavaScript) + Tailwind CSS + Lucide Icons | `http://localhost:3000` | Panel de control de Ivana con bandeja de entrada Chatwoot Headless y aprobación de borradores IA. |

---

## ⚡ 2. Comandos de Inicio Rápido (Script Unificado)

El proyecto incluye el script ejecutable [`scripts/start_dev.sh`](file:///run/media/fabrizio/Almacenamiento/Works/Proyects/consorcio-seliz/scripts/start_dev.sh):

```bash
# 1. Ejecutar la suite completa de 15 tests automatizados (API + Chatbot)
./scripts/start_dev.sh test

# 2. Iniciar el API Backend (FastAPI + Swagger docs)
./scripts/start_dev.sh api
# Documentación interactiva en: http://localhost:8000/docs

# 3. Iniciar el Panel Frontend (Vite en http://localhost:3000)
./scripts/start_dev.sh frontend
# Panel administrativo en: http://localhost:3000

# 4. Correr la simulación interactiva del Chatbot
./scripts/start_dev.sh chatbot
```

---

## 🧪 3. Semilla de Datos y Simulación de Casos

Para poblar la base de datos local con los consorcios iniciales (*Torre Corrientes y Lavalle*, *Callao 2334*) y contactos de prueba:

```bash
source .venv/bin/activate
PYTHONPATH=apps/api/src python apps/api/src/seed.py
```

### Casos Reales Verificados en el Motor:
1. **Búsqueda Vectorial RAG en FAQs:**
   - *Pregunta:* `"¿En qué horario se puede sacar la basura?"`
   - *Resultado:* Match directo con `faq-basura-horarios` (Score: 0.98, Latencia: 5 ms). Responde con la plantilla oficial.
2. **Emergencia Grave 24/7:**
   - *Pregunta:* `"¡Urgente, se rompió el caño maestro y se inunda el palier!"`
   - *Resultado:* Bypass instantáneo. Despacha canales de emergencia oficiales (SAME, Bomberos, guardia).
3. **Cierre Cordial / Prevención de Bucles:**
   - *Mensaje:* `"Listo muchas gracias 👍"`
   - *Resultado:* **Silencio inteligente** (0 palabras, no genera respuesta ni bucle infinito).
4. **Consulta Abierta / Derivación:**
   - *Pregunta:* `"¿Cuándo convocan a la próxima asamblea ordinaria de consorcio?"`
   - *Resultado:* Tev1 Opción D. Despacha acuse neutro oficial y genera ticket para que Ivana lo responda en horario hábil.

---

## 🔬 4. Modo Debug HTTP & Simulador de Conversación Local

Para probar conversaciones completas de forma local sin requerir Proxmox, Evolution API ni WhatsApp real, dispones de tres modalidades de depuración inmediata:

### A. Desde la Terminal con el Script CLI:
```bash
# 1. Consulta estándar de pagos
./scripts/chat_debug.sh "Hola, a qué cuenta transfiero las expensas?"

# 2. Emergencia grave (dispara alerta y ticket crítico)
./scripts/chat_debug.sh "Urgente, hay una fuga de gas en el palier y peligro de explosión!"

# 3. Simular horario de oficina humana (bot guarda silencio total)
./scripts/chat_debug.sh -s HUMAN_OFFICE_HOURS "Hola, están atendiendo?"

# 4. Despedida / Cierre cordial (prevención de bucles)
./scripts/chat_debug.sh "Muchas gracias por todo, buen finde!"
```

### B. Desde el Frontend Web (`http://localhost:3000`):
- Ingresá a la pestaña **"Simulador Debug"**.
- Escribí cualquier mensaje o seleccioná un ejemplo rápido (*CBU Expensas, Urgencia Gas, Ascensor Traspasado*).
- Podés forzar el horario (`BOT_ACTIVE_OFF_HOURS`, `HUMAN_OFFICE_HOURS`, `QUIET_HOURS`).
- Al presionar **"Enviar HTTP"**, verás en vivo el globo de respuesta del bot junto con la telemetría técnica completa: estado horario, match RAG, decisión Tev1, latencia desglosada y ticket generado.

### C. Vía cURL directo o Swagger:
- **Swagger UI:** `http://localhost:8000/docs#/Debug%20Simulator/debug_chat_api_v1_debug_chat_post`
- **cURL:**
```bash
curl -X POST http://localhost:8000/api/v1/debug/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hola, ¿cuál es el CBU para abonar?",
    "phone": "+5491144558899",
    "override_schedule": "BOT_ACTIVE_OFF_HOURS"
  }'
```

---

## 🎨 5. Directrices de Identidad Visual del Frontend
- **Tipografía:** Montserrat (`font-sans`).
- **Paleta de Colores:** Monocromática estricta (Slate/Charcoal `#0B0F17` / `#0F172A`).
- **Iconografía:** `lucide-react` minimalista y aislado. Cero emojis en interfaz.
- **Detalle completo en:** [docs/frontend_guidelines.md](file:///run/media/fabrizio/Almacenamiento/Works/Proyects/consorcio-seliz/docs/frontend_guidelines.md).
