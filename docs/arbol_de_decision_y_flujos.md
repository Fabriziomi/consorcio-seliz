# Especificación del Árbol de Decisión, Flujos y FSM

Este documento formaliza las reglas de negocio, los estados de conversación y los flujos operativos del sistema de atención automatizada por WhatsApp para la administración de consorcios de la **Dra. Ivana Seliz**.

---

## 1. Reglas de Negocio Fundamentales

1. **Horarios Operativos y Silencio del Bot:**
   - **Horario de Oficina (Silencio Total del Bot):**
     - Lunes a Viernes de 10:00 a 18:00 hs.
     - Sábados de 10:00 a 13:00 hs.
     - *Regla:* Durante este horario atiende la Dra. Ivana Seliz personalmente desde su teléfono físico. El bot permanece en silencio estricto.
   - **Horario de Operación del Bot:**
     - Fuera del horario de oficina, domingos completos y feriados nacionales argentinos (`FERIADOS_AR`).
   - **Quiet Hours (00:00 a 07:30 hs):**
     - Silencio nocturno total para no despertar a los vecinos.
     - Los mensajes no urgentes se persisten con `needs_human_review = True` para revisión humana matutina a las 10:00 hs.
     - No se disparan ráfagas de respuestas automáticas a las 07:31 hs.
2. **Emergencias Críticas 24/7:**
   - Incendios, escape de gas, inundaciones graves o personas atrapadas en ascensor.
   - Operan las 24 horas sin importar el horario ni las Quiet Hours.
   - Si no se conoce el edificio, se entregan números públicos inmediatos (Bomberos 100, SAME 107, Policía 911) mientras se solicita la dirección con urgencia.
   - Si el edificio está identificado, se despachan los números de guardia técnica específicos (ascensorista, plomero de urgencia, portería).
3. **Privacidad de Consorcios (Regla Inquebrantable):**
   - El bot **NUNCA** lista ni enumera el padrón de consorcios administrados a un usuario no identificado.
   - Si falta el edificio, solicita calle y altura sin dar opciones.
4. **Cobranzas y Trámites de Pago:**
   - Cero pasarelas ni botones de pago en WhatsApp.
   - Todo comprobante se remite obligatoriamente al correo oficial del consorcio (`email_cobranzas`).
   - El bot entrega CBU, Alias, CUIT y cuenta oficial, pero no concilia pagos por WhatsApp.
5. **Takeover Humano (12 Horas de TTL):**
   - Si Ivana envía un mensaje manual desde su celular (`fromMe: true` no emitido por el bot), la conversación entra en silencio automático durante 12 horas.
6. **Early Binding de Perfil:**
   - En cuanto un mensaje revela un consorcio o unidad válidos, se persisten inmediatamente en la tabla `contactos` antes de evaluar la FSM, evitando preguntas repetitivas.
7. **Comandos de Escape:**
   - Si el usuario escribe `0`, `menu`, `reiniciar`, `inicio`, `cancelar` o `salir`, la FSM resetea su estado inmediatamente a `IDLE`, reinicia `retry_count = 0` y emite la plantilla cordial de reinicio.

---

## 2. Diagrama General del Árbol de Decisión

```mermaid
flowchart TD
    Start([Mensaje Entrante de WhatsApp]) --> Webhook[FastAPI: Webhook Evolution API]
    Webhook --> GroupCheck{¿Grupo @g.us o Difusión?}
    
    GroupCheck -- Sí --> Drop[Descarte Inmediato ms 0]
    GroupCheck -- No --> Debounce[Redis Buffer Debounce 8-10s]
    
    Debounce --> BotActive{¿Bot Activo y Contacto Habilitado?}
    BotActive -- No --> Silence[Silencio Permanente]
    BotActive -- Sí --> TakeoverCheck{¿Takeover Manual Activo < 12h?}
    
    TakeoverCheck -- Sí --> SilenceTakeover[Silencio por Takeover de Ivana]
    TakeoverCheck -- No --> OfficeHours{¿Dentro de Horario de Oficina?\nL-V 10-18hs / Sáb 10-13hs}
    
    OfficeHours -- En Oficina --> SilenceOffice[Silencio Estricto: Atiende Ivana]
    OfficeHours -- Fuera de Oficina --> AudioCheck{¿Es Audio?}
    
    AudioCheck -- Sí --> Whisper[Groq Whisper API < 350ms] --> FastTokens
    AudioCheck -- No --> FastTokens{Content Guardrails}
    
    FastTokens -- Ruido asd/zz --> DropNoise[Silencio / Descarte Ruido]
    FastTokens -- Agradecimiento gracias/ok --> IntelligentSilence[Silencio Inteligente Anti-Spam]
    FastTokens -- Saludo puro --> WelcomeTemplate[Plantilla Bienvenida Institucional]
    FastTokens -- Mensaje con Contenido --> EscapeCheck{¿Comando Escape?\n0, menu, reiniciar}
    
    EscapeCheck -- Sí --> ResetFSM[Reset FSM a IDLE]
    EscapeCheck -- No --> TTLCheck{¿Inactividad > 120 min?}
    
    TTLCheck -- Sí --> ResetTTL[Reset FSM a IDLE] --> RouterAI
    TTLCheck -- No --> RouterAI[Router Tipado Jev 1.14 / Gemini Fallback]
    
    RouterAI --> EarlyBinding[Early Binding: Persistir Consorcio/Unidad en BD]
    EarlyBinding --> QuietCheck{¿Quiet Hours 00:00-07:30\ny no es Emergencia?}
    
    QuietCheck -- Sí --> NightSilence[Silencio Nocturno\nneeds_human_review = True]
    QuietCheck -- No --> FSM[ConversationFSM]
    
    FSM --> StateSwitch{Estado FSM}
    StateSwitch -- IDLE --> BranchIDLE[Rama: Reposo y Consultas Directas]
    StateSwitch -- SOLICITANDO_EDIFICIO --> BranchEdificio[Rama: Esperando Edificio]
    StateSwitch -- ONBOARDING_DATOS --> BranchOnboarding[Rama: Esperando Edificio y Unidad]
    StateSwitch -- ESPERANDO_SOLO_UNIDAD --> BranchUnidad[Rama: Esperando Solo Unidad]
    
    BranchIDLE --> SelectTemplate[Round-Robin Template len % 3]
    BranchEdificio --> SelectTemplate
    BranchOnboarding --> SelectTemplate
    BranchUnidad --> SelectTemplate
    
    SelectTemplate --> Audit[Log JSONL en fsm_audit.log]
    Audit --> AntiBan[Presencia composing 1.5s-3.0s]
    AntiBan --> Send[Despacho WhatsApp vía Evolution API]
```

