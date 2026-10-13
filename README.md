# Chatbot con Árbol de Decisión e IA — Consorcios Dra. Ivana Seliz

Sistema integral de atención inteligente por WhatsApp para la administración de consorcios de la **Dra. Ivana Seliz**, combinando reconocimiento de intención mediante Inteligencia Artificial (LLM) con un árbol de decisión determinista, seguro y libre de alucinaciones.

---

## 📌 1. Resumen del Relevamiento

A partir del relevamiento del proyecto en Obsidian (`/home/fabrizio/Documents/Obsidian Vault/Trabajo/Proyectos/Ivana Seliz/Chatbot - Consorcio/`):
- **Problema central:** Vecinos (propietarios e inquilinos) escriben a cualquier hora con quejas, dudas, pagos y urgencias de distintos focos: *Torre Corrientes, Torre Lavalle, Cochera, Galería, Callao 2334*, etc.
- **Horario de atención:** Lunes a Viernes de 10:00 a 14:00 hs y de 14:00 a 17:00 hs. Fuera de ese horario, el bot debe contener al usuario, filtrar emergencias reales y registrar las solicitudes para el siguiente día hábil.
- **Infraestructura ya disponible en Proxmox:**
  - **Evolution API (LXC `192.168.1.93`):** Pasarela WhatsApp Web multi-device lista para enviar/recibir mensajes, etiquetas y archivos multimedia.
  - **NocoDB (LXC `192.168.1.94`):** Base de datos relacional y panel tipo CRM para que Ivana y su equipo gestionen los tickets, estados y contactos sin programar.

---

## 🏛️ 2. Arquitectura de la Solución (Híbrida: IA + Árbol)

```
[Vecino en WhatsApp]
       │
       ▼
[Evolution API (192.168.1.93)]  ◄── Webhook bidireccional
       │
       ▼
[Orquestador / Decision Engine (n8n o Node.js)]
  ├── 1. Validador de Horario (10-14 y 14-17 L-V)
  ├── 2. Buscador de Contacto en NocoDB (192.168.1.94)
  ├── 3. Clasificador de Intención con LLM (Gemini 2.0 Flash / GPT-4o-mini)
  │      └── Devuelve JSON estricto: intent, urgency, entities
  └── 4. Árbol de Decisión Determinista (Ramas: Emergencia, Expensas, Mantenimiento, etc.)
       │
       ▼
[Respuestas Aprobadas + Tickets en NocoDB]
```

---

## 📑 3. Documentación del Proyecto

El relevamiento y diseño completo se encuentra desglosado en:

1. [docs/arquitectura_tecnica.md](file:///home/fabrizio/Work/chatbot/consorcio-seliz/docs/arquitectura_tecnica.md): Comparativa de stacks (n8n vs NestJS vs LangGraph), topología de red, integración con Proxmox y análisis de costos reales (menos de $0.20 USD/mes de IA).
2. [docs/arbol_de_decision_y_flujos.md](file:///home/fabrizio/Work/chatbot/consorcio-seliz/docs/arbol_de_decision_y_flujos.md): Diagrama Mermaid del árbol, especificación de las 7 ramas operativas, matriz de estados (FSM) y reglas de negocio.
3. [docs/clasificador_intenciones_ia.md](file:///home/fabrizio/Work/chatbot/consorcio-seliz/docs/clasificador_intenciones_ia.md): Prompt del sistema para el LLM, catálogo de intenciones, política estricta anti-alucinaciones y ejemplos reales de vecinos.
4. [docs/modelo_de_datos_der.md](file:///home/fabrizio/Work/chatbot/consorcio-seliz/docs/modelo_de_datos_der.md): Diagrama Entidad-Relación (DER) para NocoDB/Postgres (Consorcios, Contactos, Tickets, Respuestas Plantillas, Auditoría).
5. [docs/mensajes_y_plantillas.md](file:///home/fabrizio/Work/chatbot/consorcio-seliz/docs/mensajes_y_plantillas.md): Copys textuales de bienvenida, fuera de horario, números de emergencia, datos bancarios por edificio y solicitud de fotos de reclamos.
6. [config/intents.schema.json](file:///home/fabrizio/Work/chatbot/consorcio-seliz/config/intents.schema.json): Esquema JSON Schema para forzar Structured Outputs en el modelo.

---

## 🚀 4. Hoja de Ruta de Implementación (Roadmap)

### Fase 1: Creación de Tablas en NocoDB y Plantillas (Día 1)
- [ ] Crear el proyecto en NocoDB (`192.168.1.94`) con las tablas `consorcios`, `contactos`, `tickets_consultas` y `respuestas_plantillas`.
- [ ] Cargar los datos de los primeros consorcios (*Corrientes y Lavalle*, *Callao 2334*) con sus CBUs, alias, emails de cobranzas y teléfonos de portería.

### Fase 2: Configuración de Evolution API y Webhook (Día 2)
- [ ] Vincular el número de WhatsApp de atención en Evolution API (`192.168.1.93`).
- [ ] Configurar el webhook hacia el orquestador (n8n o backend).

### Fase 3: Conexión del Clasificador LLM y Árbol de Decisión (Días 3 - 4)
- [ ] Configurar la llamada a la API de Gemini 1.5/2.0 Flash o GPT-4o-mini con el System Prompt y JSON Schema.
- [ ] Implementar el árbol de decisión con las 7 ramas operativas (validación de horario, emergencias, CBU, carga de comprobantes, tickets con fotos).

### Fase 4: Pruebas Piloto y Puesta en Producción (Día 5)
- [ ] Simular casos reales con vecinos de prueba (avería de ascensor, fuera de horario, comprobante de pago).
- [ ] Validar la interfaz de NocoDB junto a Ivana para que empiece a gestionar los tickets diarios.
# consorcio-seliz
