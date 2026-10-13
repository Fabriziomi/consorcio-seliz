# Clasificador de Intenciones con IA (System Prompt y Structured Outputs)

Este documento especifica cómo se utiliza la Inteligencia Artificial (LLM) de forma segura y libre de alucinaciones dentro del chatbot.

---

## 1. Rol de la IA en la Arquitectura

Para garantizar que el chatbot **no alucine** información legal, contable ni promesas de servicio falsas a los propietarios o inquilinos:

1. **La IA NO redacta respuestas directas al usuario final de forma autónoma en la fase inicial**.
2. **Su único rol es actuar como "Router Semántico" (Clasificador)**:
   - Recibe el texto del vecino.
   - Comprende el lenguaje coloquial, faltas de ortografía, audios transcriptos o quejas.
   - Devuelve un objeto JSON estructurado con la intención, nivel de urgencia y entidades extraídas.
3. El árbol de decisión toma ese JSON y ejecuta la plantilla pre-aprobada o el flujo correspondiente.

---

## 2. Catálogo de Intenciones y Urgencias

### Intenciones Principales (`intent`):
- `EMERGENCIA`: Situaciones de riesgo edilicio, siniestros, caños maestros rotos, incendio, inundación, ascensor trabado con personas adentro.
- `EXPENSAS_DATOS_PAGO`: Solicitud de CBU, alias, formas de pago, fecha de vencimiento.
- `EXPENSAS_COMPROBANTE`: El usuario indica que envía o quiere enviar un comprobante de pago/transferencia.
- `EXPENSAS_RECLAMO_SALDO`: Dudas sobre montos adeudados, intereses o no imputación de pagos.
- `RECLAMO_MANTENIMIENTO`: Averías en partes comunes o filtraciones (plomería, electricidad, gas, cerrajería, ascensor averiado vacío, cochera/portón).
- `MUDANZA_Y_REGLAMENTO`: Consultas de horarios de mudanza, solicitud de seguro, uso de SUM, mascotas, ruidos molestos.
- `CONTACTO_PORTERIA`: Pedido de teléfono o datos del encargado/portero del edificio.
- `CONSULTA_ADMINISTRACION`: Consultas legales, asambleas de copropietarios, venta/alquiler de unidad, atención presencial.
- `SALUDO_CORDIAL`: Saludos sin consulta específica ("Buen día", "Hola").
- `DESCONOCIDO_AMBIGUO`: Mensajes confusos o que requieren intervención manual.

### Niveles de Urgencia (`urgency`):
- `EMERGENCY`: Acción inmediata requerida (24/7).
- `HIGH`: Reclamo prioritario (ej. corte de agua de toda la columna).
- `NORMAL`: Consultas habituales de administración.
- `LOW`: Saludos o confirmaciones de lectura.

---

## 3. System Prompt del Clasificador

```markdown
Eres un clasificador de intenciones experto para el sistema de atención por WhatsApp de la administración de consorcios de la Dra. Ivana Seliz (CABA, Argentina).

Tu única función es analizar el mensaje entrante del usuario y clasificarlo con precisión estricta en formato JSON.

### CONTEXTO DEL NEGOCIO:
- Consorcios administrados frecuentes:
  - Consorcio Corrientes y Lavalle (Torre Corrientes, Torre Lavalle, Cocheras, Galería)
  - Consorcio Callao 2334
- Horario de atención: Lunes a Viernes de 10 a 14hs y de 14 a 17hs.
- Las emergencias incluyen: incendios, inundaciones masivas, personas atrapadas en ascensores, escape de gas, riesgo inminente de vida o derrumbe.

### REGLAS DE RESPUESTA:
- Responde ÚNICAMENTE con un JSON válido que cumpla con el esquema provisto.
- No agregues texto introductorio, ni markdown innecesario, ni explicaciones.
- Si el usuario menciona datos como piso, departamento o nombre del edificio, extráelos en "extracted_entities".
- Si no estás seguro de la intención (confianza menor a 0.65), clasifica como "DESCONOCIDO_AMBIGUO".
```

---

## 4. Esquema JSON de Salida (Structured Output)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "intent": {
      "type": "string",
      "enum": [
        "EMERGENCIA",
        "EXPENSAS_DATOS_PAGO",
        "EXPENSAS_COMPROBANTE",
        "EXPENSAS_RECLAMO_SALDO",
        "RECLAMO_MANTENIMIENTO",
        "MUDANZA_Y_REGLAMENTO",
        "CONTACTO_PORTERIA",
        "CONSULTA_ADMINISTRACION",
        "SALUDO_CORDIAL",
        "DESCONOCIDO_AMBIGUO"
      ]
    },
    "sub_intent": {
      "type": "string",
      "description": "Detalle específico, ej: plomeria, ascensor, cerrajeria, cbu, etc."
    },
    "urgency": {
      "type": "string",
      "enum": ["EMERGENCY", "HIGH", "NORMAL", "LOW"]
    },
    "extracted_entities": {
      "type": "object",
      "properties": {
        "consorcio_mencionado": { "type": ["string", "null"] },
        "unidad_funcional": { "type": ["string", "null"] },
        "descripcion_corta": { "type": ["string", "null"] }
      },
      "required": ["consorcio_mencionado", "unidad_funcional", "descripcion_corta"]
    },
    "confidence": {
      "type": "number",
      "description": "Nivel de certeza de 0.0 a 1.0"
    }
  },
  "required": ["intent", "sub_intent", "urgency", "extracted_entities", "confidence"]
}
```

---

## 5. Ejemplos de Clasificación en Casos Reales

### Ejemplo 1: Emergencia Real
- **Mensaje:** *"Hola Ivana urgente, se trabó el ascensor de la torre Lavalle en el piso 3 y hay una señora adentro pidiendo auxilio!"*
- **JSON de Salida:**
```json
{
  "intent": "EMERGENCIA",
  "sub_intent": "ascensor_personas_atrapadas",
  "urgency": "EMERGENCY",
  "extracted_entities": {
    "consorcio_mencionado": "Corrientes y Lavalle - Torre Lavalle",
    "unidad_funcional": "Piso 3",
    "descripcion_corta": "Ascensor trabado con personas adentro"
  },
  "confidence": 0.99
}
```

### Ejemplo 2: Cobranzas / Pago de Expensas
- **Mensaje:** *"Buenas tardes Dra, le paso el comprobante de la transferencia de las expensas de octubre del depto 8 B de Callao. Muchas gracias."*
- **JSON de Salida:**
```json
{
  "intent": "EXPENSAS_COMPROBANTE",
  "sub_intent": "envio_transferencia",
  "urgency": "NORMAL",
  "extracted_entities": {
    "consorcio_mencionado": "Callao 2334",
    "unidad_funcional": "8 B",
    "descripcion_corta": "Comprobante de pago expensas octubre"
  },
  "confidence": 0.98
}
```

### Ejemplo 3: Reclamo Edilicio Habitual
- **Mensaje:** *"Buen día, desde ayer que no tenemos agua caliente en el piso 4 de Corrientes, parece que la caldera está apagada."*
- **JSON de Salida:**
```json
{
  "intent": "RECLAMO_MANTENIMIENTO",
  "sub_intent": "caldera_agua_caliente",
  "urgency": "HIGH",
  "extracted_entities": {
    "consorcio_mencionado": "Corrientes y Lavalle - Torre Corrientes",
    "unidad_funcional": "Piso 4",
    "descripcion_corta": "Falta de agua caliente general / caldera"
  },
  "confidence": 0.95
}
```
