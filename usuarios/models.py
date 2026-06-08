from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class PerfilUsuario(models.Model):
    """
    Guarda información complementaria del usuario.
    Junior developer: usamos una relación uno a uno sencilla.
    """
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Perfil de {self.usuario.username}"

# Señal para crear el perfil automáticamente cuando se crea un usuario
@receiver(post_save, sender=User)
def crear_perfil(sender, instance, created, **kwargs):
    if created:
        PerfilUsuario.objects.get_or_create(usuario=instance)
