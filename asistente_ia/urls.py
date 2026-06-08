"""
URL configuration for asistente_ia project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    # Gestión de sesiones y usuarios (login/logout)
    path('', include('usuarios.urls')),

    # Gestión de cuentas de correo Gmail y sincronizaciones
    path('', include('correo.urls')),

    # Todas las URLs de la app core (chat + API de ARIA)
    path('', include('core.urls')),
]
