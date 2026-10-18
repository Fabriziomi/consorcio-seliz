# Catálogo Oficial de Mensajes y Plantillas Institucionales

Este documento formaliza el catálogo oficial de plantillas del sistema de atención conversacional de la **Dra. Ivana Seliz Administraciones**, implementado en `apps/chatbot/src/services/templates.py`.

---

## 1. Reglas de Estilo y Políticas de Redacción

1. **Español Rioplatense Formal:**
   - Voseo profesional argentino (*"¿cómo estás?"*, *"te comunicaste con la administración"*, *"por favor indicanos"*, *"remití tu comprobante"*).
   - Tono sobrio, empático, resolutivo y con autoridad institucional.
2. **Cero Emojis (Regla Estricta):**
   - Prohibido el uso de emojis en todos los mensajes automáticos, placeholders y metadatos.
3. **Selección Round-Robin Determinista:**
   - Cada plantilla cuenta con 3 variantes formales equivalentes.
   - La selección de la variante se realiza mediante `len(historial) % 3`, logrando variedad conversacional natural sin depender de variabilidad estocástica de un LLM.
4. **Cero Alucinaciones:**
   - Las plantillas solo interpolan variables previamente verificadas en la base de datos o validadas en el contexto.

---

## 2. Catálogo de Plantillas por Estado e Intención

### A. Onboarding de Datos (`ONBOARDING_DATOS`)
*Se activa cuando un usuario nuevo o sin datos en su perfil envía una consulta que requiere consorcio y unidad.*
- **Variante 1:** *"Hola{nombre_saludo}, ¿cómo estás? Te comunicaste con la administración de la Dra. Ivana Seliz. Para poder registrar tu consulta y asistirte, ¿podrías indicarnos a qué edificio pertenecés y cuál es tu unidad funcional (piso y departamento)?"*
- **Variante 2:** *"Hola{nombre_saludo}, gracias por contactar a la administración de la Dra. Ivana Seliz. Para poder canalizar tu mensaje con el equipo correspondiente, por favor decinos de qué consorcio y qué departamento nos escribís."*
- **Variante 3:** *"Hola{nombre_saludo}, buenas tardes. Desde la administración de la Dra. Ivana Seliz te pedimos, por favor, que nos indiques tu edificio y número de unidad funcional (piso y letra) para poder gestionar tu mensaje."*

### B. Reintento de Onboarding (`ONBOARDING_REINTENTO_1`)
*Se activa si en el primer intento no fue posible identificar el edificio o la unidad.*
- **Variante 1:** *"Hola{nombre_saludo}, no pudimos identificar el edificio en nuestro padrón. Por favor, escribí la calle y altura exacta del inmueble, junto con tu piso y departamento."*
- **Variante 2:** *"Disculpá{nombre_saludo}, no encontramos el consorcio con los datos provistos. ¿Podrías reiterarnos la dirección exacta con calle, numeración y unidad funcional?"*
- **Variante 3:** *"Hola{nombre_saludo}, necesitamos confirmar la dirección precisa. Indicá por favor la calle y número de puerta del consorcio y tu departamento para poder ubicarte en el sistema."*

### C. Bailout de Onboarding (`ONBOARDING_BAILOUT`)
*Se activa al fallar dos intentos consecutivos para cortar el bucle y derivar a atención humana.*
- **Variante 1:** *"Hola{nombre_saludo}, no logramos validar los datos de tu edificio en el sistema. Dejamos asentado tu mensaje para que la Dra. Ivana Seliz lo revise personalmente a partir de las 10:00 hs en horario de oficina."*
- **Variante 2:** *"Gracias por tu mensaje{nombre_saludo}. Al no poder verificar la dirección del inmueble, el caso queda derivado para su revisión manual por la administración a las 10:00 hs."*
- **Variante 3:** *"Hola{nombre_saludo}, asentamos tu contacto para atención personalizada. El equipo de administración retomará tu consulta a partir de las 10:00 hs en horario habitual de atención."*

### D. Solicitud de Edificio para Expensas (`SOLICITAR_EDIFICIO_EXPENSAS`)
*Se activa cuando se solicita CBU pero no se conoce el edificio del usuario.*
- **Variante 1:** *"Hola{nombre_saludo}, para poder enviarte los datos de cuenta bancaria y CBU correspondientes al pago de expensas, ¿podrías indicarnos la dirección de tu edificio?"*
- **Variante 2:** *"Hola{nombre_saludo}, ¿a qué edificio pertenecés? Decinos la calle y altura para poder enviarte el CBU oficial de tu consorcio."*
- **Variante 3:** *"Buenas tardes{nombre_saludo}, para brindarte la información bancaria exacta necesitamos saber a qué consorcio pertenecés. Por favor indicanos la dirección de tu edificio."*

### E. Solicitud de Edificio para Emergencia (`SOLICITAR_EDIFICIO_EMERGENCIA`)
*Se activa ante un incidente grave sin consorcio asignado.*
- **Variante 1:** *"Hola{nombre_saludo}. Si estás ante una emergencia con riesgo inminente, comunicate de inmediato con Bomberos (100) o SAME (107). Para enviar la guardia técnica del edificio a la brevedad, por favor indicanos con urgencia la dirección exacta y piso."*
- **Variante 2:** *"ATENCIÓN: Si hay peligro inminente (gas, fuego o derrumbe), llamá urgente a Bomberos (100), SAME (107) o Policía (911). Por favor escribinos la calle y número del edificio para despachar la guardia técnica correspondiente."*
- **Variante 3:** *"Hola{nombre_saludo}. Ante situaciones de urgencia crítica llamá de inmediato al 100 (Bomberos) o 107 (SAME). Indicanos la dirección de tu edificio ya mismo para derivar la asistencia técnica del consorcio."*

