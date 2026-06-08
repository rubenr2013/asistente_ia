from django.db import models
from django.contrib.auth.models import User

class Conversacion(models.Model):
    """
    Guarda el historial de mensajes de la conversación entre el usuario y ARIA.
    Permite que ARIA mantenga la memoria de los mensajes previos.
    """
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversaciones')
    rol = models.CharField(max_length=20)  # 'user' (usuario) o 'aria' (asistente)
    mensaje = models.TextField()
    intencion_detectada = models.CharField(max_length=50, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['fecha']
        verbose_name = 'Mensaje de Conversación'
        verbose_name_plural = 'Mensajes de Conversación'

    def __str__(self):
        return f"{self.rol.upper()} a las {self.fecha.strftime('%H:%M:%S')}: {self.mensaje[:30]}..."


class Actividad(models.Model):
    """
    Log o registro de acciones que el agente ARIA ejecuta por el usuario.
    Permite al usuario auditar y ver los informes de decisiones de ARIA.
    """
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='actividades')
    intencion = models.CharField(max_length=50)
    mensaje_original = models.TextField()
    resultado = models.TextField()
    exitoso = models.BooleanField(default=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha']
        verbose_name = 'Registro de Actividad'
        verbose_name_plural = 'Registros de Actividad'

    def __str__(self):
        estado = "OK" if self.exitoso else "ERROR"
        return f"[{estado}] {self.intencion} - {self.fecha.strftime('%d/%m/%Y %H:%M')}"
