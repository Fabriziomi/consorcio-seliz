# Arquitectura Técnica — Chatbot Consorcio Seliz

Este documento detalla la infraestructura, comparación de stacks tecnológicos, análisis de costos reales y la arquitectura de integración para el chatbot de atención de la **Dra. Ivana Seliz (Administración de Consorcios)**.

---

## 1. Relevamiento del Entorno y Recursos Existentes

A partir del análisis del vault de Obsidian (`/home/fabrizio/Documents/Obsidian Vault`), se identifican los siguientes activos de infraestructura ya disponibles:

- **Proxmox VE (Servidor Local):**
  - Contenedor LXC Evolution API: `192.168.1.93` (Pasarela WhatsApp Web multi-device).
  - Contenedor LXC NocoDB: `192.168.1.94` (Base de datos relacional y panel visual tipo Airtable/Excel).
- **VPS Linux (Producción Docker):**
  - Orquestación con Docker Compose, proxy inverso Nginx/Caddy con certificados SSL automáticos.
- **Canal de Comunicación:**
  - WhatsApp de la Dra. Ivana Seliz (`+54 9 11 6248-3302` o línea designada para consorcios).

---

## 2. Opciones de Stack para el Motor del Chatbot

El requerimiento exige: **reconocimiento de intención con IA + ejecución de un árbol de decisión determinista** (para evitar alucinaciones, asegurar cumplimiento de horarios y respetar mensajes aprobados).

A continuación se analizan 3 caminos tecnológicos viables:

### Opción A: Orquestación Visual con n8n Self-Hosted + NocoDB + Evolution API *(Recomendado para fase MVP y puesta en marcha rápida)*

- **Cómo funciona:**
  1. Evolution API envía un webhook a n8n ante cada mensaje entrante.
  2. n8n ejecuta un nodo de lógica de control:
     - Verifica si el mensaje entra dentro del horario de atención (10 a 14hs y 14 a 17hs de Lunes a Viernes).
     - Consulta NocoDB para ver si el número telefónico ya tiene consorcio y rol asignado (inquilino/propietario).
     - Si es necesario clasificar texto libre, invoca a un modelo LLM (Gemini Flash o GPT-4o-mini) con formato JSON estructurado para obtener: `{ intencion, urgencia, consorcio_mencionado, datos_extra }`.
  3. Un nodo "Switch" (árbol de decisión determinista) ejecuta la rama correspondiente:
     - Si es emergencia: envía teléfonos de guardia y alerta inmediata.
     - Si falta el consorcio: solicita consorcio sin revelar otros.
     - Si es reclamo de mantenimiento: solicita unidad y foto/video, y crea el ticket en NocoDB.
     - Si es cobranzas/expensas: devuelve los datos bancarios o registra el comprobante adjunto.
  4. Responde a través de Evolution API.
- **Ventajas:**
  - Desarrollo en días, no semanas.
  - Ivana o el equipo técnico pueden ajustar mensajes y condiciones sin re-compilar código.
  - NocoDB funciona como el CRM/Backoffice donde Ivana ve los tickets entrantes clasificados por etiqueta, consorcio y prioridad.
- **Desventajas:**
  - Si el árbol crece con decenas de sub-ramas complejas, los flujos visuales pueden volverse densos (se resuelve modulando en sub-workflows).

---

### Opción B: Backend Dedicado en TypeScript / Node.js (Fastify / NestJS) + Prisma/PostgreSQL

- **Cómo funciona:**
  - API REST/Webhook server con arquitectura por capas:
    - `WhatsAppWebhookController`
    - `IntentClassifierService` (llamada a SDK de Google GenAI o OpenAI con schema Zod)
    - `DecisionTreeEngine` (implementado mediante Máquina de Estados Finitos con `XState` o clases de estado)
    - `NocoDbOrPostgresRepository`
- **Ventajas:**
  - Máximo control de código, tipado estricto en TypeScript, testing unitario e integración continua.
  - Lógica de estados y timeouts (ej. "esperar respuesta del usuario hasta 15 minutos") muy precisa.
