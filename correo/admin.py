from django.contrib import admin
from .models import CuentaGmail, Correo


@admin.register(CuentaGmail)
class CuentaGmailAdmin(admin.ModelAdmin):
    list_display = ['email', 'usuario', 'activa', 'creada_en']
    list_filter = ['activa']
    search_fields = ['email']


@admin.register(Correo)
class CorreoAdmin(admin.ModelAdmin):
    list_display = ['cuenta', 'remitente', 'asunto', 'categoria', 'leido', 'fecha']
    list_filter = ['cuenta', 'categoria', 'leido', 'eliminado']
    search_fields = ['remitente', 'asunto', 'cuerpo']
