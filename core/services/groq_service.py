import json
from groq import Groq
from django.conf import settings

# Creamos el cliente de Groq con nuestra API key
cliente = Groq(api_key=settings.GROQ_API_KEY)


def preguntar_al_asistente(mensaje, contexto="", historial=""):
    """
    Función principal para hablar con el asistente de forma general.
    - mensaje: lo que el usuario pregunta o pide.
    - contexto: información adicional relevante (ej: notas actuales, correos).
    - historial: mensajes anteriores para dar continuidad.
    """
    sistema = """
    Eres un asistente personal inteligente llamado ARIA 
    (Asistente de Respuesta Inteligente Automatizada).
    
    Tu trabajo es:
    - Ayudar a gestionar correos electrónicos
    - Clasificar información importante
    - Crear resúmenes y reportes
    - Gestionar notas y recordatorios
    
    Siempre respondes en español, de forma clara, concisa y profesional.
    """

    if contexto:
        sistema += f"\n\nContexto actual del usuario:\n{contexto}"

    messages = [{"role": "system", "content": sistema}]

    # Si hay historial de chat, lo agregamos para dar memoria a ARIA
    if historial:
        messages.extend(historial)

    messages.append({"role": "user", "content": mensaje})

    try:
        respuesta = cliente.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.7,
            max_tokens=1024
        )
        return respuesta.choices[0].message.content
    except Exception as e:
        return f"Lo siento, he tenido un problema de conexión con mi cerebro artificial. Error: {str(e)}"


def clasificar_texto(texto, categorias):
    """
    Clasifica un texto dentro de una lista de categorías dadas.
    """
    mensaje = f"""
    Clasifica el siguiente texto en UNA de estas categorías: {', '.join(categorias)}
    
    Texto:
    {texto}
    
    Responde ÚNICAMENTE con el nombre de la categoría, sin explicaciones, puntos ni palabras adicionales.
    """

    try:
        respuesta = cliente.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": mensaje}],
            temperature=0.1,
            max_tokens=50
        )
        return respuesta.choices[0].message.content.strip()
    except Exception:
        return categorias[0]  # Fallback a la primera categoría si hay error


def detectar_intencion(mensaje):
    """
    Analiza el mensaje del usuario para clasificar su intención en una de las acciones conocidas.
    """
    instrucciones = """
    Analiza el mensaje del usuario y clasifícalo en una de las siguientes intenciones posibles.
    Debes responder ÚNICAMENTE con el nombre clave de la intención (ej: leer_correos), sin texto adicional ni explicaciones.

    Intenciones posibles:
    - leer_correos (cuando pide leer, ver, consultar o listar la bandeja de entrada o correos no leídos)
    - clasificar_correos (organizar, clasificar o etiquetar los correos recibidos)
    - responder_correo (redactar o enviar una respuesta a un correo específico)
    - eliminar_spam (buscar correos spam y eliminarlos o limpiar la bandeja)
    - enviar_correo (enviar o redactar un correo nuevo a alguien)
    - buscar_correo (buscar correos por asunto, remitente o palabra clave)
    - crear_nota (crear una nota, recordatorio de texto o apunte nuevo)
    - agregar_a_nota (añadir información, gastos o datos a una nota existente)
    - ver_notas (mostrar, listar o ver las notas guardadas)
    - editar_nota (modificar o actualizar una nota completa)
    - crear_recordatorio (crear un evento, cita o recordatorio en el calendario)
    - ver_recordatorios (ver los próximos eventos o recordatorios en el calendario)
    - ver_actividad (ver qué ha hecho ARIA hoy, revisar el log o el informe de decisiones)
    - cambiar_cuenta_gmail (cambiar a otra cuenta de Gmail o configurar correos)
    - conversacion_general (si solo saluda, conversa o hace preguntas de conocimiento general que no requieren ejecutar acciones de correo, calendario o notas)

    Mensaje del usuario:
    """

    try:
        respuesta = cliente.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": instrucciones},
                {"role": "user", "content": mensaje}
            ],
            temperature=0.1,
            max_tokens=20
        )
        return respuesta.choices[0].message.content.strip().lower()
    except Exception:
        return 'conversacion_general'


def extraer_datos(mensaje, intencion):
    """
    Usa el LLM para extraer entidades importantes en formato JSON según la intención.
    Junior friendly: devolvemos un diccionario Python interpretado desde JSON.
    """
    if intencion == 'conversacion_general' or intencion == 'ver_notas' or intencion == 'ver_recordatorios' or intencion == 'ver_actividad':
        return {}

    prompt = f"""
    Dado el siguiente mensaje y su intención clasificada como '{intencion}', extrae los datos necesarios en formato JSON plano.
    Devuelve ÚNICAMENTE el JSON y nada más. Si un campo no se encuentra en el mensaje, devuélvelo como null o vacío.

    Esquemas de JSON esperados por intención:
    
    - Para 'enviar_correo':
      {{"destinatario": "correo@ejemplo.com", "asunto": "Asunto del correo", "cuerpo": "Contenido del correo"}}
    
    - Para 'responder_correo':
      {{"correo_id": "id_del_correo_si_se_menciona", "instrucciones": "ej: dile que acepto el trato de forma formal"}}
    
    - Para 'buscar_correo':
      {{"termino": "termino de busqueda (ej: factura, juan)"}}

    - Para 'crear_nota':
      {{"titulo": "Título de la nota (ej: gastos de viaje)", "contenido": "Contenido inicial"}}

    - Para 'agregar_a_nota':
      {{"titulo": "Título de la nota a la que quiere agregar", "contenido": "ej: $50 para taxi"}}

    - Para 'crear_recordatorio':
      {{"titulo": "Título de la cita", "fecha_hora": "Fecha y hora en formato YYYY-MM-DD HH:MM:SS", "descripcion": "Detalles"}}

    Mensaje: "{mensaje}"
    """

    try:
        respuesta = cliente.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=300
        )
        cleaned_response = respuesta.choices[0].message.content.strip()
        # Intentamos parsear JSON
        # A veces el LLM agrega bloques de código ```json ... ```, los limpiamos
        if cleaned_response.startswith("```"):
            cleaned_response = cleaned_response.split("```")[1]
            if cleaned_response.startswith("json"):
                cleaned_response = cleaned_response[4:]
        
        return json.loads(cleaned_response.strip())
    except Exception:
        return {}
