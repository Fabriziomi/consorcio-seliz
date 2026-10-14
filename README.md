# Chatbot con Árbol de Decisión e IA — Consorcios Dra. Ivana Seliz

Sistema integral de atención inteligente por WhatsApp para la administración de consorcios de la **Dra. Ivana Seliz**, combinando reconocimiento de intención mediante Inteligencia Artificial (LLM) con un árbol de decisión determinista, seguro y libre de alucinaciones.

---

## 📌 1. Resumen del Relevamiento

A partir del relevamiento del proyecto en Obsidian (`Vault/Trabajo/Proyectos/Ivana Seliz/Chatbot - Consorcio/`):
- **Problema central:** Vecinos (propietarios e inquilinos) escriben a cualquier hora con quejas, dudas, pagos y urgencias de distintos focos: *Torre Corrientes, Torre Lavalle, Cochera, Galería, Callao 2334*, etc.
- **Horario de atención:** Lunes a Viernes de 10:00 a 14:00 hs y de 14:00 a 17:00 hs. Fuera de ese horario, el bot debe contener al usuario, filtrar emergencias reales y registrar las solicitudes para el siguiente día hábil.
- **Infraestructura ya disponible en Proxmox:**
  - **Evolution API:** Pasarela WhatsApp Web multi-device lista para enviar/recibir mensajes, etiquetas y archivos multimedia.
  - **NocoDB:** Base de datos relacional y panel tipo CRM para que Ivana y su equipo gestionen los tickets, estados y contactos sin programar.

---

## 🏛️ 2. Arquitectura de la Solución (Monorepo `/apps/`)

```
[Vecino en WhatsApp]
       │
       ▼
[Evolution API]  ◄── Webhook bidireccional
       │
       ▼
[Chatwoot API (Intermediario Omnicanal)]
       │
       ├──► [apps/api (FastAPI Gateway & Hub)]
       │        ├── PostgreSQL 15 (Datos y pgvector)
       │        └── NocoDB (Tablas operativas)
       │
       ├──► [apps/chatbot (LangGraph Engine)]
       │        ├── 1. Validador de Horarios y Quiet Hours
       │        ├── 2. Filtro Rápido de Emergencias 24/7
       │        ├── 3. RAG FAQs (Similitud >= 0.85)
       │        └── 4. Tev1 0.8B Decision Router & Buffer Redis
       │
       └──► [apps/frontend (Panel Custom UI)]
                ├── Chatwoot API (Mensajes, presencia y notas en vivo)
                ├── Tablas y vistas de Consorcios/Tickets
                └── Diseño sobrio (Montserrat, monocromático, Lucide Icons)
```

---

## 📑 3. Documentación del Proyecto

El relevamiento y diseño completo se encuentra desglosado en:

1. [docs/mvp_quickstart.md](file:///run/media/fabrizio/Almacenamiento/Works/Proyects/consorcio-seliz/docs/mvp_quickstart.md): **Guía rápida de ejecución del MVP**, comandos del script y prueba de escenarios.
2. [docs/project_brief.md](file:///run/media/fabrizio/Almacenamiento/Works/Proyects/consorcio-seliz/docs/project_brief.md): Especificación técnica completa, modelos locales CPU, guardrails y arquitectura.
3. [docs/frontend_guidelines.md](file:///run/media/fabrizio/Almacenamiento/Works/Proyects/consorcio-seliz/docs/frontend_guidelines.md): Directrices visuales y técnicas del frontend (Montserrat, monocromía sobria, Lucide Icons y consumo de APIs de Chatwoot/NocoDB).
4. [docs/arbol_de_decision_y_flujos.md](file:///run/media/fabrizio/Almacenamiento/Works/Proyects/consorcio-seliz/docs/arbol_de_decision_y_flujos.md): Diagrama Mermaid del árbol, especificación de las 7 ramas operativas, matriz de estados (FSM) y reglas de negocio.
5. [docs/clasificador_intenciones_ia.md](file:///run/media/fabrizio/Almacenamiento/Works/Proyects/consorcio-seliz/docs/clasificador_intenciones_ia.md): Prompt del sistema para el LLM, catálogo de intenciones, política estricta anti-alucinaciones y ejemplos reales de vecinos.
6. [docs/modelo_de_datos_der.md](file:///run/media/fabrizio/Almacenamiento/Works/Proyects/consorcio-seliz/docs/modelo_de_datos_der.md): Diagrama Entidad-Relación (DER) para NocoDB/Postgres (Consorcios, Contactos, Tickets, Respuestas Plantillas, Auditoría).
7. [docs/mensajes_y_plantillas.md](file:///run/media/fabrizio/Almacenamiento/Works/Proyects/consorcio-seliz/docs/mensajes_y_plantillas.md): Copys textuales de bienvenida, fuera de horario, números de emergencia, datos bancarios por edificio y solicitud de fotos de reclamos.
8. [config/intents.schema.json](file:///run/media/fabrizio/Almacenamiento/Works/Proyects/consorcio-seliz/config/intents.schema.json): Esquema JSON Schema para forzar Structured Outputs en el modelo.

---

## ⚡ 4. Inicio Rápido de Desarrollo (Quickstart)

Podés arrancar y probar cualquier componente del proyecto con el script [`scripts/start_dev.sh`](file:///run/media/fabrizio/Almacenamiento/Works/Proyects/consorcio-seliz/scripts/start_dev.sh):

```bash
# Correr los 15 tests automatizados (API + Chatbot)
./scripts/start_dev.sh test

# Iniciar la API Backend (FastAPI + Swagger docs en :8000)
./scripts/start_dev.sh api

# Iniciar el Frontend (Vite + React en :3000)
./scripts/start_dev.sh frontend

# Simular casos reales del Chatbot en consola
./scripts/start_dev.sh chatbot
```

---

## 🚀 5. Hoja de Ruta de Implementación (Roadmap)

### Fase 1: Creación de Tablas en NocoDB y Plantillas (Día 1)
- [ ] Crear el proyecto en NocoDB con las tablas `consorcios`, `contactos`, `tickets_consultas` y `respuestas_plantillas`.
- [ ] Cargar los datos de los primeros consorcios (*Corrientes y Lavalle*, *Callao 2334*) con sus CBUs, alias, emails de cobranzas y teléfonos de portería.

### Fase 2: Configuración de Evolution API y Webhook (Día 2)
- [ ] Vincular el número de WhatsApp de atención en Evolution API.
- [ ] Configurar el webhook hacia el orquestador (n8n o backend).

### Fase 3: Conexión del Clasificador LLM y Árbol de Decisión (Días 3 - 4)
- [ ] Configurar la llamada a la API de Gemini 1.5/2.0 Flash o GPT-4o-mini con el System Prompt y JSON Schema.
- [ ] Implementar el árbol de decisión con las 7 ramas operativas (validación de horario, emergencias, CBU, carga de comprobantes, tickets con fotos).

### Fase 4: Pruebas Piloto y Puesta en Producción (Día 5)
- [ ] Simular casos reales con vecinos de prueba (avería de ascensor, fuera de horario, comprobante de pago).
- [ ] Validar la interfaz de NocoDB junto a Ivana para que empiece a gestionar los tickets diarios.
# consorcio-seliz
