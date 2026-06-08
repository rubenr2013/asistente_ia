from django.urls import path
from . import views

urlpatterns = [
    # Inicia el flujo de autenticación de Gmail
    path('gmail/conectar/', views.conectar_gmail, name='conectar_gmail'),
    
    # Callback de retorno de Google OAuth
    path('gmail/callback/', views.callback_gmail, name='callback_gmail'),
    
    # Desvincular una cuenta
    path('gmail/desconectar/<int:cuenta_id>/', views.desconectar_gmail, name='desconectar_gmail'),
    
    # Seleccionar cuenta activa para ARIA
    path('gmail/seleccionar/<int:cuenta_id>/', views.seleccionar_cuenta, name='seleccionar_cuenta'),
]