### F. Datos de Expensas y Cobranzas (`EXPENSAS_DATOS_PAGO`)
*Se activa cuando el consorcio está verificado y se solicitan datos bancarios.*
- **Variante 1:**
  > *"Hola{nombre_saludo}, te compartimos los datos oficiales de la cuenta bancaria del consorcio {consorcio}:*
  > *• CBU: {cbu}*
  > *• Alias: {alias}*
  > *• CUIT: {cuit}*
  > *Una vez realizada la transferencia, recordá remitir el comprobante a {email_cobranzas} indicando tu unidad funcional."*
- **Variante 2:**
  > *"Buenas tardes{nombre_saludo}. Los datos bancarios del consorcio {consorcio} son los siguientes:*
  > *• Cuenta CBU: {cbu}*
  > *• Alias: {alias}*
  > *• CUIT: {cuit}*
  > *Por favor enviá el comprobante de pago por correo electrónico a {email_cobranzas} para su imputación contable."*
- **Variante 3:**
  > *"Hola{nombre_saludo}, los datos para el pago de expensas de {consorcio} son:*
  > *• CBU oficial: {cbu}*
  > *• Alias: {alias}*
  > *• CUIT: {cuit}*
  > *Es indispensable enviar el comprobante de transferencia a {email_cobranzas} detallando piso y departamento."*

### G. Aviso de Pago Realizado (`AVISO_PAGO_CONFIRMACION`)
- **Variante 1:** *"Gracias por avisarnos{nombre_saludo}. Te recordamos que es necesario enviar el comprobante de transferencia por correo electrónico a {email_cobranzas} para que el sector contable lo impute en tu cuenta."*
- **Variante 2:** *"Tomamos conocimiento de tu aviso de pago{nombre_saludo}. Por favor remití el comprobante a {email_cobranzas} indicando tu unidad para registrar la acreditación correspondiente."*
- **Variante 3:** *"Hola{nombre_saludo}, gracias por la información. Para imputar el pago en las expensas, recordá enviar el comprobante digital a {email_cobranzas} con los datos de tu departamento."*

### H. Emergencia Activa con Guardias Técnicas (`EMERGENCIA_ACTIVA`)
- **Variante 1:**
  > *"ATENCIÓN: Si hay peligro inminente, comunicate de inmediato con Bomberos (100), SAME (107) o Policía (911).*
  > *Contactos de urgencia para el consorcio {consorcio}:*
  > *{telefonos_guardia}*
  > *Dejamos asentada tu notificación con prioridad urgente para la administración."*
- **Variante 2:**
  > *"EMERGENCIA: Para situaciones críticas con riesgo de vida comunicate ya al 100 (Bomberos) o 107 (SAME).*
  > *Guardias técnicas habilitadas para {consorcio}:*
  > *{telefonos_guardia}*
  > *El caso queda registrado con alerta prioritaria para intervención inmediata."*
- **Variante 3:**
  > *"Aviso de urgencia para {consorcio}. Ante peligro grave llamá inmediatamente al 100 (Bomberos), 107 (SAME) o 911.*
  > *Líneas de asistencia técnica de guardia:*
  > *{telefonos_guardia}*
  > *Tomamos conocimiento de la situación con máxima prioridad."*

### I. Acuse de Recibo de Reclamos (`RECLAMO_ACUSE_RECIBO`)
- **Variante 1:** *"Hola{nombre_saludo}, registramos tu mensaje sobre el inconveniente reportado en {consorcio}{unidad}. El equipo de administración lo evaluará a partir de las 10:00 hs para coordinar la intervención técnica correspondiente."*
- **Variante 2:** *"Buenas tardes{nombre_saludo}. Tomamos conocimiento del reclamo correspondiente a {consorcio}{unidad}. El tema será revisado por la administración a partir de las 10:00 hs en horario habitual de atención."*
- **Variante 3:** *"Hola{nombre_saludo}, quedó asentado tu reporte para {consorcio}{unidad}. A partir de las 10:00 hs el equipo técnico evaluará la prioridad y las acciones a seguir."*

### J. Intención Ambigua / Menú Cordial (`INTENCION_AMBIGUA`)
- **Variante 1:** *"Hola{nombre_saludo}, ¿cómo estás? Para poder asistirte mejor, por favor indicanos el motivo de tu consulta (pago de expensas, reporte de avería, mudanza o urgencia) junto con tu edificio y departamento."*
- **Variante 2:** *"Buenas tardes{nombre_saludo}. Para derivar tu mensaje correctamente, por favor escribinos detallando tu consulta y mencionando a qué consorcio y unidad pertenecés."*
- **Variante 3:** *"Hola{nombre_saludo}, recibimos tu mensaje. Para orientarte adecuadamente, por favor decinos en qué podemos ayudarte e indicá tu dirección y departamento."*

---

## 3. Validación Preventiva en el Arranque

Al iniciar el servidor FastAPI, se invoca automáticamente:
```python
validate_templates_on_startup()
```
Esta función valida que:
1. Las 20 plantillas contengan exactamente 3 variantes cada una.
2. Ningún placeholder contenga errores tipográficos.
3. Se rechace cualquier plantilla que contenga caracteres emoji o lunfardo no institucional.
