import json
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from core.models import Conversacion
from core.services.agente_service import procesar_mensaje


@login_required
def chat_view(request):
    """
    Muestra la página principal del chat de ARIA.
    Carga el historial de conversación anterior del usuario.
    """
    # Cargamos el historial de los últimos 20 mensajes de la conversación
    historial = Conversacion.objects.filter(usuario=request.user).order_by('-fecha')[:20]
    # Los invertimos para que queden en orden cronológico correcto
    historial = reversed(historial)

    return render(request, 'core/chat.html', {
        'historial_chat': historial
    })


@login_required
def aria_responder(request):
    """
    Recibe el mensaje del usuario, recupera el historial de chat de la BD
    y procesa la solicitud a través del agente.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Solo se aceptan peticiones POST'}, status=405)

    try:
        datos = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Formato de datos inválido'}, status=400)

    mensaje_usuario = datos.get('mensaje', '').strip()

    if not mensaje_usuario:
        return JsonResponse({'error': 'El mensaje no puede estar vacío'}, status=400)

    # Recuperamos el historial de mensajes de la conversación para pasarlo como contexto al LLM
    # Formateamos en la estructura esperada por la API de Groq
    conversaciones_anteriores = Conversacion.objects.filter(usuario=request.user).order_by('-fecha')[:10]
    historial_contexto = []
    
    for conv in reversed(conversaciones_anteriores):
        rol_groq = "assistant" if conv.rol == 'aria' else "user"
        historial_contexto.append({"role": rol_groq, "content": conv.mensaje})

    # Procesar el mensaje con nuestro Agente
    respuesta_agente = procesar_mensaje(request.user, mensaje_usuario, historial_contexto)

    return JsonResponse({'respuesta': respuesta_agente})
