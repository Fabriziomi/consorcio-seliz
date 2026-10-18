# Modelo de Datos y Diagrama Entidad-Relación (PostgreSQL)

Este documento describe la estructura relacional de la base de datos PostgreSQL del sistema de administración de consorcios **Dra. Ivana Seliz Administraciones**, gestionada mediante **SQLAlchemy 2.0 Async** en `apps/api/src/infrastructure/models.py`.

---

## 1. Diagrama Entidad-Relación (DER)

```mermaid
erDiagram
    CONSORCIOS ||--o{ CONSORCIOS_ATRIBUTOS_DINAMICOS : "posee"
    CONSORCIOS ||--o{ CONTACTOS : "agrupa vecinos"
    CONSORCIOS ||--o{ CONVERSACIONES : "mantiene hilos"
    CONSORCIOS ||--o{ TICKETS_CONSULTAS : "recibe tickets"
    CONSORCIOS ||--o{ EXPEDIENTES_INCIDENCIAS : "gestiona expedientes"
    CONSORCIOS ||--o{ FAQS_APROBADAS : "parametriza"

    CONTACTOS ||--o{ CONVERSACIONES : "chatea"
    CONTACTOS ||--o{ TICKETS_CONSULTAS : "inicia reclamo"

    CONVERSACIONES ||--o{ MENSAJES : "almacena mensajes"
    USUARIOS ||--o{ CONVERSACIONES : "asigna operador"
    USUARIOS ||--o{ MENSAJES : "redacta respuestas"

    EXPEDIENTES_INCIDENCIAS ||--o{ TICKETS_CONSULTAS : "consolida incidentes"

    CONSORCIOS {
        string id PK "UUIDv4"
        string nombre "Nombre oficial del consorcio"
        string direccion "Calle y número"
        string cuit "Identificación tributaria"
        string cbu_bancario "CBU oficial expensas"
        string alias_bancario "Alias bancario"
        string email_cobranzas "Email para envío de comprobantes"
        string telefono_porteria "Teléfono del encargado"
        string emergencia_ascensores "Teléfono guardia ascensorista"
        string emergencia_plomeria "Teléfono guardia plomero/gasista"
        text pautas_mudanza "Reglamento de mudanzas y SUM"
        boolean activo "Estado operativo del consorcio"
        datetime creado_el "Fecha de alta"
    }

    CONSORCIOS_ATRIBUTOS_DINAMICOS {
        string id PK "UUIDv4"
        string consorcio_id FK "Consorcio propietario"
        string clave "Identificador del atributo"
        string etiqueta_visible "Nombre visible en frontend"
        text valor "Contenido o configuración"
        boolean es_publico_vecinos "Visibilidad para el bot"
    }

    CONTACTOS {
        string id PK "UUIDv4"
        string telefono_wa UK "WhatsApp ID (+54 9...)"
        string nombre_completo "Nombre del vecino o razón social"
        string consorcio_id FK "Consorcio al que pertenece"
        string unidad_funcional "Piso y Depto / Cochera"
        enum rol "PROPIETARIO, INQUILINO, INMOBILIARIA, PROVEEDOR, OTRO"
        string foto_url "Avatar de WhatsApp"
        boolean bot_desactivado "Exclusión del bot"
        datetime creado_el "Fecha de registro"
        datetime ultimo_contacto_el "Fecha de última interacción"
    }

    CONVERSACIONES {
        string id PK "UUIDv4"
        string contacto_id FK "Contacto titular"
        string consorcio_id FK "Consorcio asociado"
        enum estado "OPEN, SNOOZED, RESOLVED"
        boolean bot_activo "Interruptor local del bot"
        string fsm_estado "Estado FSM: IDLE, ONBOARDING_DATOS, etc"
        json fsm_contexto "Contexto serializado FSM"
        boolean needs_human_review "Marcador de derivación a Ivana"
        datetime ultimo_takeover_at "Timestamp de takeover manual"
        string agente_id FK "Operador asignado"
        json etiquetas "Etiquetas organizativas"
        datetime ultimo_mensaje_el "Timestamp de último mensaje"
        datetime creado_el "Fecha de inicio"
    }

    MENSAJES {
        string id PK "UUIDv4"
        string conversacion_id FK "Conversación asociada"
        enum tipo "INCOMING, OUTGOING"
        text contenido "Texto del mensaje"
        boolean privado "Nota interna de administración"
        enum enviado_por "VECINO, BOT, AGENTE, SISTEMA"
        string agente_id FK "Operador remitente"
        string media_url "URL de imagen o archivo adjunto"
        string media_tipo "MIME type"
        boolean leido "Estado de lectura"
        string whatsapp_message_id "ID de mensaje en WhatsApp"
        datetime creado_el "Timestamp de envío"
    }

    TICKETS_CONSULTAS {
        string id PK "UUIDv4"
        string contacto_id FK "Vecino remitente"
        string consorcio_id FK "Consorcio afectado"
        string expediente_id FK "Expediente vinculado"
        string intencion "Clave de intención clasificada"
        string sub_intencion "Detalle específico del problema"
        enum prioridad "CRITICA, ALTA, NORMAL, BAJA"
        enum estado "NUEVO, EN_REVISION, DERIVADO, ESPERANDO_RESPUESTA, RESUELTO"
        text descripcion "Descripción del reclamo"
        json adjuntos_urls "Lista de URLs de archivos adjuntos"
        boolean creado_fuera_de_horario "True si ingresó fuera de oficina"
        datetime creado_el "Fecha de creación"
    }

    EXPEDIENTES_INCIDENCIAS {
        string id PK "UUIDv4"
        string codigo UK "EXP-YYYY-XXXXX"
        string consorcio_id FK "Consorcio"
        string titulo "Título del problema común"
        enum categoria "PLOMERIA, ELECTRICIDAD, GAS, ASCENSORES, COCHERA, OTRO"
        enum prioridad "CRITICA, ALTA, NORMAL, BAJA"
        enum estado "ABIERTO, EN_PROCESO, ESPERANDO_PRESUPUESTO, RESUELTO, CERRADO"
        text descripcion_consolidada "Resumen acumulativo de la falla"
        string proveedor_asignado "Empresa o profesional a cargo"
        datetime creado_el "Fecha de apertura"
        datetime actualizado_el "Última novedad"
        datetime resuelto_el "Fecha de resolución técnica"
    }

    FAQS_APROBADAS {
        string id PK "UUIDv4"
        string consorcio_id FK "Consorcio (nulo si aplica a todos)"
        text pregunta "Pregunta o consulta frecuente"
        text respuesta_oficial "Respuesta institucional aprobada"
        boolean activo "Estado activo"
    }

    USUARIOS {
        string id PK "UUIDv4"
        string email UK "Correo de acceso"
        string password_hash "Hash seguro de contraseña"
        string nombre_completo "Nombre del operador o administrador"
        enum rol "SUPERADMIN, ADMINISTRADOR, AGENTE, LECTURA"
        boolean activo "Estado activo"
        datetime creado_el "Fecha de registro"
        datetime ultimo_login "Último inicio de sesión"
    }

    ETIQUETAS {
        string id PK "UUIDv4"
        string titulo UK "Nombre de la etiqueta"
        string color "Código hexadecimal"
        string descripcion "Descripción o propósito"
        datetime creado_el "Fecha de creación"
    }
```

---

## 2. Índices de Rendimiento y Claves Únicas

Para asegurar latencias sub-segundo en PostgreSQL con cientos de conversaciones activas:

1. **`contactos.telefono_wa`:** Índice único (`UNIQUE INDEX`), acceso en $O(1)$ en la ingesta del webhook.
2. **`conversaciones.contacto_id` y `conversaciones.consorcio_id`:** Índices foráneos con cascada controlada.
3. **`conversaciones.ultimo_mensaje_el`:** Índice descendente para ordenar de inmediato la bandeja de entrada del inbox sin scan de tabla completa.
4. **`conversaciones.needs_human_review`:** Índice booleano para filtrar en milisegundos las conversaciones que requieren atención de Ivana a las 10:00 hs.
5. **`mensajes.conversacion_id` y `mensajes.creado_el`:** Índice compuesto para carga secuencial instantánea del historial en `MessageThread`.
