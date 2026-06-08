from django.db import models
from django.contrib.auth.models import User

class Nota(models.Model):
    """
    Representa una nota de texto del usuario (ideas, listas, recordatorios, gastos).
    ARIA puede crear y editar estas notas a petición del usuario.
    """
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notas')
    titulo = models.CharField(max_length=200)
    contenido = models.TextField(blank=True)
    categoria = models.CharField(max_length=50, blank=True, default='General')
    creada = models.DateTimeField(auto_now_add=True)
    actualizada = models.DateTimeField(auto_now=True)
    archivada = models.BooleanField(default=False)

    class Meta:
        ordering = ['-actualizada']
        verbose_name = 'Nota'
        verbose_name_plural = 'Notas'

    def __str__(self):
        return f"{self.titulo} (por {self.usuario.username})"
