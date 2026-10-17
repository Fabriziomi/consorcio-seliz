"""
Catálogo oficial de plantillas de comunicación institucional — Dra. Ivana Seliz Administraciones.
Normas de estilo:
- Tono: Español rioplatense formal (voseo profesional argentino).
- Cero emojis en mensajes, placeholders y metadatos.
- Selección Round-Robin determinista: len(historial) % 3.
- Cero alucinaciones: Solo variables provistas y verificadas.
"""

from typing import Dict, List, Any
import logging
from core.config import settings

logger = logging.getLogger(__name__)

TEMPLATES: Dict[str, List[str]] = {
    "ONBOARDING_DATOS": [
        (
            "Hola{nombre_saludo}, ¿cómo estás? Te comunicaste con la administración de la Dra. Ivana Seliz. "
            "Para poder registrar tu consulta y asistirte, ¿podrías indicarnos a qué edificio pertenecés y cuál es tu unidad funcional (piso y departamento)?"
        ),
        (
            "Hola{nombre_saludo}, gracias por contactar a la administración de la Dra. Ivana Seliz. "
            "Para poder canalizar tu mensaje con el equipo correspondiente, por favor decinos de qué consorcio y qué departamento nos escribís."
        ),
        (
            "Hola{nombre_saludo}, buenas tardes. Desde la administración de la Dra. Ivana Seliz te pedimos, por favor, "
            "que nos indiques tu edificio y número de unidad funcional (piso y letra) para poder gestionar tu mensaje."
        ),
    ],
    "ONBOARDING_REINTENTO_1": [
        (
            "Hola{nombre_saludo}, no pudimos identificar el edificio en nuestro padrón. "
            "Por favor, escribí la calle y altura exacta del inmueble, junto con tu piso y departamento."
        ),
        (
            "Disculpá{nombre_saludo}, no encontramos el consorcio con los datos provistos. "
            "¿Podrías reiterarnos la dirección exacta con calle, numeración y unidad funcional?"
        ),
        (
            "Hola{nombre_saludo}, necesitamos confirmar la dirección precisa. "
            "Indicá por favor la calle y número de puerta del consorcio y tu departamento para poder ubicarte en el sistema."
        ),
    ],
    "ONBOARDING_BAILOUT": [
        (
            "Hola{nombre_saludo}, no logramos validar los datos de tu edificio en el sistema. "
            "Dejamos asentado tu mensaje para que la Dra. Ivana Seliz lo revise personalmente a partir de las 10:00 hs en horario de oficina."
        ),
        (
            "Gracias por tu mensaje{nombre_saludo}. Al no poder verificar la dirección del inmueble, "
            "el caso queda derivado para su revisión manual por la administración a las 10:00 hs."
        ),
        (
            "Hola{nombre_saludo}, asentamos tu contacto para atención personalizada. "
            "El equipo de administración retomará tu consulta a partir de las 10:00 hs en horario habitual de atención."
        ),
    ],
    "EDIFICIO_NO_ADMINISTRADO": [
        (
            "Hola{nombre_saludo}, te informamos que la dirección indicada no se encuentra bajo la administración de la Dra. Ivana Seliz. "
            "Te sugerimos verificar los datos de contacto del administrador correspondiente a tu consorcio."
        ),
        (
            "Hola{nombre_saludo}, el inmueble mencionado no corresponde a los edificios administrados por nuestro estudio. "
            "Por favor, corroborá los datos de contacto provistos en la liquidación de expensas de tu edificio."
        ),
        (
            "Buenas tardes{nombre_saludo}. El edificio por el que consultás no está registrado en el padrón de esta administración. "
            "Te recomendamos contactar a la administración designada en tu consorcio."
        ),
    ],
    "SOLICITAR_EDIFICIO_EXPENSAS": [
        (
            "Hola{nombre_saludo}, para poder enviarte los datos de cuenta bancaria y CBU correspondientes al pago de expensas, "
            "¿podrías indicarnos la dirección de tu edificio?"
        ),
        (
            "Hola{nombre_saludo}, ¿a qué edificio pertenecés? Decinos la calle y altura para poder enviarte el CBU oficial de tu consorcio."
        ),
        (
            "Buenas tardes{nombre_saludo}, para brindarte la información bancaria exacta necesitamos saber a qué consorcio pertenecés. "
            "Por favor indicanos la dirección de tu edificio."
        ),
    ],
    "SOLICITAR_EDIFICIO_EMERGENCIA": [
        (
            "Hola{nombre_saludo}. Si estás ante una emergencia con riesgo inminente, comunicate de inmediato con Bomberos (100) o SAME (107). "
            "Para enviar la guardia técnica del edificio a la brevedad, por favor indicanos con urgencia la dirección exacta y piso."
        ),
        (
            "ATENCIÓN: Si hay peligro inminente (gas, fuego o derrumbe), llamá urgente a Bomberos (100), SAME (107) o Policía (911). "
            "Por favor escribinos la calle y número del edificio para despachar la guardia técnica correspondiente."
        ),
        (
            "Hola{nombre_saludo}. Ante situaciones de urgencia crítica llamá de inmediato al 100 (Bomberos) o 107 (SAME). "
            "Indicanos la dirección de tu edificio ya mismo para derivar la asistencia técnica del consorcio."
        ),
    ],
    "SOLICITAR_EDIFICIO_REINTENTO": [
        (
            "Hola{nombre_saludo}, no pudimos localizar la dirección indicada. Por favor escribí la calle y altura exacta de tu edificio."
        ),
        (
            "Disculpá{nombre_saludo}, necesitamos la calle y numeración exacta para identificar tu consorcio en el padrón."
        ),
        (
            "Hola{nombre_saludo}, no encontramos coincidencia con esa dirección. Por favor corroborá la calle y número del consorcio."
        ),
    ],
    "SOLICITAR_SOLO_UNIDAD": [
        (
            "Hola{nombre_saludo}, tenemos registrado el edificio {nombre_consorcio}. "
            "¿Cuál es tu unidad funcional (piso y departamento)?"
        ),
        (
            "Gracias{nombre_saludo}. Para completar el registro en {nombre_consorcio}, "
            "por favor indicanos tu número de piso y letra de departamento."
        ),
        (
            "Hola{nombre_saludo}, respecto al consorcio {nombre_consorcio}, "
            "¿nos confirmarías tu piso y departamento para dejar asentada tu unidad?"
        ),
    ],
    "SOLICITAR_UNIDAD_REINTENTO": [
        (
            "Hola{nombre_saludo}, no llegamos a interpretar el formato de la unidad. "
            "Por favor escribilo en formato habitual (por ejemplo: 4° B, PB A o Cochera 12)."
        ),
        (
            "Por favor{nombre_saludo}, indicanos claramente piso y departamento (por ejemplo: 2 A, 8 C o Local 1)."
        ),
        (
            "Hola{nombre_saludo}, requerimos el piso y departamento exacto (ejemplo: 5° B) para actualizar tu ficha en el edificio."
        ),
    ],
    "EXPENSAS_DATOS_BANCARIOS": [
        (
            "Hola{nombre_saludo}, te pasamos los datos oficiales para el pago de expensas de {nombre_consorcio}:\n\n"
            "• CBU: {cbu}\n"
            "• Alias: {alias}\n"
            "• CUIT: {cuit}\n\n"
            "Una vez efectuada la transferencia, remití por favor el comprobante por correo electrónico a {email_cobranzas} "
            "indicando consorcio y unidad funcional ({unidad}). Saludos cordiales."
        ),
        (
            "Hola{nombre_saludo}, a continuación tenés los datos bancarios para transferir las expensas de {nombre_consorcio}:\n\n"
            "• CBU: {cbu}\n"
            "• Alias: {alias}\n"
            "• CUIT: {cuit}\n\n"
            "Por favor enviá la constancia de pago a {email_cobranzas} señalando tu unidad ({unidad}) para su imputación contable. Saludos."
        ),
        (
            "Buenas tardes{nombre_saludo}. Te detallamos la cuenta bancaria de {nombre_consorcio}:\n\n"
            "• CBU: {cbu}\n"
            "• Alias: {alias}\n"
            "• CUIT: {cuit}\n\n"
            "Recordá que el comprobante de transferencia se recibe únicamente vía correo electrónico en {email_cobranzas} para su conciliación formal."
        ),
    ],
    "AVISO_PAGO_RECORDATORIO_EMAIL": [
        (
            "Hola{nombre_saludo}, tomamos nota de tu aviso de pago para la unidad {unidad} de {nombre_consorcio}.\n\n"
            "Por favor recordá remitir el comprobante adjunto a la casilla de cobranzas ({email_cobranzas}) "
            "para que el área contable proceda con la conciliación y emisión del recibo oficial. Saludos."
        ),
        (
            "Muchas gracias por avisar{nombre_saludo}. Para que la transferencia quede acreditada en la liquidación de {nombre_consorcio}, "
            "es indispensable enviar la constancia por correo a {email_cobranzas} indicando la unidad ({unidad}). Saludos."
        ),
        (
            "Hola{nombre_saludo}, registramos tu notificación de pago. Te pedimos que reenvíes el comprobante a {email_cobranzas} "
            "así el sector de cobranzas concilia la operación de la unidad {unidad}. Saludos cordiales."
        ),
    ],
    "ACUSE_FORMAL_RECLAMO": [
        (
            "Hola{nombre_saludo}, recibimos tu reporte correspondiente a la unidad {unidad} de {nombre_consorcio}. "
            "Queda registrado formalmente para ser evaluado y coordinado por el equipo de la Dra. Ivana Seliz a partir de las 10:00 hs en horario de oficina."
        ),
        (
            "Hola{nombre_saludo}, asentamos tu reclamo para {nombre_consorcio} ({unidad}). "
            "El equipo de administración lo analizará a primera hora a partir de las 10:00 hs para gestionar la respuesta o visita técnica pertinente."
        ),
        (
            "Buenas tardes{nombre_saludo}. Dejamos asentada tu consulta para el consorcio {nombre_consorcio} ({unidad}). "
            "Será revisada a las 10:00 hs en el inicio de la jornada administrativa para su curso correspondiente."
        ),
    ],
    "EMERGENCIA_CON_CONSORCIO": [
        (
            "Hola{nombre_saludo}. Ante una emergencia en {nombre_consorcio}, comunicate en forma prioritaria con las guardias técnicas:\n\n"
            "{telefonos_guardia}\n\n"
            "En caso de peligro inminente con riesgo de vida o colapso, llamá a Bomberos (100) o SAME (107). "
            "Dejamos asentado el aviso urgente para la administración."
        ),
        (
            "ATENCIÓN: Para la atención inmediata en {nombre_consorcio}, contactá a los teléfonos de guardia asignados:\n\n"
            "{telefonos_guardia}\n\n"
            "Si la situación lo requiere, intervení con servicios públicos de auxilio (Bomberos 100 / SAME 107). "
            "Notificamos de manera prioritaria al equipo de administración."
        ),
        (
            "Hola{nombre_saludo}. Te brindamos los contactos de auxilio técnico para {nombre_consorcio}:\n\n"
            "{telefonos_guardia}\n\n"
            "Recordá los números de auxilio público ante siniestros: Bomberos 100 y Emergencias Médicas 107. El reporte queda registrado con prioridad."
        ),
    ],
    "MUDANZA_INFO": [
        (
            "Hola{nombre_saludo}, te compartimos las pautas vigentes de mudanza para {nombre_consorcio}:\n\n"
            "{pautas_mudanza}\n\n"
            "Por favor recordá solicitar la reserva con al menos 48 hs hábiles de antelación y presentar el seguro del personal de flete. Saludos."
        ),
        (
            "Hola{nombre_saludo}, respecto a las mudanzas en {nombre_consorcio}:\n\n"
            "{pautas_mudanza}\n\n"
            "Tené en cuenta coordinar fecha y horario con la administración con antelación y proteger debidamente el ascensor. Saludos."
        ),
        (
            "Buenas tardes{nombre_saludo}. Las normas oficiales de mudanza para {nombre_consorcio} son:\n\n"
            "{pautas_mudanza}\n\n"
            "Se requiere coordinar previamente con administración para verificar disponibilidad y seguros correspondientes."
        ),
    ],
    "ADJUNTO_MUDO": [
        (
            "Hola{nombre_saludo}, recibimos tu archivo adjunto. "
            "Si se trata de un comprobante de pago de expensas, recordá remitirlo por correo a {email_cobranzas}. "
            "Si es una constancia de reclamo, queda registrada para ser revisada a las 10:00 hs por el equipo de administración."
        ),
        (
            "Hola{nombre_saludo}, acusamos recibo del archivo. "
            "De ser una constancia de transferencia bancaria, debe enviarse a {email_cobranzas} indicando tu unidad. "
            "Si adjuntás una foto por desperfecto edilicio, queda archivada para revisión a partir de las 10:00 hs."
        ),
        (
            "Buenas tardes{nombre_saludo}, recepcionamos el documento adjunto. "
            "Para pagos de expensas, el canal oficial es {email_cobranzas}. Si corresponde a una incidencia técnica, queda asentada para su tratamiento a las 10:00 hs."
        ),
    ],
    "AUDIO_INVALIDO": [
        (
            "Hola{nombre_saludo}, recibimos tu nota de voz pero no logramos escucharla con claridad. "
            "¿Podrías escribirnos tu consulta brevemente por texto indicando edificio y unidad para que podamos ayudarte?"
        ),
        (
            "Hola{nombre_saludo}, tuvimos dificultades para reproducir con nitidez el audio recibido. "
            "Te pedimos que nos escribas tu mensaje por este medio para poder gestionarlo adecuadamente."
        ),
        (
            "Buenas tardes{nombre_saludo}. No logramos interpretar con precisión la grabación enviada. "
            "Por favor dejanos tu mensaje por escrito junto a tu piso y departamento."
        ),
    ],
    "INTENCION_AMBIGUA": [
        (
            "Hola{nombre_saludo}, no llegamos a interpretar con precisión tu consulta. "
            "Por favor escribinos con mayor detalle indicando si se trata de expensas, un reclamo o una urgencia, junto a tu edificio y departamento."
        ),
        (
            "Hola{nombre_saludo}, ¿en qué podemos ayudarte? "
            "Por favor brindanos más precisiones sobre tu pedido indicando edificio y número de unidad."
        ),
        (
            "Buenas tardes{nombre_saludo}, para poder brindarte una respuesta precisa, "
            "por favor decinos en qué te podemos ayudar y a qué consorcio y unidad pertenecés."
        ),
    ],
    "CIERRE_CORDIAL": [
        (
            "Muchas gracias{nombre_saludo}. Quedamos a disposición por cualquier otra consulta. Saludos cordiales."
        ),
        (
            "De nada{nombre_saludo}. Que tengas muy buen día. Saludos cordiales desde la administración."
        ),
        (
            "Gracias a vos{nombre_saludo}. Saludos cordiales."
        ),
    ],
    "EMERGENCIA_GENERAL": [
        (
            "Hola{nombre_saludo}. Si estás ante una situación de urgencia con riesgo inminente en el edificio, por favor comunicate cuanto antes con la guardia al {telefono_guardia} o con los servicios de auxilio (Bomberos 100 / SAME 107).\n\n"
            "Dejamos asentado el aviso de forma prioritaria para la administración."
        ),
        (
            "ATENCIÓN: Si hay peligro inminente en el edificio, contactá a la brevedad a la guardia al {telefono_guardia} o a los servicios públicos (Bomberos 100 / SAME 107).\n\n"
            "Registramos la notificación de manera urgente para la administración."
        ),
        (
            "Hola{nombre_saludo}. Ante una emergencia en el inmueble comunicate de inmediato con la guardia al {telefono_guardia} o con auxilio (Bomberos 100 / SAME 107).\n\n"
            "El aviso queda registrado con prioridad para la administración."
        ),
    ],
    "SALUDO_INICIAL": [
        (
            "Hola{nombre_saludo}, ¿cómo estás? Decinos en qué te podemos ayudar y qué unidad tenés en el consorcio así lo revisamos."
        ),
        (
            "Hola{nombre_saludo}, gracias por comunicarte con la administración. ¿En qué podemos ayudarte hoy?"
        ),
        (
            "Buenas tardes{nombre_saludo}. ¿En qué podemos colaborarte desde la administración?"
        ),
    ],
    "BIENVENIDA_HORARIO": [
        (
            "Hola{nombre_saludo}, ¿cómo estás? Te comunicaste con la administración de la Dra. Ivana Seliz.\n"
            "Nuestro horario de atención es de lunes a viernes de 10 a 18 hs y sábados de 10 a 13 hs.\n"
            "¿En qué podemos ayudarte?"
        ),
        (
            "Hola{nombre_saludo}. La administración atiende de lunes a viernes de 10 a 18 hs y sábados de 10 a 13 hs. Decinos tu consulta."
        ),
        (
            "Buenas tardes{nombre_saludo}. Horario de administración: L-V 10 a 18 hs, Sáb 10 a 13 hs. ¿En qué te podemos ayudar?"
        ),
    ],
    "FUERA_HORARIO": [
        (
            "Hola{nombre_saludo}, ¿cómo estás? Recibimos tu mensaje. En este momento estamos fuera del horario de atención de la administración, pero lo revisamos con el equipo a primera hora a partir de las 10:00 hs para darte una respuesta.\n\n"
            "Si llega a ser una urgencia que requiera atención inmediata en el edificio (fuga de gas, rotura de caño o personas atrapadas en ascensor), por favor avisanos por este medio."
        ),
        (
            "Hola{nombre_saludo}. Recibimos tu comunicación fuera de nuestro horario habitual. Lo derivamos al equipo para responderte a las 10:00 hs. Ante una urgencia con riesgo en el edificio, por favor avisanos de inmediato."
        ),
        (
            "Buenas tardes{nombre_saludo}. Asentamos tu mensaje fuera de horario para tratamiento matutino a partir de las 10:00 hs. Si se trata de un siniestro o emergencia edilicia, notificalo por este canal."
        ),
    ],
    "SOLICITAR_CONSORCIO": [
        (
            "Hola{nombre_saludo}, para poder ayudarte con la información correspondiente, ¿me indicarías a qué edificio pertenecés y cuál es tu unidad funcional (piso y departamento)? Muchas gracias."
        ),
        (
            "Hola{nombre_saludo}. Para identificar tu expediente en el sistema, ¿podrías indicarnos tu consorcio y número de departamento?"
        ),
        (
            "Buenas tardes{nombre_saludo}. Por favor indicanos tu edificio y unidad funcional para poder asistirte."
        ),
    ],
    "SOLICITAR_CONSORCIO_PAGO": [
        (
            "Hola{nombre_saludo}, para poder facilitarte los datos de cuenta bancaria y CBU correspondientes para el pago de expensas, ¿podrías indicarnos de qué edificio y qué unidad funcional (piso y departamento) nos escribís? Así te enviamos la información exacta de tu consorcio."
        ),
        (
            "Hola{nombre_saludo}. Para remitirte la cuenta bancaria correcta para expensas, por favor indicanos la dirección de tu consorcio y número de unidad."
        ),
        (
            "Buenas tardes{nombre_saludo}. Decinos tu edificio y piso/departamento para hacerte llegar los datos de pago oficiales."
        ),
    ],
    "FUERA_HORARIO_SOLICITAR_EDIFICIO": [
        (
            "Hola{nombre_saludo}, ¿cómo estás? Recibimos tu mensaje para la administración. Para poder identificar tu reclamo y coordinarlo a primera hora con el equipo técnico correspondiente, ¿podrías indicarnos a qué edificio/consorcio pertenecés y tu unidad (piso y departamento)? Muchas gracias."
        ),
        (
            "Hola{nombre_saludo}. Para dejar registrado tu reporte para las 10:00 hs, por favor decinos a qué edificio y departamento pertenecés."
        ),
        (
            "Buenas tardes{nombre_saludo}. Necesitamos tu consorcio y unidad para procesar el aviso en horario administrativo."
        ),
    ],
    "EXPENSAS_PAGO_INFO": [
        (
            "Hola{nombre_saludo}, te paso los datos para la transferencia de expensas de {nombre_consorcio}:\n\n"
            "• CBU: {cbu}\n"
            "• Alias: {alias}\n"
            "• CUIT: {cuit}\n\n"
            "Una vez realizado el pago, envianos por favor el comprobante a {email_cobranzas} indicando tu unidad funcional ({unidad}). Saludos."
        ),
        (
            "Hola{nombre_saludo}. Datos oficiales para el pago de expensas ({nombre_consorcio}):\n\n"
            "• CBU: {cbu}\n"
            "• Alias: {alias}\n"
            "• CUIT: {cuit}\n\n"
            "Remití la constancia a {email_cobranzas} indicando tu unidad ({unidad}). Saludos cordiales."
        ),
        (
            "Buenas tardes{nombre_saludo}. Cuenta bancaria de {nombre_consorcio}:\n\n"
            "• CBU: {cbu}\n"
            "• Alias: {alias}\n"
            "• CUIT: {cuit}\n\n"
            "Enviá por favor el comprobante de transferencia a {email_cobranzas} ({unidad}). Saludos."
        ),
    ],
    "EXPENSAS_COMPROBANTE_RECIBIDO": [
        (
            "Hola{nombre_saludo}, muchas gracias por enviarnos la constancia de pago de expensas de {nombre_consorcio} para la unidad {unidad}.\n\n"
            "Ya lo derivamos al área contable ({email_cobranzas}) para su imputación y conciliación bancaria. En cuanto se confirme la acreditación, te enviaremos el recibo oficial correspondiente. Saludos."
        ),
        (
            "Hola{nombre_saludo}. Registramos el comprobante de expensas para {nombre_consorcio} ({unidad}). "
            "Se remite a cobranzas ({email_cobranzas}) para su debida imputación. Saludos."
        ),
        (
            "Buenas tardes{nombre_saludo}. Constancia recibida para {nombre_consorcio} ({unidad}). "
            "El sector de cobranzas ({email_cobranzas}) procederá con la conciliación contable. Saludos cordiales."
        ),
    ],
    "ATRIBUTO_DINAMICO_INFO": [
        (
            "Hola{nombre_saludo}, respecto a tu consulta sobre {etiqueta_atributo} en {nombre_consorcio}: {valor_atributo}."
        ),
        (
            "Hola{nombre_saludo}. Información sobre {etiqueta_atributo} en {nombre_consorcio}: {valor_atributo}."
        ),
        (
            "Buenas tardes{nombre_saludo}. En relación a {etiqueta_atributo} de {nombre_consorcio}: {valor_atributo}."
        ),
    ],
    "ATRIBUTO_SEGURIDAD_RESTRINGIDO": [
        (
            "Hola{nombre_saludo}, por motivos de seguridad del consorcio {nombre_consorcio}, la información sobre {etiqueta_atributo} no se divulga por este canal automático. "
            "Dejamos registrado tu pedido para que la administración o la guardia lo valide directamente con tu unidad ({unidad})."
        ),
        (
            "Hola{nombre_saludo}. Por políticas de seguridad edilicia en {nombre_consorcio}, la información sobre {etiqueta_atributo} requiere validación manual con la unidad ({unidad})."
        ),
        (
            "Buenas tardes{nombre_saludo}. Los datos de {etiqueta_atributo} en {nombre_consorcio} se coordinan de forma personalizada por seguridad para tu unidad ({unidad})."
        ),
    ],
    "FUERA_HORARIO_CONFIRMACION_EDIFICIO": [
        (
            "Hola{nombre_saludo}, muchas gracias por indicarnos los datos de tu edificio y unidad ({nombre_consorcio}, {unidad}).\n\n"
            "Dejamos registrado tu mensaje para coordinarlo a primera hora a partir de las 10:00 hs con el equipo correspondiente. Saludos."
        ),
        (
            "Hola{nombre_saludo}. Quedan registrados los datos de {nombre_consorcio} ({unidad}) para su atención a partir de las 10:00 hs. Saludos."
        ),
        (
            "Buenas tardes{nombre_saludo}. Asentamos tu edificio ({nombre_consorcio}, {unidad}) para tratamiento a primera hora a las 10:00 hs. Saludos."
        ),
    ],
    "ACUSE_RECIBO_NEUTRO": [
        (
            "Hola{nombre_saludo}, recibimos tu mensaje para la administración. Lo revisamos con el equipo y te respondemos en nuestro horario habitual de atención (lunes a viernes de 10 a 18 hs | sábados de 10 a 13 hs)."
        ),
        (
            "Hola{nombre_saludo}. Recibimos tu consulta. Te responderemos dentro de la jornada habitual de atención administrativa."
        ),
        (
            "Buenas tardes{nombre_saludo}. Mensaje asentado para ser atendido en horario de oficina (L-V 10 a 18 hs, Sáb 10 a 13 hs)."
        ),
    ],
    "RUIDO_CORTO": [
        (
            "Hola{nombre_saludo}, no llegamos a interpretar tu mensaje. Por favor escribinos con mayor detalle tu consulta o reclamo junto a tu número de unidad así te podemos ayudar."
        ),
        (
            "Hola{nombre_saludo}. Por favor envianos tu consulta con mayor detalle y tu piso/departamento para poder responderte."
        ),
        (
            "Buenas tardes{nombre_saludo}. Brindanos más precisiones sobre tu consulta edilicia junto a tu número de unidad."
        ),
    ],
}


