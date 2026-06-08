from django.db import models
from django.contrib.auth.models import User


class CuentaGmail(models.Model):
    """
    Representa una cuenta de correo de Gmail vinculada por el usuario.
    El usuario único de ARIA puede registrar hasta 5 cuentas distintas.
    """
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cuentas_gmail')
    email = models.EmailField(unique=True)
    token_json = models.TextField()  # Contiene las credenciales de Google OAuth serializadas en JSON
    activa = models.BooleanField(default=True)  # Si es la cuenta que ARIA está leyendo por defecto
    creada_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Cuenta de Gmail'
        verbose_name_plural = 'Cuentas de Gmail'

    def __str__(self):
        estado = "Activa" if self.activa else "Inactiva"
        return f"{self.email} ({estado})"


class Correo(models.Model):
    """
    Copia local de los correos recibidos de Gmail para permitir
    procesamiento rápido, clasificación offline y resúmenes sin
    saturar la API de Gmail.
    """
    CATEGORIAS = [
        ('trabajo', 'Trabajo'),
        ('personal', 'Personal'),
        ('spam', 'Spam'),
        ('promociones', 'Promociones'),
        ('importante', 'Importante'),
        ('informativo', 'Informativo'),
    ]

    cuenta = models.ForeignKey(CuentaGmail, on_delete=models.CASCADE, related_name='correos', null=True, blank=True)
    gmail_id = models.CharField(max_length=200, unique=True)  # ID único retornado por Gmail
    remitente = models.CharField(max_length=300)
    asunto = models.CharField(max_length=500)
    fecha = models.DateTimeField(null=True, blank=True)  # Cambiado a DateTimeField para ordenación correcta
    cuerpo = models.TextField(blank=True)
    snippet = models.TextField(blank=True)  # Resumen corto que provee Gmail
    categoria = models.CharField(max_length=50, choices=CATEGORIAS, blank=True)
    resumen_ia = models.TextField(blank=True)  # Resumen corto generado por ARIA
    leido = models.BooleanField(default=False)
    eliminado = models.BooleanField(default=False)  # Mover a papelera local
    fecha_sincronizacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha']  # Ordenamos por la fecha del correo de más nuevo a más viejo
        verbose_name = 'Correo'
        verbose_name_plural = 'Correos'

    def __str__(self):
        return f"De: {self.remitente} | Asunto: {self.asunto[:30]}..."
