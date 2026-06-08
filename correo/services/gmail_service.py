import os
import json
import base64
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from django.conf import settings
from django.utils import timezone
from core.services.groq_service import preguntar_al_asistente, clasificar_texto
from correo.models import CuentaGmail, Correo
from datetime import datetime

# Permisos requeridos para Gmail
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.modify'
]

CREDENTIALS_PATH = os.path.join(settings.BASE_DIR, 'credentials.json')


def obtener_servicio_gmail(cuenta_gmail):
    """
    Crea y retorna un servicio de la API de Gmail para la cuenta especificada.
    Refresca el token si ha expirado.
    """
    token_data = json.loads(cuenta_gmail.token_json)
    creds = Credentials.from_authorized_user_info(token_data, SCOPES)

    # Si el token expiró, lo refrescamos usando el refresh_token
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            # Guardamos el token actualizado en la base de datos
            cuenta_gmail.token_json = creds.to_json()
            cuenta_gmail.save()
        except Exception as e:
            print(f"Error al refrescar credenciales de Google: {str(e)}")

    return build('gmail', 'v1', credentials=creds)


def sincronizar_correos_cuenta(cuenta_gmail, cantidad=15):
    """
    Sincroniza los correos no leídos más recientes de Gmail
    y los guarda localmente en PostgreSQL.
    """
    try:
        servicio = obtener_servicio_gmail(cuenta_gmail)
        # Buscar correos no leídos
        resultado = servicio.users().messages().list(
            userId='me',
            q='is:unread in:inbox',
            maxResults=cantidad
        ).execute()

        mensajes = resultado.get('messages', [])
        correos_sincronizados = 0

        for msg in mensajes:
            # Si ya existe localmente, no lo volvemos a descargar
            if Correo.objects.filter(gmail_id=msg['id']).exists():
                continue

            # Traemos el detalle completo
            detalle = servicio.users().messages().get(
                userId='me',
                id=msg['id'],
                format='full'
            ).execute()

            # Parsear el correo
            datos = extraer_datos_correo(detalle)

            # Convertir fecha de texto a objeto timezone
            # Ejemplo de fecha de Gmail: "Mon, 8 Jun 2026 10:15:30 +0000"
            fecha_correo = parse_fecha_gmail(datos['fecha'])

            # Crear el correo localmente
            correo_obj = Correo.objects.create(
                cuenta=cuenta_gmail,
                gmail_id=datos['id'],
                remitente=datos['remitente'],
                asunto=datos['asunto'],
                fecha=fecha_correo,
                cuerpo=datos['cuerpo'],
                snippet=datos['snippet'],
                leido=False
            )

            # Clasificar y resumir con ARIA en segundo plano/secuencial
            correo_obj.categoria = clasificar_correo(correo_obj)
            correo_obj.resumen_ia = resumir_correo(correo_obj)
            correo_obj.save()

            correos_sincronizados += 1

        return {
            'exitoso': True,
            'mensaje': f"Sincronizados {correos_sincronizados} correos nuevos para {cuenta_gmail.email}."
        }
    except Exception as e:
        return {
            'exitoso': False,
            'mensaje': f"Fallo en la sincronización de correos: {str(e)}"
        }


def parse_fecha_gmail(fecha_str):
    """
    Intenta parsear la fecha que retorna el header de Gmail a datetime.
    Si falla, retorna la fecha y hora actual con zona horaria.
    """
    if not fecha_str:
        return timezone.now()
    
    # Limpieza básica de la fecha
    # A veces viene con detalles adicionales al final, ej: " (UTC)"
    if "(" in fecha_str:
        fecha_str = fecha_str.split("(")[0].strip()

    formatos = [
        '%a, %d %b %Y %H:%M:%S %z',
        '%a, %d %b %Y %H:%M:%S %Z',
        '%d %b %Y %H:%M:%S %z',
        '%a, %d %b %Y %H:%M %z'
    ]

    for formato in formatos:
        try:
            return datetime.strptime(fecha_str.strip(), formato)
        except Exception:
            continue
            
    return timezone.now()


