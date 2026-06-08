from django.urls import path
from core import views

urlpatterns = [
    # Página principal del chat — entra a http://localhost:8000/
    path('', views.chat_view, name='chat'),

    # Endpoint que recibe mensajes y devuelve respuesta de ARIA
    # El JavaScript del chat llama a esta URL con fetch()
    path('aria/responder/', views.aria_responder, name='aria_responder'),
]
