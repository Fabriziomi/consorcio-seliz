# Guía de Diseño y Arquitectura Frontend — Consorcio Seliz

Este documento define la arquitectura técnica, las directrices visuales y las reglas de diseño para el frontend personalizado del sistema de atención y gestión de la **Dra. Ivana Seliz**.

---

## 1. Visión y Objetivos del Frontend

- **Propósito:** Panel de control y gestión operativa unificada donde la administradora (Ivana Seliz) y su equipo gestionan los mensajes de WhatsApp, tickets, estados de consorcios y respuestas del chatbot.
- **Enfoque Headless / Intermediario:** 
  - En lugar de usar la interfaz estándar de Chatwoot o NocoDB directamente, se construye una **UI a medida ajustada a la identidad visual corporativa**.
  - **Chatwoot API como motor conversacional:** Se utiliza como intermediario backend (inbox multicanal, mensajería en tiempo real, asignación de agentes, estados abierto/resuelto y notas internas).
  - **NocoDB / Postgres como motor de tablas operativas:** Se integran vistas de tablas, filtros de edificios, unidades funcionales y datos de expensas.

---

## 2. Sistema de Diseño e Identidad Visual (*Design System*)

### 2.1. Tipografía
- **Familia principal:** **Montserrat** (`font-sans`).
- **Jerarquía y Pesos:**
  - `Light (300)` / `Regular (400)`: Textos de lectura, transcripciones, notas secundarias.
  - `Medium (500)`: Inputs, botones secundarios, navegación, metadatos y etiquetas.
  - `Semi-Bold (600)`: Títulos de sección, nombres de consorcios, identificadores de ticket.
  - `Bold (700)`: Encabezados principales de pantalla y números de métricas críticas.
- **Interlineado y Tracking:** Espaciado limpio (`tracking-tight` en títulos grandes, `tracking-normal` en textos).

### 2.2. Paleta de Colores y Tokens de Diseño (Alineados con Contino CRM)
El diseño sigue de forma estricta las especificaciones de diseño de Contino Propiedades CRM, garantizando una estética limpia, luminosa, corporativa y de alta gama:

| Token | Valor Hexadecimal | Propósito |
| :--- | :--- | :--- |
| `brand-ink` | `#1B1B1D` | Color principal de marca, texto primario y botones de acción principal |
| `brand-ink-elevated` | `#303034` | Estado hover de botones primarios y elementos elevados |
| `surface` | `#FFFFFF` | Fondo de tarjetas, sidebar, modales y contenedores de contenido |
| `surface-soft` | `#F8F9FA` | Fondo general de la aplicación |
| `surface-muted` | `#F1F3F5` | Fondos secundarios, hovers de lista, tags neutros e inputs |
| `border` | `#E5E7EB` | Borde base sutil de tarjetas, tablas y separadores |
| `border-strong` | `#62656B` | Borde de énfasis en hovers de formulario |
| `text-primary` | `#1B1B1D` | Títulos principales, remitentes y datos destacados |
| `text-secondary` | `#62656B` | Subtítulos, metadatos, descripciones secundarias |
| `text-muted` | `#62656B` | Placeholders y textos de menor jerarquía |

> **Estados Semánticos (Fondo Suave + Borde + Texto):**
> - **Success:** `#2F6F5E` (texto) / `#EAF4F0` (fondo)
> - **Warning:** `#8A5A00` (texto) / `#FBF3E4` (fondo)
> - **Info:** `#3A6576` (texto) / `#EAF2F5` (fondo)
> - **Danger:** `#A33D47` (texto) / `#FBECEE` (fondo)

### 2.3. Componentes Fundacionales de UI (`src/components/ui/`)
- **`Button.jsx`:** Variantes `primary` (gradiente carbón `#303034` -> `#1B1B1D`), `secondary` (borde blanco), `ghost`, `danger`, con altura mínima táctil de 44px (`min-h-11`) y efecto activo `translateY(1px)`.
- **`Badge.jsx`:** Píldoras con variantes semánticas `neutral`, `success`, `warning`, `danger`, `info`.
- **`Card.jsx`:** Contenedores estructurados con `CardHeader` y `CardContent`, borde `#E5E7EB` y sombra fría `shadow-card` (`0 12px 32px -20px rgba(38, 48, 60, 0.22)`).
- **Iconografía:** `lucide-react` minimalista y sin emojis en la interfaz.

---

## 3. Arquitectura Técnica de `apps/frontend`

```
apps/frontend/
├── src/
│   ├── components/
│   │   ├── chat/                # ChatInbox.jsx, MessageThread.jsx, AiDraftBox.jsx
│   │   └── tables/              # TicketsTable.jsx (grilla tipo NocoDB con filtros)
│   ├── lib/
│   │   ├── chatwoot-client.js   # Integración con Chatwoot API (conversaciones y mensajes)
│   │   └── api-client.js        # Conexión con `apps/api`
│   ├── App.jsx                  # Dashboard unificado (Inbox, Hilos, Tickets, Consorcios)
│   ├── index.css                # Directivas de Tailwind (@tailwind base, components, utilities)
│   └── main.jsx                 # Entry point de React 18 con Vite
├── index.html                   # HTML base con carga de fuente Montserrat de Google Fonts
├── vite.config.js               # Configuración de Vite con @vitejs/plugin-react
├── postcss.config.js            # PostCSS para procesamiento de Tailwind y Autoprefixer
├── tailwind.config.js           # Paleta monocromática, Montserrat y Lucide Icons
└── package.json
```

---

## 4. Integraciones Clave

1. **Chatwoot API (Intermediario Conversacional):**
   - El frontend consume los endpoints de Chatwoot (`/api/v1/accounts/{id}/conversations`) para listar conversaciones activas, leer mensajes, enviar respuestas manuales y asignar etiquetas.
   - Sincronización en tiempo real mediante WebSocket (ActionCable de Chatwoot).

2. **NocoDB / API Central (`apps/api`):**
   - Panel de consorcios con edición de CBU, teléfonos de guardia y pautas de mudanza.
   - Tabla de tickets con filtrado por consorcio y estado SLA.