def extraer_datos_correo(detalle):
    """
    Extrae remitente, asunto, fecha y cuerpo del payload complejo de Gmail.
    """
    headers = detalle['payload']['headers']
    remitente = ''
    asunto = ''
    fecha = ''

    for h in headers:
        if h['name'] == 'From':
            remitente = h['value']
        elif h['name'] == 'Subject':
            asunto = h['value']
        elif h['name'] == 'Date':
            fecha = h['value']

    cuerpo = extraer_cuerpo(detalle['payload'])

    return {
        'id': detalle['id'],
        'remitente': remitente,
        'asunto': asunto,
        'fecha': fecha,
        'cuerpo': cuerpo[:1000],  # Guardamos los primeros 1000 caracteres
        'snippet': detalle.get('snippet', '')
    }


def extraer_cuerpo(payload):
    """
    Recorre de forma recursiva el payload del correo de Gmail buscando texto plano.
    """
    cuerpo = ''
    if 'parts' in payload:
        for parte in payload['parts']:
            if parte['mimeType'] == 'text/plain':
                data = parte['body'].get('data', '')
                if data:
                    cuerpo = base64.urlsafe_b64decode(data).decode('utf-8')
                    break
            elif 'parts' in parte:
                cuerpo = extraer_cuerpo(parte)
                if cuerpo:
                    break
    else:
        data = payload['body'].get('data', '')
        if data:
            cuerpo = base64.urlsafe_b64decode(data).decode('utf-8')

    return cuerpo


def clasificar_correo(correo):
    """
    Usa ARIA para clasificar el correo en categorías basadas en el asunto y snippet.
    """
    categorias = ['Trabajo', 'Personal', 'Spam', 'Promociones', 'Importante', 'Informativo']
    texto = f"Asunto: {correo.asunto}\nRemitente: {correo.remitente}\nContenido: {correo.snippet}"
    return clasificar_texto(texto, categorias).lower()


def resumir_correo(correo):
    """
    Usa ARIA para hacer un resumen corto de 2 líneas de este correo.
    """
    contexto = f"Remitente: {correo.remitente}\nAsunto: {correo.asunto}\nContenido: {correo.cuerpo}"
    resumen = preguntar_al_asistente(
        "Haz un resumen de máximo 2 líneas de este correo. Solo el resumen, sin preámbulos.",
        contexto=contexto
    )
    return resumen


def enviar_correo(cuenta_gmail, destinatario, asunto, cuerpo):
    """
    Envía un correo electrónico desde la cuenta vinculada del usuario.
    """
    servicio = obtener_servicio_gmail(cuenta_gmail)

    mensaje = MIMEMultipart()
    mensaje['to'] = destinatario
    mensaje['subject'] = asunto
    mensaje.attach(MIMEText(cuerpo, 'plain'))

    raw = base64.urlsafe_b64encode(mensaje.as_bytes()).decode()

    servicio.users().messages().send(
        userId='me',
        body={'raw': raw}
    ).execute()

    return f"Correo enviado correctamente a {destinatario}"


def marcar_como_leido(cuenta_gmail, gmail_id):
    """
    Quita la etiqueta UNREAD del correo en los servidores de Gmail.
    """
    servicio = obtener_servicio_gmail(cuenta_gmail)
    servicio.users().messages().modify(
        userId='me',
        id=gmail_id,
        body={'removeLabelIds': ['UNREAD']}
    ).execute()


def eliminar_correo(cuenta_gmail, gmail_id):
    """
    Mueve un correo a la papelera (trash) en Gmail.
    """
    servicio = obtener_servicio_gmail(cuenta_gmail)
    servicio.users().messages().trash(
        userId='me',
        id=gmail_id
    ).execute()
