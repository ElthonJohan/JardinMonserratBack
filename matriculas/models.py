from django.db import models



class PeriodoAcademico(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    anio = models.IntegerField(unique=True)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    activo = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-anio']
        verbose_name = 'Periodo Académico'
        verbose_name_plural = 'Periodos Académicos'
    
    def __str__(self):
        return f"{self.nombre} ({self.fecha_inicio} - {self.fecha_fin})"
class Matricula(models.Model):
    ESTADO_CHOICES = [
        ('Activa', 'Activa'),
        ('Trasladado', 'Trasladado'),
        ('Retirado', 'Retirado'),
    ]
    
    periodo_academico = models.ForeignKey('PeriodoAcademico', on_delete=models.RESTRICT, related_name='matriculas', default=None, null=True, blank=True)
    alumno = models.ForeignKey('estudiantes.Estudiante', on_delete=models.RESTRICT, related_name='matriculas')
    aula = models.ForeignKey('estudiantes.Aula', on_delete=models.RESTRICT, related_name='matriculas')
    fecha_matricula = models.DateField(auto_now_add=True)
    observaciones = models.TextField(blank=True, null=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='Activa')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-fecha_matricula']
        indexes = [
            models.Index(fields=['periodo_academico']),
            models.Index(fields=['estado']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['alumno', 'periodo_academico'],
                name='unique_matricula_periodo',
                violation_error_message='El alumno ya está matriculado en este período académico'
            )
        ]
        verbose_name = 'Matrícula'
        verbose_name_plural = 'Matrículas'
    
    def __str__(self):
        alumno_nombre = '-'
        if self.alumno_id:
            nombres = getattr(self.alumno, 'nombres', '')
            apellidos = getattr(self.alumno, 'apellidos', '')
            alumno_nombre = f"{nombres} {apellidos}".strip() or str(self.alumno_id)
        aula_nombre = getattr(self.aula, 'nombre', '-')
        
        return (
    f"{alumno_nombre} - "
    f"Aula {aula_nombre} - "
    f"{self.periodo_academico.nombre}"
)


