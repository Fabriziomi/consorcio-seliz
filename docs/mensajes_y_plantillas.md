# Catálogo de Mensajes y Plantillas Aprobadas

Este archivo contiene los textos exactos y parametrizados que el chatbot utilizará en cada punto del árbol de decisión.

---

## 1. Mensajes de Apertura y Horario

### Plantilla: `BIENVENIDA_HORARIO` (Dentro de 10 a 14hs y 14 a 17hs)
> *"Hola, buenos días. Te comunicaste con la administración de la Dra. Ivana Seliz.*
> *Te cuento que mi horario de atención es de 10 a 14hs y de 14 a 17hs, de Lunes a Viernes.*
> *¿En qué podemos ayudarte hoy?"*

### Plantilla: `FUERA_HORARIO` (Fuera de días y horas hábiles)
> *"Hola, gracias por comunicarte con la administración de la Dra. Ivana Seliz.*
> *En este momento nos encontramos fuera del horario de atención (Lunes a Viernes de 10 a 14hs y de 14 a 17hs).*
> *Cualquier mensaje fuera del horario de atención será respondido a la brevedad en la próxima jornada hábil.*
> 
> *⚠️ Si tu consulta corresponde a un incidente grave (incendio, inundación, ascensor trabado con personas), por favor leé las instrucciones de emergencia a continuación."*

---

## 2. Mensajes de Emergencia (24/7)

### Plantilla: `EMERGENCIA_GENERAL`
> *"🚨 **CANALES DE CONTACTO DE EMERGENCIA** 🚨*
> 
> *NOTA: Válido exclusivamente para situaciones de incendio, inundaciones graves, personas atrapadas en ascensores o incidentes con riesgo inminente.*
> 
> *• **Guardia de Emergencia Consorcio:** +54 9 11 [NÚMERO_DE_GUARDIA]*
> *• **Bomberos:** 100*
> *• **SAME (Urgencias Médicas):** 107*
> *• **Policía:** 911*
> *• **Defensa Civil CABA:** 103*
> 
> *Si tu edificio cuenta con portería o encargado presente, por favor dale aviso de inmediato.*
> *Tu alerta ha sido registrada con máxima prioridad para el equipo de administración."*

---

## 3. Identificación y Protección de Privacidad

### Plantilla: `SOLICITAR_CONSORCIO` (Para usuarios no registrados)
*(Cumple la regla de NO revelar la lista de clientes o consorcios externos)*
> *"Para poder derivar correctamente tu consulta, por favor indicanos:*
> 1. *¿A qué edificio o dirección pertenecés?*
> 2. *¿Cuál es tu unidad (Piso y Depto / Cochera)?*
> 3. *¿Sos propietario o inquilino?*
> 
> *Con estos datos podremos brindarte la información exacta de tu consorcio."*

---

## 4. Expensas y Cobranzas

### Plantilla: `EXPENSAS_DATOS_PAGO_CORRIENTES_LAVALLE`
> *"📋 **Datos de Pago — Consorcio Corrientes y Lavalle** (Torre Corrientes, Torre Lavalle, Cochera y Galería):*
> 
> *• **Banco / Cuenta:** [NOMBRE_BANCO]*
> *• **CBU:** [CBU_CORRIENTES_LAVALLE]*
> *• **Alias:** [ALIAS_CORRIENTES_LAVALLE]*
> *• **Titular:** Consorcio Propietarios Corrientes y Lavalle*
> *• **CUIT:** [CUIT_CORRIENTES_LAVALLE]*
> *• **Email de cobranzas:** [EMAIL_COBRANZAS]*
> 
> *Recordá remitir el comprobante de transferencia indicando claramente tu Torre, Piso y Departamento."*

### Plantilla: `EXPENSAS_DATOS_PAGO_CALLAO_2334`
> *"📋 **Datos de Pago — Consorcio Callao 2334**:*
> 
> *• **Banco / Cuenta:** [NOMBRE_BANCO]*
> *• **CBU:** [CBU_CALLAO_2334]*
> *• **Alias:** [ALIAS_CALLAO_2334]*
> *• **Titular:** Consorcio Propietarios Callao 2334*
> *• **CUIT:** [CUIT_CALLAO_2334]*
> *• **Email de cobranzas:** [EMAIL_COBRANZAS]*
> 
> *Recordá remitir el comprobante de transferencia indicando tu Piso y Departamento."*

### Plantilla: `CONFIRMACION_COMPROBANTE_PAGO`
> *"✅ Muchas gracias. Hemos recibido tu comprobante de transferencia.*
> *El archivo fue derivado al área de cobranzas para su correspondiente imputación en la liquidación de expensas."*

---

## 5. Reclamos y Averías Técnicas

### Plantilla: `SOLICITAR_DETALLE_RECLAMO`
> *"Tomamos nota de tu reporte edilicio.*
> *Para que el equipo de mantenimiento pueda evaluar el caso con precisión:*
> 1. *Por favor describinos brevemente la falla.*
> 2. *Si es posible, envianos una foto o video corto de la situación.*
> 3. *Indicá si la avería afecta solo a tu unidad o a espacios comunes / otros pisos."*

### Plantilla: `CONFIRMACION_TICKET_RECLAMO`
> *"🛠️ Tu reclamo ha sido registrado con el Ticket Nº **#{TICKET_ID}**.*
> *El área técnica de administración evaluará la prioridad y coordinará la visita del proveedor habilitado en el horario habitual de servicio.*
> *¡Muchas gracias por colaborar con el mantenimiento del edificio!"*

---

## 6. Teléfonos de Portería e Información Edilicia

### Plantilla: `CONTACTO_PORTERIA`
> *"🏢 **Datos de Portería y Encargado — {NOMBRE_CONSORCIO}**:*
> 
> *• **Encargado:** [NOMBRE_ENCARGADO]*
> *• **Teléfono de portería:** {TELEFONO_PORTERIA}*
> *• **Horario habitual de portería:** [HORARIO_PORTERIA]*
> *• **Retiro de residuos:** Lunes a Domingos de 19:00 a 20:00 hs (en bolsas cerradas).*
> 
> *Cualquier duda administrativa adicional podés gestionarla por este mismo canal con la Dra. Ivana Seliz."*
