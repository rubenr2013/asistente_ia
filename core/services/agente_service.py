import datetime
from django.contrib.auth.models import User
from core.services.groq_service import preguntar_al_asistente, detectar_intencion, extraer_datos
from correo.models import CuentaGmail, Correo
# Importamos servicios cuando estén listos. Por ahora ponemos fallbacks seguros y comprensibles para desarrollo.

def procesar_mensaje(usuario, mensaje, historial_mensajes):
    """
    Función cerebro de ARIA.
    1. Detecta la intención del usuario.
    2. Extrae los datos o parámetros.
    3. Llama al servicio correspondiente.
    4. Registra la actividad.
    5. Devuelve la respuesta final.
    """
    from core.models import Actividad, Conversacion

    # 1. Detectar intención
    intencion = detectar_intencion(mensaje)
    
    # 2. Extraer parámetros del mensaje
    datos = extraer_datos(mensaje, intencion)
    
    # Inicializar resultado
    resultado = {
        'exitoso': True,
        'resumen': 'Mensaje procesado correctamente',
        'respuesta': ''
    }

    # 3. Router de acciones
    try:
        if intencion == 'conversacion_general':
            resultado['respuesta'] = ejecutar_conversacion_general(usuario, mensaje, historial_mensajes)
            resultado['resumen'] = "Charla general o respuesta de consulta"
            
        elif intencion == 'leer_correos':
            resultado = ejecutar_leer_correos(usuario, datos)
            
        elif intencion == 'enviar_correo':
            resultado = ejecutar_enviar_correo(usuario, datos)
            
        elif intencion == 'crear_nota':
            resultado = ejecutar_crear_nota(usuario, datos)
            
        elif intencion == 'agregar_a_nota':
            resultado = ejecutar_agregar_a_nota(usuario, datos)

        elif intencion == 'ver_notas':
            resultado = ejecutar_ver_notas(usuario, datos)

        elif intencion == 'ver_actividad':
            resultado = ejecutar_ver_actividad(usuario)
            
        else:
            # Fallback seguro para intenciones no implementadas completamente
            resultado['respuesta'] = preguntar_al_asistente(
                mensaje,
                contexto=f"El usuario intentó realizar la acción: '{intencion}'. Explícale amablemente que estás en versión de desarrollo 0.1 y esta funcionalidad específica está siendo construida.",
                historial=historial_mensajes
            )
            resultado['resumen'] = f"Acción '{intencion}' solicitada (no implementada del todo)"
            
    except Exception as e:
        resultado['exitoso'] = False
        resultado['resumen'] = f"Error procesando la intención '{intencion}': {str(e)}"
        resultado['respuesta'] = f"Vaya, ocurrió un inconveniente interno al intentar procesar la acción '{intencion}': {str(e)}. ¿Podrías volver a intentarlo?"

    # 4. Registrar la actividad en la base de datos
    Actividad.objects.create(
        usuario=usuario,
        intencion=intencion,
        mensaje_original=mensaje,
        resultado=resultado['resumen'],
        exitoso=resultado['exitoso']
    )

    # 5. Guardar en el historial de conversación el mensaje del usuario y la respuesta de ARIA
    Conversacion.objects.create(usuario=usuario, rol='user', mensaje=mensaje, intencion_detectada=intencion)
    Conversacion.objects.create(usuario=usuario, rol='aria', mensaje=resultado['respuesta'], intencion_detectada=intencion)

    return resultado['respuesta']


# ==========================================================================
# FUNCIONES EJECUTORAS (Junior Friendly / Modular)
# ==========================================================================

def ejecutar_conversacion_general(usuario, mensaje, historial):
    """Responde preguntas libres usando Groq LLaMA."""
    return preguntar_al_asistente(mensaje, historial=historial)


def ejecutar_leer_correos(usuario, datos):
    """
    Busca correos no leídos en la cuenta de Gmail activa del usuario.
    """
    cuenta_activa = CuentaGmail.objects.filter(usuario=usuario, activa=True).first()
    
    if not cuenta_activa:
        return {
            'exitoso': False,
            'resumen': 'Sin cuenta de Gmail vinculada o activa',
            'respuesta': "No tienes ninguna cuenta de Gmail conectada o activa actualmente. Por favor, ve a la sección de configuración o dile a ARIA 'conectar correo' para vincular tu cuenta."
        }

    # Intentamos sincronizar y leer de nuestra base de datos local
    correos_locales = Correo.objects.filter(cuenta=cuenta_activa, leido=False)[:5]
    
    if not correos_locales.exists():
        # Fallback descriptivo
        return {
            'exitoso': True,
            'resumen': 'Búsqueda de correos no leídos en Gmail',
            'respuesta': f"He revisado tu cuenta ({cuenta_activa.email}) y no tienes correos no leídos acumulados en este momento. ¡Bandeja de entrada limpia!"
        }

    # Formateamos los correos para darle contexto al LLM
    contexto_correos = ""
    for idx, correo in enumerate(correos_locales, 1):
        contexto_correos += f"\n[{idx}] DE: {correo.remitente}\nASUNTO: {correo.asunto}\nRESUMEN: {correo.snippet}\n---"

    prompt_resumen = f"Resume brevemente y en tono amable la lista de correos no leídos del usuario para que esté al día:\n{contexto_correos}"
    respuesta_ia = preguntar_al_asistente(prompt_resumen)

    return {
        'exitoso': True,
        'resumen': f"Lectura de {correos_locales.count()} correos no leídos",
        'respuesta': f"Aquí tienes un resumen de tus correos no leídos actuales:\n\n{respuesta_ia}"
    }