---

## 3. Especificación de Ramas Operativas

### Rama 1: Emergencia Crítica 24/7
- **Activación:** Fuego, escape de gas, inundación de columna principal, personas atrapadas en ascensor, derrumbe.
- **Acción:**
  - Si el usuario tiene consorcio registrado: entrega teléfonos de guardia técnica directa (portería, ascensorista, plomero de guardia) y números públicos de auxilio (100, 107, 911).
  - Si el usuario no tiene consorcio registrado: entrega números públicos y solicita con urgencia la dirección del edificio (`SOLICITANDO_EDIFICIO` con `pending_intent = EMERGENCIA`).
  - Persiste el mensaje y marca `needs_human_review = True` con prioridad `CRÍTICA`.

### Rama 2: Expensas y Cobranzas
- **Sub-flujo A: Pedido de CBU / Datos de Cuenta:**
  - Si el usuario tiene consorcio asignado: entrega CBU, Alias, CUIT, Titular y correo oficial de cobranzas.
  - Si el usuario no tiene consorcio: transiciona a `SOLICITANDO_EDIFICIO` con `pending_intent = EXPENSAS_DATOS_PAGO`.
- **Sub-flujo B: Aviso de Transferencia / Envío de Comprobante:**
  - El bot recuerda enviar el comprobante adjunto al correo oficial (`email_cobranzas`).
  - Si viene una imagen o PDF adjunto, se persiste en la conversación y se confirma su recepción para imputación contable.
- **Sub-flujo C: Reclamos de Saldo:**
  - Se registra el mensaje para análisis administrativo de Ivana a las 10:00 hs (`needs_human_review = True`).

### Rama 3: Reclamos y Mantenimiento Edilicio
- **Condición:**
  - Requiere consorcio y unidad funcional completos.
  - Si falta consorcio y unidad: transiciona a `ONBOARDING_DATOS`.
  - Si tiene consorcio pero falta unidad: transiciona a `ESPERANDO_SOLO_UNIDAD`.
  - Si tiene ambos: emite acuse de recibo formal confirmando que el reclamo fue registrado para evaluación por el equipo técnico a las 10:00 hs (`needs_human_review = True`).

### Rama 4: Mudanzas y Normas de Convivencia
- Si el consorcio tiene `pautas_mudanza` cargadas, se envían los horarios y requisitos de seguros de ART.
- Se marca para revisión humana si se solicita reserva de ascensor o coordinación con portería.

---

## 4. Máquina de Estados Finitos (`ConversationFSM`)

```mermaid
stateDiagram-v2
    [*] --> IDLE
    
    IDLE --> IDLE : Perfil completo + Consulta resuelta
    IDLE --> SOLICITANDO_EDIFICIO : Falta edificio para CBU o Emergencia
    IDLE --> ONBOARDING_DATOS : Reclamo / Mudanza sin datos
    IDLE --> ESPERANDO_SOLO_UNIDAD : Consorcio conocido, falta piso/depto
    
    SOLICITANDO_EDIFICIO --> IDLE : Consorcio válido identificado\nDespacha pending_intent
    SOLICITANDO_EDIFICIO --> SOLICITANDO_EDIFICIO : Reintento 1 (Dirección no reconocida)
    SOLICITANDO_EDIFICIO --> IDLE : Bailout (Intento 2 fallido)\nneeds_human_review = True (10:00 hs)
    SOLICITANDO_EDIFICIO --> IDLE : Edificio no administrado
    
    ONBOARDING_DATOS --> IDLE : Edificio y unidad provistos juntos\nEarly Binding + Despacha pending_intent
    ONBOARDING_DATOS --> ESPERANDO_SOLO_UNIDAD : Indicó consorcio pero olvidó unidad
    ONBOARDING_DATOS --> ONBOARDING_DATOS : Reintento 1 (No se entendió)
    ONBOARDING_DATOS --> IDLE : Bailout (Intento 2 fallido)\nneeds_human_review = True (10:00 hs)
    
    ESPERANDO_SOLO_UNIDAD --> IDLE : Unidad válida provista (ej: 4° B)\nEarly Binding + Despacha pending_intent
    ESPERANDO_SOLO_UNIDAD --> ESPERANDO_SOLO_UNIDAD : Reintento 1 (Formato no claro)
    ESPERANDO_SOLO_UNIDAD --> IDLE : Bailout (Intento 2 fallido)\nneeds_human_review = True (10:00 hs)
    
    IDLE --> IDLE : Escape (0, menu, reiniciar) -> Reset
    SOLICITANDO_EDIFICIO --> IDLE : Escape / TTL > 120m -> Reset
    ONBOARDING_DATOS --> IDLE : Escape / TTL > 120m -> Reset
    ESPERANDO_SOLO_UNIDAD --> IDLE : Escape / TTL > 120m -> Reset
```
