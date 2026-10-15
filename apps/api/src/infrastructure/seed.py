from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from core.logging import logger
from infrastructure.models import (
    ConsorcioModel,
    ConsorcioAtributoDinamicoModel,
    ContactoModel,
    TicketConsultaModel,
    UsuarioModel,
    FaqAprobadaModel,
    EtiquetaModel,
    ConversacionModel,
    MensajeModel,
)
from domain.schemas import (
    RolContacto,
    RolUsuario,
    PrioridadTicket,
    EstadoTicket,
    EstadoConversacion,
    TipoMensaje,
    EnviadoPor,
)
from core.security import hash_password


async def seed_initial_data(db: AsyncSession):
    """
    Pobla la base de datos con los consorcios administrados por Dra. Ivana Seliz,
    atributos dinámicos, contactos de prueba y tickets iniciales si la base está vacía.
    """
    # 0. Verificar y sembrar usuario administrador principal
    user_res = await db.execute(select(UsuarioModel).where(UsuarioModel.email == "admin@selizadministraciones.com.ar"))
    admin_user = user_res.scalar_one_or_none()
    if not admin_user:
        logger.info("[DB_SEED] Creando usuario administrador por defecto: admin@selizadministraciones.com.ar")
        admin_user = UsuarioModel(
            id="user-admin-seliz",
            email="admin@selizadministraciones.com.ar",
            password_hash=hash_password("AdminSeliz2026!"),
            nombre_completo="Dra. Ivana Seliz",
            rol=RolUsuario.SUPER_ADMIN,
            activo=True,
        )
        operador_user = UsuarioModel(
            id="user-operador-1",
            email="operador@selizadministraciones.com.ar",
            password_hash=hash_password("Operador2026!"),
            nombre_completo="Mesa de Entrada y Guardia",
            rol=RolUsuario.OPERADOR,
            activo=True,
        )
        db.add_all([admin_user, operador_user])
        await db.commit()

    res = await db.execute(select(ConsorcioModel))
    existing = res.scalars().first()
    if existing:
        logger.info("[DB_SEED] La base de datos ya cuenta con consorcios. Omitiendo seed de consorcios.")
        return

    logger.info("[DB_SEED] Base de datos vacía de consorcios. Sembrando datos iniciales de Consorcios Seliz...")

    # 1. Consorcios
    c1 = ConsorcioModel(
        id="cons-corrientes-lavalle",
        nombre="Consorcio Corrientes y Lavalle (Torres, Cochera y Galería)",
        direccion="Av. Corrientes 1240 / Lavalle 1241, CABA",
        cuit="30-71122334-5",
        cbu_bancario="0140000000000000000001",
        alias_bancario="CONSORCIO.LAVALLE.OFICIAL",
        email_cobranzas="cobranzas.lavalle@selizadministraciones.com.ar",
        telefono_porteria="+54 9 11 4371-0001",
        emergencia_ascensores="+54 9 11 4444-1111",
        emergencia_plomeria="+54 9 11 4444-2222",
        pautas_mudanza="Lunes a Viernes de 9 a 17 hs y Sábados de 9 a 13 hs. Presentar seguro flete 48hs antes.",
        activo=True,
    )

    c2 = ConsorcioModel(
        id="cons-callao-2334",
        nombre="Consorcio Callao 2334",
        direccion="Av. Callao 2334, Recoleta, CABA",
        cuit="30-71998877-6",
        cbu_bancario="0140000000000000000002",
        alias_bancario="CALLAO.2334.EXPENSAS",
        email_cobranzas="callao2334@selizadministraciones.com.ar",
        telefono_porteria="+54 9 11 4801-9999",
        emergencia_ascensores="+54 9 11 4444-3333",
        emergencia_plomeria="+54 9 11 4444-4444",
        pautas_mudanza="Lunes a Viernes de 10 a 16 hs exclusivamente.",
        activo=True,
    )

    db.add_all([c1, c2])
    await db.flush()

    # 2. Atributos Dinámicos
    attrs = [
        # Corrientes y Lavalle
        ConsorcioAtributoDinamicoModel(
            id="attr-c1-1",
            consorcio_id="cons-corrientes-lavalle",
            clave="codigo_alarma_palier",
            etiqueta_visible="Código de Alarma Palier",
            valor="9842#",
            es_publico_vecinos=False,  # Protegido por seguridad
        ),
        ConsorcioAtributoDinamicoModel(
            id="attr-c1-2",
            consorcio_id="cons-corrientes-lavalle",
            clave="piso_sum",
            etiqueta_visible="Ubicación SUM y Parrilla",
            valor="Piso 15 Torre Lavalle",
            es_publico_vecinos=True,
        ),
        ConsorcioAtributoDinamicoModel(
            id="attr-c1-3",
            consorcio_id="cons-corrientes-lavalle",
            clave="encargado_nombre",
            etiqueta_visible="Encargado Titular",
            valor="Roberto Martínez (+54 9 11 4371-0002)",
            es_publico_vecinos=True,
        ),
        # Callao 2334
        ConsorcioAtributoDinamicoModel(
            id="attr-c2-1",
            consorcio_id="cons-callao-2334",
            clave="llave_tanque_agua",
            etiqueta_visible="Ubicación Llave Tanque",
            valor="Guardada en tablero técnico central",
            es_publico_vecinos=False,  # Protegido por seguridad
        ),
        ConsorcioAtributoDinamicoModel(
            id="attr-c2-2",
            consorcio_id="cons-callao-2334",
            clave="horario_retiro_basura",
            etiqueta_visible="Horario de Basura",
            valor="Todos los días de 20:00 a 21:00 hs",
            es_publico_vecinos=True,
        ),
    ]
    db.add_all(attrs)
    await db.flush()

    # 3. Contactos
    contactos = [
        ContactoModel(
            id="cont-1",
            telefono_wa="+5491144558899",
            nombre_completo="Carlos Méndez",
            consorcio_id="cons-corrientes-lavalle",
            unidad_funcional="Torre Corrientes 4° B",
            rol=RolContacto.PROPIETARIO,
        ),
        ContactoModel(
            id="cont-2",
            telefono_wa="+5491166778899",
            nombre_completo="Lucía Rossi",
            consorcio_id="cons-callao-2334",
            unidad_funcional="7° A",
            rol=RolContacto.INQUILINO,
        ),
        ContactoModel(
            id="cont-3",
            telefono_wa="+5491133221100",
            nombre_completo="Mariano Gómez",
            consorcio_id="cons-corrientes-lavalle",
            unidad_funcional="Cochera 14",
            rol=RolContacto.PROPIETARIO,
        ),
    ]
    db.add_all(contactos)
    await db.flush()

    # 4. Tickets Iniciales
    tickets = [
        TicketConsultaModel(
            id="tick-1042",
            contacto_id="cont-1",
            consorcio_id="cons-corrientes-lavalle",
            intencion="RECLAMO",
            sub_intencion="CORTE_LUZ_PALIER",
            prioridad=PrioridadTicket.ALTA,
            estado=EstadoTicket.EN_REVISION,
            descripcion="Corte de luz en palier del piso 4 Torre Corrientes.",
        ),
        TicketConsultaModel(
            id="tick-1041",
            contacto_id="cont-2",
            consorcio_id="cons-callao-2334",
            intencion="EXPENSAS",
            sub_intencion="CONSULTA_DATOS_PAGO",
            prioridad=PrioridadTicket.NORMAL,
            estado=EstadoTicket.NUEVO,
            descripcion="Consulta de CBU y datos de pago de expensas.",
        ),
        TicketConsultaModel(
            id="tick-1040",
            contacto_id="cont-3",
            consorcio_id="cons-corrientes-lavalle",
            intencion="EMERGENCIA",
            sub_intencion="ASCENSOR_ATRAPADOS",
            prioridad=PrioridadTicket.CRITICA,
            estado=EstadoTicket.DERIVADO,
            descripcion="Personas atrapadas en ascensor Torre Lavalle.",
        ),
    ]
    db.add_all(tickets)

    # 5. FAQs Homologadas Iniciales
    faqs = [
        FaqAprobadaModel(
            id="faq-1",
            consorcio_id="cons-corrientes-lavalle",
            pregunta="¿Cuáles son los horarios permitidos para mudanzas?",
            respuesta_oficial="Lunes a viernes de 09:00 a 17:00 hs y sábados de 09:00 a 13:00 hs. Se debe presentar el seguro del flete con 48 hs de antelación en portería.",
            activo=True,
        ),
        FaqAprobadaModel(
            id="faq-2",
            consorcio_id="cons-callao-2334",
            pregunta="¿Cuáles son los horarios de mudanza en Callao 2334?",
            respuesta_oficial="Lunes a viernes de 10:00 a 16:00 hs exclusivamente. Días sábados y feriados no se permiten mudanzas.",
            activo=True,
        ),
        FaqAprobadaModel(
            id="faq-3",
            consorcio_id=None,
            pregunta="¿En qué horario se puede sacar la basura?",
            respuesta_oficial="De acuerdo a las normativas de CABA, los residuos deben depositarse de 19:00 a 21:00 hs de domingo a viernes en bolsas cerradas.",
            activo=True,
        ),
        FaqAprobadaModel(
            id="faq-4",
            consorcio_id=None,
            pregunta="¿Cómo enviar el comprobante de pago de expensas?",
            respuesta_oficial="El comprobante de transferencia bancaria debe remitirse por email a la casilla de cobranzas correspondiente, indicando consorcio y número de unidad funcional.",
            activo=True,
        ),
    ]
    db.add_all(faqs)

    # 6. Etiquetas Iniciales
    etiquetas = [
        EtiquetaModel(id="lbl-1", titulo="URGENTE", color="#DC2626", descripcion="Incidencias edilicias críticas o emergencias"),
        EtiquetaModel(id="lbl-2", titulo="EXPENSAS", color="#2563EB", descripcion="Consultas de pagos y cobranzas"),
        EtiquetaModel(id="lbl-3", titulo="MUDANZA", color="#D97706", descripcion="Coordinación y permisos de mudanza"),
        EtiquetaModel(id="lbl-4", titulo="RECLAMO", color="#7C3AED", descripcion="Averías y mantenimiento general"),
        EtiquetaModel(id="lbl-5", titulo="RESUELTO", color="#16A34A", descripcion="Casos resueltos satisfactoriamente"),
    ]
    db.add_all(etiquetas)

    # 7. Conversaciones y Mensajes Iniciales
    c_conv1 = ConversacionModel(
        id="conv-1",
        contacto_id="cont-1",
        consorcio_id="cons-corrientes-lavalle",
        estado=EstadoConversacion.OPEN,
        bot_activo=True,
        etiquetas=["RECLAMO"],
    )
    c_conv2 = ConversacionModel(
        id="conv-2",
        contacto_id="cont-2",
        consorcio_id="cons-callao-2334",
        estado=EstadoConversacion.OPEN,
        bot_activo=True,
        etiquetas=["EXPENSAS"],
    )
    c_conv3 = ConversacionModel(
        id="conv-3",
        contacto_id="cont-3",
        consorcio_id="cons-corrientes-lavalle",
        estado=EstadoConversacion.OPEN,
        bot_activo=False,
        etiquetas=["URGENTE"],
    )
    db.add_all([c_conv1, c_conv2, c_conv3])
    await db.flush()

    m1 = MensajeModel(
        id="msg-init-1",
        conversacion_id="conv-1",
        tipo=TipoMensaje.INCOMING,
        contenido="Hola, se cortó la luz en el palier del piso 4 de Torre Corrientes. ¿Podrán mandar a alguien a revisar?",
        enviado_por=EnviadoPor.VECINO,
        leido=True,
    )
    m2 = MensajeModel(
        id="msg-init-2",
        conversacion_id="conv-1",
        tipo=TipoMensaje.OUTGOING,
        contenido="Buenas tardes Carlos. Hemos registrado el aviso bajo el Ticket #TICK-1042. El electricista de guardia ya fue notificado para verificar la térmica del palier.",
        enviado_por=EnviadoPor.BOT,
        leido=True,
    )
    m3 = MensajeModel(
        id="msg-init-3",
        conversacion_id="conv-2",
        tipo=TipoMensaje.INCOMING,
        contenido="Hola buen día, ¿me podrían pasar el CBU y alias para transferir las expensas de este mes de la unidad 7A?",
        enviado_por=EnviadoPor.VECINO,
        leido=False,
    )
    m4 = MensajeModel(
        id="msg-init-4",
        conversacion_id="conv-2",
        tipo=TipoMensaje.OUTGOING,
        contenido="Hola Lucía. Para Consorcio Callao 2334 los datos bancarios son:\n\n• CBU: 0140000000000000000002\n• Alias: CALLAO.2334.EXPENSAS\n• CUIT: 30-71998877-6\n\nPor favor remití el comprobante a callao2334@selizadministraciones.com.ar indicando tu unidad (7° A).",
        enviado_por=EnviadoPor.BOT,
        leido=True,
    )
    m5 = MensajeModel(
        id="msg-init-5",
        conversacion_id="conv-3",
        tipo=TipoMensaje.INCOMING,
        contenido="Urgente, hay dos personas atrapadas en el ascensor principal de Torre Lavalle!",
        enviado_por=EnviadoPor.VECINO,
        leido=True,
    )
    m6 = MensajeModel(
        id="msg-init-6",
        conversacion_id="conv-3",
        tipo=TipoMensaje.OUTGOING,
        contenido="EMERGENCIA DETECTADA. Ya se comunicó a la guardia técnica de ascensores (+54 9 11 4444-1111). Bomberos CABA: 100. Un operador humano está monitoreando esta conversación.",
        enviado_por=EnviadoPor.BOT,
        leido=True,
    )
    m7 = MensajeModel(
        id="msg-init-7",
        conversacion_id="conv-3",
        tipo=TipoMensaje.ACTIVITY,
        contenido="📋 Ticket registrado automáticamente #tick-1040 [Expediente #EXP-2026-0001]. Escalado a prioridad CRÍTICA.",
        enviado_por=EnviadoPor.BOT,
        privado=True,
        leido=True,
    )
    db.add_all([m1, m2, m3, m4, m5, m6, m7])

    await db.commit()
    logger.info("[DB_SEED] Sembrado inicial completado con éxito.")