- **Desventajas:**
  - Mayor tiempo inicial de desarrollo.
  - Para cambiar una plantilla de mensaje o un paso del flujo se requiere tocar código o exponer un panel custom.

---

### Opción C: Flujo Agéntico con Python + LangGraph

- **Cómo funciona:**
  - Grafo de estados (`StateGraph`) donde el nodo inicial es un clasificador/router que deriva condicionalmente hacia nodos deterministas (`EmergencyNode`, `MaintenanceNode`, `PaymentNode`, `ClarificationNode`).
- **Ventajas:**
  - Muy potente si en el futuro se desea que el bot lea reglamentos de copropiedad en PDF mediante RAG (búsqueda semántica de reglamentos).
- **Desventajas:**
  - Sobreingeniería para una primera etapa si el 90% de los casos se resuelven con plantillas aprobadas y reglas de negocio fijas.

---

## 3. Matriz de Decisión y Recomendación

| Criterio | Opción A (n8n + NocoDB + Evolution) | Opción B (Backend TS / NestJS) | Opción C (Python / LangGraph) |
| :--- | :--- | :--- | :--- |
| **Tiempo de implementación** | **2 a 4 días** | 2 a 3 semanas | 2 a 3 semanas |
| **Curva de mantenimiento** | **Baja (Visual + NocoDB)** | Media (Código TS) | Media/Alta |
| **Control anti-alucinaciones** | **100% (Árbol estricto)** | 100% (FSM estricta) | 95% (Requiere guardrails) |
| **Aprovechamiento de Proxmox actual** | **100% (LXC ya listos)** | Requiere nuevo deploy | Requiere nuevo deploy |
| **Autonomía para Ivana (ver tickets)** | **Inmediata con NocoDB** | Requiere UI extra | Requiere UI extra |

**Recomendación estratégica:**
Iniciar con la **Opción A (n8n + Evolution API + NocoDB)** conectando un modelo de IA ultrarrápido y económico (**Gemini 1.5/2.0 Flash** o **GPT-4o-mini**) exclusivamente para la detección de intenciones y extracción de entidades. Si el volumen o la lógica sobrepasa la herramienta, migrar el motor a la **Opción B**.

---

## 4. Análisis de Costos Reales

### A. Canal de WhatsApp
1. **Con Evolution API (Self-Hosted en Proxmox):**
   - Costo mensual: **$0 USD**.
   - No paga por mensaje ni por conversación iniciada.
   - Utiliza la sesión web del número telefónico.
2. **Con Meta Cloud API Oficial (Alternativa):**
   - Primeras 1.000 conversaciones de servicio/mes iniciadas por usuarios: **Gratis**.
   - Mensajes adicionales de servicio en Argentina: ~$0.03 a $0.05 USD por conversación de 24hs.

### B. Consumo de Inteligencia Artificial (Detección de Intenciones)
El bot **no genera respuestas largas en streaming**, sino únicamente un payload JSON de clasificación de 150 a 250 tokens por interacción.

- **Modelo: Google Gemini 1.5 Flash / 2.0 Flash**
  - Entrada: ~$0.075 USD por millón de tokens.
  - Salida: ~$0.30 USD por millón de tokens.
  - Con un promedio de 500 consultas mensuales (1.500 mensajes clasificados):
  - **Costo mensual estimado: Menos de $0.05 USD (Literalmente centavos de dólar)**.
- **Modelo alternativo: OpenAI GPT-4o-mini**
  - Entrada: $0.15 / 1M tokens | Salida: $0.60 / 1M tokens.
  - **Costo mensual estimado: ~$0.10 a $0.20 USD**.
- **Modelo Local (Ollama en Proxmox - Llama 3.2 3B):**
  - **$0 USD** de consumo de API (requiere hardware de cómputo en Proxmox).

### C. Infraestructura de Servidor
- En el Proxmox local existente: **$0 USD** adicionales.
- Si se replica en VPS en la nube para disponibilidad 24/7 (ej. Hetzner Cloud CX22 o similar): **~$4 a $6 USD/mes**.

> **Resumen de Costos Operativos Totales:**
> **Entre $0 USD y $6 USD al mes** para atender cientos de consultas mensuales.
