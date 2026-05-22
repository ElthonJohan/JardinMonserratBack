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

    def __str__(self):
        return f"{self.username}"