def render_template(template_key: str, historial_len: int = 0, **kwargs: Any) -> str:
    """
    Selecciona determinísticamente una variante según len(historial) % 3
    y renderiza los placeholders con valores sanitizados.
    """
    variants = TEMPLATES.get(template_key)
    if not variants:
        logger.warning("Plantilla '%s' no encontrada. Utilizando fallback ACUSE_FORMAL_RECLAMO.", template_key)
        variants = TEMPLATES["ACUSE_FORMAL_RECLAMO"]

    variant_index = abs(historial_len) % len(variants)
    selected_template = variants[variant_index]

    user_name = kwargs.get("user_name") or kwargs.get("nombre_contacto")
    if user_name and isinstance(user_name, str) and user_name.strip():
        first_name = user_name.strip().split()[0].capitalize()
        if first_name.lower() not in ("vecino", "vecina", "desconocido", "none"):
            kwargs.setdefault("nombre_saludo", f" {first_name}")
        else:
            kwargs.setdefault("nombre_saludo", "")
    else:
        kwargs.setdefault("nombre_saludo", "")

    kwargs.setdefault("unidad", kwargs.get("unidad_funcional") or "tu unidad")
    kwargs.setdefault("unidad_funcional", kwargs.get("unidad") or "tu unidad")
    kwargs.setdefault("nombre_consorcio", "tu consorcio")
    kwargs.setdefault("cbu", "")
    kwargs.setdefault("alias", "")
    kwargs.setdefault("cuit", "")

    if "{email_cobranzas}" in selected_template and not kwargs.get("email_cobranzas"):
        admin_email = getattr(settings, "ADMIN_EMAIL_COBRANZAS", None)
        if admin_email:
            kwargs["email_cobranzas"] = admin_email
        else:
            logger.error("[TEMPLATES] Falta parámetro 'email_cobranzas' para plantilla '%s' y no está configurado en ADMIN_EMAIL_COBRANZAS.", template_key)
            kwargs["email_cobranzas"] = ""

    if ("{telefono_guardia}" in selected_template or "{telefonos_guardia}" in selected_template) and not kwargs.get("telefono_guardia") and not kwargs.get("telefonos_guardia"):
        admin_guardia = getattr(settings, "ADMIN_TELEFONO_GUARDIA", None)
        if admin_guardia:
            kwargs["telefono_guardia"] = admin_guardia
            kwargs["telefonos_guardia"] = f"• Guardia general administración: {admin_guardia}"
        else:
            logger.error("[TEMPLATES] Faltan teléfonos de guardia para plantilla '%s' y no está configurado ADMIN_TELEFONO_GUARDIA.", template_key)
            kwargs["telefono_guardia"] = ""
            kwargs["telefonos_guardia"] = ""
    else:
        kwargs.setdefault("telefono_guardia", kwargs.get("telefonos_guardia") or "")
        kwargs.setdefault("telefonos_guardia", kwargs.get("telefono_guardia") or "")

    kwargs.setdefault("etiqueta_atributo", "la consulta")
    kwargs.setdefault("valor_atributo", "información provista por la administración")

    if "{pautas_mudanza}" in selected_template and not kwargs.get("pautas_mudanza"):
        default_pautas = getattr(settings, "DEFAULT_PAUTAS_MUDANZA", None)
        if default_pautas:
            kwargs["pautas_mudanza"] = default_pautas
        else:
            logger.warning("[TEMPLATES] Falta parámetro 'pautas_mudanza' para plantilla '%s' y no está configurado en DEFAULT_PAUTAS_MUDANZA.", template_key)
            kwargs["pautas_mudanza"] = ""

    try:
        return selected_template.format(**kwargs)
    except KeyError as exc:
        logger.error("Error al renderizar plantilla '%s' variante %d: falta parámetro %s", template_key, variant_index, exc)
        clean_text = selected_template.replace("{" + str(exc).strip("'") + "}", "")
        return clean_text


