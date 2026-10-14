"""
Plantillas de mensajes institucionales de la administración de la Dra. Ivana Seliz.
Tono: Humano, profesional, sobrio, empático y resolutivo.
Sin modismos de IA, sin mayúsculas exageradas ni emojis estridentes.
"""

TEMPLATES = {
    "SALUDO_INICIAL": (
        "Hola{nombre_saludo}, ¿cómo estás? Decinos en qué te podemos ayudar y qué unidad tenés en el consorcio así lo revisamos."
    ),

    "BIENVENIDA_HORARIO": (
        "Hola{nombre_saludo}, ¿cómo estás? Te comunicaste con la administración de la Dra. Ivana Seliz.\n"
        "Nuestro horario de atención es de lunes a viernes de 10 a 18 hs y sábados de 10 a 13 hs.\n"
        "¿En qué podemos ayudarte?"
    ),
    
    "FUERA_HORARIO": (
        "Hola{nombre_saludo}, ¿cómo estás? Recibimos tu mensaje. En este momento estamos fuera del horario de atención de la administración, pero lo revisamos con el equipo a primera hora a partir de las 10:00 hs para darte una respuesta.\n\n"
        "Si llega a ser una urgencia que requiera atención inmediata en el edificio (fuga de gas, rotura de caño o personas atrapadas en ascensor), por favor avisanos por este medio."
    ),

    "EMERGENCIA_GENERAL": (
        "Hola{nombre_saludo}. Si estás ante una situación de urgencia con riesgo inminente en el edificio, por favor comunicate cuanto antes con la guardia al {telefono_guardia} o con los servicios de auxilio (Bomberos 100 / SAME 107).\n\n"
        "Dejamos asentado el aviso de forma prioritaria para la administración."
    ),

    "SOLICITAR_CONSORCIO": (
        "Hola{nombre_saludo}, para poder ayudarte con la información correspondiente, ¿me indicarías a qué edificio pertenecés y cuál es tu unidad funcional (piso y departamento)? Muchas gracias."
    ),

    "SOLICITAR_CONSORCIO_PAGO": (
        "Hola{nombre_saludo}, para poder facilitarte los datos de cuenta bancaria y CBU correspondientes para el pago de expensas, ¿podrías indicarnos de qué edificio y qué unidad funcional (piso y departamento) nos escribís? Así te enviamos la información exacta de tu consorcio."
    ),

    "FUERA_HORARIO_SOLICITAR_EDIFICIO": (
        "Hola{nombre_saludo}, ¿cómo estás? Recibimos tu mensaje para la administración. Para poder identificar tu reclamo y coordinarlo a primera hora con el equipo técnico correspondiente, ¿podrías indicarnos a qué edificio/consorcio pertenecés y tu unidad (piso y departamento)? Muchas gracias."
    ),

    "EXPENSAS_PAGO_INFO": (
        "Hola{nombre_saludo}, te paso los datos para la transferencia de expensas de {nombre_consorcio}:\n\n"
        "• CBU: {cbu}\n"
        "• Alias: {alias}\n"
        "• CUIT: {cuit}\n\n"
        "Una vez realizado el pago, envianos por favor el comprobante a {email_cobranzas} indicando tu unidad funcional ({unidad}). Saludos."
    ),

    "EXPENSAS_COMPROBANTE_RECIBIDO": (
        "Hola{nombre_saludo}, muchas gracias por enviarnos la constancia de pago de expensas de {nombre_consorcio} para la unidad {unidad}.\n\n"
        "Ya lo derivamos al área contable ({email_cobranzas}) para su imputación y conciliación bancaria. En cuanto se confirme la acreditación, te enviaremos el recibo oficial correspondiente. Saludos."
    ),

    "MUDANZA_INFO": (
        "Hola{nombre_saludo}, te compartimos las pautas oficiales de mudanza para {nombre_consorcio}:\n\n"
        "• {pautas_mudanza}\n\n"
        "Por favor recordá coordinar con la administración con al menos 48 hs hábiles de antelación y presentar el seguro correspondiente si contratás flete. Saludos."
    ),

    "ATRIBUTO_DINAMICO_INFO": (
        "Hola{nombre_saludo}, respecto a tu consulta sobre {etiqueta_atributo} en {nombre_consorcio}: {valor_atributo}."
    ),

    "ATRIBUTO_SEGURIDAD_RESTRINGIDO": (
        "Hola{nombre_saludo}, por motivos de seguridad del consorcio {nombre_consorcio}, la información sobre {etiqueta_atributo} no se divulga por este canal automático. "
        "Dejamos registrado tu pedido para que la administración o la guardia lo valide directamente con tu unidad ({unidad})."
    ),

    "ACUSE_RECIBO_NEUTRO": (
        "Hola{nombre_saludo}, recibimos tu mensaje para la administración. Lo revisamos con el equipo y te respondemos en nuestro horario habitual de atención (lunes a viernes de 10 a 18 hs | sábados de 10 a 13 hs)."
    ),

    "RUIDO_CORTO": (
        "Hola{nombre_saludo}, no llegamos a interpretar tu mensaje. Por favor escribinos con mayor detalle tu consulta o reclamo junto a tu número de unidad así te podemos ayudar."
    ),
}


def render_template(template_key: str, **kwargs) -> str:
    """Renderiza una plantilla textual con tono humano y parámetros personalizados."""
    template = TEMPLATES.get(template_key, TEMPLATES["ACUSE_RECIBO_NEUTRO"])

    # Personalización sutil del saludo si se cuenta con el nombre del vecino
    user_name = kwargs.get("user_name") or kwargs.get("nombre_contacto")
    if user_name and isinstance(user_name, str) and user_name.strip() and user_name.strip().lower() != "vecino":
        first_name = user_name.strip().split()[0]
        kwargs.setdefault("nombre_saludo", f" {first_name}")
    else:
        kwargs.setdefault("nombre_saludo", "")

    # Parámetros por defecto para evitar KeyErrors
    kwargs.setdefault("unidad", kwargs.get("unidad_funcional") or "tu unidad")
    kwargs.setdefault("nombre_consorcio", "tu consorcio")
    kwargs.setdefault("cbu", "0140000000000000000001")
    kwargs.setdefault("alias", "CONSORCIO.SELIZ.OFICIAL")
    kwargs.setdefault("cuit", "30-71122334-5")
    kwargs.setdefault("email_cobranzas", "cobranzas@selizadministraciones.com.ar")
    kwargs.setdefault("telefono_guardia", "+54 9 11 6248-3302")

    return template.format(**kwargs)
