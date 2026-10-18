# Sistema de Atencion por WhatsApp — Consorcios Dra. Ivana Seliz

Sistema integral y determinista de atencion por WhatsApp para la administracion de consorcios de la Dra. Ivana Seliz (CABA, Argentina), combinando clasificacion tipada de intenciones mediante inteligencia artificial con una Maquina de Estados Finitos pura (`ConversationFSM`), guardrails anti-ban y un panel administrativo propio en React.

---

## 1. Principios Fundamentales

- Determinismo sobre Magia: La logica conversacional y las transiciones de estado residen en codigo Python estructurado (`ConversationFSM`), no en inferencia probabilistica descontrolada.
- Cero Alucinaciones: El sistema jamas inventa telefonos, cuentas bancarias, horarios ni politicas edilicias. Todas las respuestas se generan mediante plantillas aprobadas con variables verificadas desde base de datos o variables de entorno.
- Resiliencia Operativa: Conectores a APIs externas (OpenRouter Jev 1.14, Gemini 2.5 Flash, Groq Whisper API, Evolution API v2) con timeouts estrictos (5s para clasificacion, 3s para audio) y conmutacion automatica.
- Proteccion Anti-Ban: Emision de estados de presencia (`composing`) y retardos humanos naturales (1.5s a 3.0s) antes del despacho de mensajes.
- Sin Dependencias de Terceros Innecesarias: El sistema es 100% autosuficiente con su propia API FastAPI y su panel web React, eliminando la necesidad de NocoDB o servidores externos de Chatwoot.

---

## 2. Dominio del Negocio y Reglas Operativas

- Canal Oficial: WhatsApp oficial via Evolution API v2 (+54 9 11 6248-3302).
- Horario de Oficina (Silencio Estricto del Bot):
  - Lunes a Viernes de 10:00 a 18:00 hs.
  - Sabados de 10:00 a 13:00 hs.
  - Durante este periodo atiende personalmente la Dra. Ivana Seliz. El bot permanece en silencio.
- Horario de Operacion del Bot:
  - Fuera del horario de oficina, domingos y feriados nacionales argentinos.
- Quiet Hours (00:00 a 07:30 hs):
  - Silencio nocturno estricto para no perturbar a los vecinos. Los reclamos no criticos se guardan con `needs_human_review = True` para revision a las 10:00 hs.
- Emergencias Criticas 24/7:
  - Fuga de gas, personas atrapadas en ascensores, incendios o inundaciones graves. Se entregan inmediatamente los telefonos de Bomberos (100), SAME (107) y las guardias tecnicas especificas del consorcio.
- Cobranzas y Expensas:
  - Entrega de CBU, Alias y CUIT del consorcio identificado. Los comprobantes se remiten al correo oficial de cobranzas.

---

## 3. Arquitectura del Sistema (`/apps`)

```
[Vecino en WhatsApp]
       |
       v
[Evolution API v2] (Pasarela WhatsApp)
       |
       v  (Webhook POST /api/v1/webhook/evolution)
[apps/api] (FastAPI Backend Gateway)
       |-- PostgreSQL 15 / SQLite (SQLAlchemy Async: Consorcios, Contactos, Tickets, Expedientes)
       |-- Redis 7 (Debounce de mensajes, sesiones y Takeover humano 12h)
       |-- Groq Whisper API (Transcripcion de audios < 90s)
       |
       +--> [apps/chatbot] (Motor FSM & Clasificacion Tipada)
       |        |-- Cortocircuito de Perfil (Early Binding)
       |        |-- Clasificador Jev 1.14 (OpenRouter) con Fallback a Gemini 2.5 Flash
       |        |-- ConversationFSM (Estados: IDLE, ONBOARDING_DATOS, SOLICITANDO_EDIFICIO, ESPERANDO_SOLO_UNIDAD)
       |        |-- Catalogo de Plantillas Tipadas Round-Robin (len(historial) % 3)
       |
       +--> [apps/frontend] (Panel Administrativo Propio)
                |-- Bandeja de Conversaciones en tiempo real
                |-- Gestion de Expedientes Edilicios y Tickets consolidados
                |-- Administrador de Consorcios y Atributos Dinamicos
                |-- Base de Conocimiento y FAQs aprobadas
                |-- Directorio de Vecinos (Contactos)
                |-- Simulador interactivo de chat y debug
```

---

## 4. Estructura del Repositorio

- `apps/api`: Servidor FastAPI con endpoints REST para el frontend, webhooks de WhatsApp, gestión de autenticación JWT, expedientes consolidados y control de takeover humano.
- `apps/chatbot`: Motor de estados finitos (`ConversationFSM`), evaluador de horarios, clasificador tipado Jev 1.14 / Gemini Flash, extractor semántico de unidades y motor RAG.
- `apps/frontend`: Panel web administrativo desarrollado en React 19, Tailwind CSS, Lucide Icons y Vite, con diseño monocromático, memoización de componentes y posicionamiento instantáneo de scroll en chats.
- `config/`: Esquemas JSON Schema para structured outputs.
- `docs/`: Documentación técnica sincronizada (FSM, DER PostgreSQL, catálogo de plantillas sin emojis, arquitectura y flujos Mermaid).
- `scripts/`: Herramientas de benchmark (`benchmark_jev.py`), simulador interactivo (`test_fsm_cli.py`) y testing automatizado.

---

## 5. Puesta en Marcha y Desarrollo Local

### Requisitos Previos
- Python 3.12+ (compatible con Python 3.14)
- Node.js 18+ y npm
- Docker y Docker Compose (opcional para stack completo)
- Redis (local o en Docker)

### Configuracion de Entorno
Copiar el archivo de variables de entorno y configurar credenciales:
```bash
cp .env.example .env
```

### Comandos de Desarrollo
El script `scripts/start_dev.sh` centraliza la ejecucion:

```bash
# Ejecutar suite completa de tests automatizados (84 tests)
./scripts/start_dev.sh test

# Iniciar la API Backend (FastAPI en http://localhost:8000 - Docs: /docs)
./scripts/start_dev.sh api

# Iniciar el Frontend (Vite + React en http://localhost:3000)
./scripts/start_dev.sh frontend

# Simular casos conversacionales del Chatbot en consola
./scripts/start_dev.sh chatbot
```

### Ejecucion con Docker Stack
```bash
docker compose up -d --build
```
Servicios levantados:
- Frontend Dashboard: `http://localhost:3000`
- API REST & Swagger: `http://localhost:8000/docs`
- Evolution API: `http://localhost:8080`
- PostgreSQL: `localhost:5433` (interno 5432)
- Redis: `localhost:6379`

---

## 6. Verificacion y Bateria de Pruebas

El sistema cuenta con una cobertura integral de 84 pruebas unitarias y de integracion:
```bash
.venv/bin/pytest apps/api/tests apps/chatbot/tests
```
- Validacion de FSM y maquinas de estado multi-turno.
- Verificacion de cero fallbacks hardcodeados en plantillas y generacion de respuestas.
- Evaluador de horarios de oficina, feriados argentinos y quiet hours nocturnas.
- Deteccion y clasificacion de emergencias edilicias criticas.
- Rutas REST de la API: autenticacion, expedientes, conversaciones, tickets y contactos.
- Compilacion de produccion del frontend validada con Vite.
