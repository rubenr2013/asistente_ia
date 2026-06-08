from django.urls import path
from . import views

urlpatterns = [
    # Ruta para iniciar sesión — /login/
    path('login/', views.login_view, name='login'),
    
    # Ruta para cerrar sesión — /logout/
    path('logout/', views.logout_view, name='logout'),
]