def validate_templates_on_startup() -> None:
    """
    Valida en el arranque que todas las plantillas y variantes posean sintaxis válida
    y puedan formatearse con el conjunto de parámetros de prueba estándar (Fail-Fast).
    """
    dummy_params = {
        "nombre_saludo": " Juan",
        "nombre_consorcio": "Consorcio Callao 2334",
        "unidad": "4° B",
        "unidad_funcional": "4° B",
        "cbu": "0140000000000000000002",
        "alias": "CALLAO.2334.EXPENSAS",
        "cuit": "30-71000000-1",
        "email_cobranzas": "callao2334@selizadministraciones.com.ar",
        "telefono_guardia": "+54 9 11 0000-0000",
        "telefonos_guardia": "• Ascensores: +54 9 11 4444-1111\n• Plomería: +54 9 11 4444-2222",
        "pautas_mudanza": "• Días hábiles de 09:00 a 17:00 hs.",
        "etiqueta_atributo": "código de acceso",
        "valor_atributo": "1234",
    }

    total_variants = 0
    for key, variants in TEMPLATES.items():
        if len(variants) != 3:
            raise ValueError(f"La plantilla '{key}' no posee exactamente 3 variantes (posee {len(variants)}).")
        for idx, variant in enumerate(variants):
            total_variants += 1
            try:
                variant.format(**dummy_params)
            except Exception as exc:
                raise ValueError(
                    f"Fallo de validación en plantilla '{key}' (variante {idx}): {exc}"
                ) from exc

    logger.info("Validación exitosa de plantillas: %d claves y %d variantes verificadas.", len(TEMPLATES), total_variants)
