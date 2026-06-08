import os
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from django.conf import settings
from .models import CuentaGmail
from .services.gmail_service import SCOPES, CREDENTIALS_PATH, obtener_servicio_gmail, sincronizar_correos_cuenta

# Helper to get redirect URI
def obtener_redirect_uri(request):
    """
    Construye la URI de callback de Google OAuth de forma dinámica
    para que funcione tanto en desarrollo (localhost) como en producción (Render).
    """
    protocolo = 'https' if request.is_secure() else 'http'
    host = request.get_host()
    return f"{protocolo}://{host}/gmail/callback/"


@login_required
def conectar_gmail(request):
    """
    Inicia el flujo de autenticación de Google OAuth.
    Redirige al usuario al consentimiento de Google.
    """
    redirect_uri = obtener_redirect_uri(request)
    
    # Creamos el flujo de autenticación
    flow = Flow.from_client_secrets_file(
        CREDENTIALS_PATH,
        scopes=SCOPES,
        redirect_uri=redirect_uri
    )
    
    # Genera la URL de autorización
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )
    
    # Guardamos el estado (state) en la sesión del usuario para validación de seguridad posterior
    request.session['oauth_state'] = state
    
    return redirect(authorization_url)


@login_required
def callback_gmail(request):
    """
    Callback al que Google redirige después del consentimiento del usuario.
    Obtiene los tokens y los guarda en CuentaGmail.
    """
    state = request.session.get('oauth_state')
    if not state or request.GET.get('state') != state:
        return HttpResponseBadRequest("Estado de OAuth inválido (posible ataque CSRF).")

    redirect_uri = obtener_redirect_uri(request)
    
    flow = Flow.from_client_secrets_file(
        CREDENTIALS_PATH,
        scopes=SCOPES,
        redirect_uri=redirect_uri,
        state=state
    )

    # Obtenemos el token de acceso
    authorization_response = request.build_absolute_uri()
    # Solución alternativa si HTTPS no está configurado localmente
    if 'http://' in authorization_response and not settings.DEBUG:
        authorization_response = authorization_response.replace('http://', 'https://')
        
    flow.fetch_token(authorization_response=authorization_response)
    creds = flow.credentials

    # Usamos las credenciales para averiguar a qué correo pertenecen
    servicio_temporal = build('gmail', 'v1', credentials=creds)
    perfil = servicio_temporal.users().getProfile(userId='me').execute()
    email_vinculado = perfil.get('emailAddress')

    if not email_vinculado:
        return HttpResponseBadRequest("No se pudo obtener el correo de la cuenta de Google.")

    # Guardamos o actualizamos la cuenta de Gmail en la base de datos
    cuenta, creada = CuentaGmail.objects.update_or_create(
        usuario=request.user,
        email=email_vinculado,
        defaults={
            'token_json': creds.to_json(),
            'activa': True  # Activamos por defecto la última conectada
        }
    )

    # Desactivamos las otras cuentas para que esta sea la activa principal por defecto
    if creada:
        CuentaGmail.objects.filter(usuario=request.user).exclude(id=cuenta.id).update(activa=False)

    # Sincronizamos los correos de la cuenta recién agregada
    sincronizar_correos_cuenta(cuenta)

    return redirect('chat')


@login_required
def desconectar_gmail(request, cuenta_id):
    """
    Desvincula una cuenta de correo eliminándola de la base de datos.
    """
    cuenta = CuentaGmail.objects.filter(usuario=request.user, id=cuenta_id).first()
    if cuenta:
        cuenta.delete()
    return redirect('chat')


@login_required
def seleccionar_cuenta(request, cuenta_id):
    """
    Cambia la cuenta de Gmail activa del usuario actual.
    """
    # Desactivar todas las cuentas del usuario
    CuentaGmail.objects.filter(usuario=request.user).update(activa=False)
    
    # Activar la cuenta seleccionada
    cuenta = CuentaGmail.objects.filter(usuario=request.user, id=cuenta_id).first()
    if cuenta:
        cuenta.activa = True
        cuenta.save()
        
        # Sincronizar correos de esta cuenta al seleccionarla
        sincronizar_correos_cuenta(cuenta)

    return redirect('chat')
