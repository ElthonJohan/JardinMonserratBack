from django.contrib.auth.models import AbstractUser
from django.db import models

class Usuario(AbstractUser):
    apoderado_rel = models.ForeignKey(
        'estudiantes.Apoderado',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='usuarios'
    )

    is_parent = models.BooleanField(default=False, verbose_name="Es Apoderado")
    first_login = models.BooleanField(default=True, verbose_name="Primer inicio de sesión")
    
    def __str__(self):
        return f"{self.username}"