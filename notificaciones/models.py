from django.db import models

class Notificacion(models.Model):
    TIPO_CHOICES = [
    ('PAGO_REGISTRADO', 'Pago Registrado'),
    ('PAGO_APROBADO', 'Pago Aprobado'),
    ('PAGO_RECHAZADO', 'Pago Rechazado'),
    ('SISTEMA', 'Alerta de Sistema'),
]

    usuario = models.ForeignKey('usuarios.Usuario', on_delete=models.CASCADE, related_name='notificaciones')
    alumno = models.ForeignKey('estudiantes.Estudiante', on_delete=models.CASCADE, null=True, blank=True)
    titulo = models.CharField(max_length=200)
    mensaje = models.TextField()
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES, default='SISTEMA')
    # NUEVO
    ruta = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )
    leido = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha_creacion']

    def __str__(self):
        estado = "Leída" if self.leido else "No Leída"
        return f"[{self.tipo}] {self.titulo} - {self.usuario} ({estado})"