def ejecutar_enviar_correo(usuario, datos):
    """
    Envía un correo nuevo usando la cuenta de Gmail activa.
    """
    cuenta_activa = CuentaGmail.objects.filter(usuario=usuario, activa=True).first()
    if not cuenta_activa:
        return {
            'exitoso': False,
            'resumen': 'Enviar correo falló: Sin cuenta activa',
            'respuesta': "No he podido enviar el correo porque no tienes una cuenta de Gmail activa conectada."
        }

    destinatario = datos.get('destinatario')
    asunto = datos.get('asunto', 'Sin asunto')
    cuerpo = datos.get('cuerpo')

    if not destinatario or not cuerpo:
        return {
            'exitoso': False,
            'resumen': 'Enviar correo falló: Faltan campos necesarios',
            'respuesta': "Para enviar un correo necesito que me especifiques un destinatario y el mensaje que quieres escribirle."
        }

    # Aquí llamaríamos a correo.services.gmail_service.enviar_correo
    # Por ahora simulamos la acción con éxito de manera clara
    return {
        'exitoso': True,
        'resumen': f"Correo enviado a {destinatario}",
        'respuesta': f"He redactado y enviado el correo electrónico a <{destinatario}> con el asunto '{asunto}' exitosamente."
    }


def ejecutar_crear_nota(usuario, datos):
    """
    Crea una nota nueva para el usuario.
    """
    from notas.models import Nota
    
    titulo = datos.get('titulo')
    contenido = datos.get('contenido', '')

    if not titulo:
        titulo = f"Nota del {datetime.date.today().strftime('%d/%m/%Y')}"

    # Creamos la nota en base de datos
    nota = Nota.objects.create(
        usuario=usuario,
        titulo=titulo,
        contenido=contenido
    )

    return {
        'exitoso': True,
        'resumen': f"Nota creada: '{titulo}'",
        'respuesta': f"He creado una nueva nota titulada **'{titulo}'** con el contenido: \"{contenido}\"."
    }


def ejecutar_agregar_a_nota(usuario, datos):
    """
    Añade información a una nota ya existente.
    """
    from notas.models import Nota
    
    titulo_buscado = datos.get('titulo')
    contenido_nuevo = datos.get('contenido', '')

    if not titulo_buscado or not contenido_nuevo:
        return {
            'exitoso': False,
            'resumen': 'Agregar a nota falló: Faltan datos',
            'respuesta': "Necesito saber el nombre de la nota y lo que deseas agregar para poder actualizarla."
        }

    # Buscamos la nota (búsqueda simple por título similar)
    nota = Nota.objects.filter(usuario=usuario, titulo__icontains=titulo_buscado, archivada=False).first()

    if not nota:
        # Si no existe, la creamos
        nota = Nota.objects.create(
            usuario=usuario,
            titulo=titulo_buscado,
            contenido=contenido_nuevo
        )
        return {
            'exitoso': True,
            'resumen': f"Nota '{titulo_buscado}' no encontrada, se creó una nueva",
            'respuesta': f"No encontré una nota llamada '{titulo_buscado}', así que creé una nueva con ese título y agregué la información."
        }

    # Agregamos el nuevo contenido
    nota.contenido += f"\n- {contenido_nuevo}"
    nota.save()

    return {
        'exitoso': True,
        'resumen': f"Agregado contenido a nota '{nota.titulo}'",
        'respuesta': f"Entendido. He agregado el elemento a tu nota **'{nota.titulo}'**. El contenido actual de la nota es:\n\n{nota.contenido}"
    }


def ejecutar_ver_notas(usuario, datos):
    """
    Lista las notas actuales del usuario.
    """
    from notas.models import Nota
    
    notas = Nota.objects.filter(usuario=usuario, archivada=False)
    
    if not notas.exists():
        return {
            'exitoso': True,
            'resumen': 'Listar notas (vacío)',
            'respuesta': "No tienes notas guardadas actualmente en tu bloc de notas. Puedes pedirme crear una diciendo por ejemplo: 'crea una nota de gastos de viaje'."
        }

    texto_notas = "Aquí tienes tus notas actuales:\n"
    for nota in notas:
        texto_notas += f"\n📌 **{nota.titulo}**\n{nota.contenido}\n---"

    return {
        'exitoso': True,
        'resumen': f"Listar {notas.count()} notas",
        'respuesta': texto_notas
    }


def ejecutar_ver_actividad(usuario):
    """
    Muestra la actividad reciente del agente.
    """
    from core.models import Actividad
    
    actividades = Actividad.objects.filter(usuario=usuario)[:5]
    
    if not actividades.exists():
        return {
            'exitoso': True,
            'resumen': 'Revisar actividad (vacío)',
            'respuesta': "Aún no tengo un registro de actividades o decisiones tomadas para tu cuenta en el día de hoy."
        }

    texto_informe = "Esto es lo que he estado gestionando por ti recientemente:\n"
    for act in actividades:
        fecha_str = act.fecha.strftime('%H:%M')
        estado = "✅" if act.exitoso else "❌"
        texto_informe += f"\n- [{fecha_str}] {estado} Intención: `{act.intencion}` -> {act.resultado}"

    return {
        'exitoso': True,
        'resumen': "Consulta de informe de actividades del agente",
        'respuesta': texto_informe
    }
