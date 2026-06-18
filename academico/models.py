from django.db import models

class PeriodoEvaluacion(models.Model):
    nombre = models.CharField(max_length=100)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    periodo_matricula = models.ForeignKey('matriculas.PeriodoAcademico', on_delete=models.RESTRICT, related_name='periodos_evaluacion')
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Periodo de Evaluación'
        verbose_name_plural = 'Periodos de Evaluación'
        ordering = ['fecha_inicio']

    def __str__(self):
        return f"{self.nombre} ({self.periodo_matricula.nombre})"

class Area(models.Model):
    nombre = models.CharField(max_length=100)
    orden = models.IntegerField()
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Área'
        verbose_name_plural = 'Áreas'
        ordering = ['orden']

    def __str__(self):
        return self.nombre

class Competencia(models.Model):
    descripcion = models.TextField()
    area = models.ForeignKey(Area, on_delete=models.RESTRICT, related_name='competencias')
    orden = models.IntegerField()
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Competencia'
        verbose_name_plural = 'Competencias'
        ordering = ['area', 'orden']

    def __str__(self):
        return f"{self.area.nombre} - {self.descripcion[:50]}"

class Calificacion(models.Model):
    VALOR_CHOICES = [
        ('AD', 'AD'),
        ('A', 'A'),
        ('B', 'B'),
        ('C', 'C'),
    ]

    valor = models.CharField(max_length=2, choices=VALOR_CHOICES)
    alumno = models.ForeignKey('estudiantes.Estudiante', on_delete=models.CASCADE, related_name='calificaciones')
    competencia = models.ForeignKey(Competencia, on_delete=models.RESTRICT, related_name='calificaciones')
    periodo_evaluacion = models.ForeignKey(PeriodoEvaluacion, on_delete=models.RESTRICT, related_name='calificaciones')
    docente_evaluador = models.ForeignKey('usuarios.Usuario', on_delete=models.RESTRICT, related_name='calificaciones_registradas')
    fecha_registro = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Calificación'
        verbose_name_plural = 'Calificaciones'
        unique_together = ['alumno', 'competencia', 'periodo_evaluacion']

    def __str__(self):
        return f"{self.alumno} - {self.competencia.area.nombre}: {self.valor}"

class Apreciacion(models.Model):
    comentario = models.TextField()
    alumno = models.ForeignKey('estudiantes.Estudiante', on_delete=models.CASCADE, related_name='apreciaciones')
    periodo_evaluacion = models.ForeignKey(PeriodoEvaluacion, on_delete=models.RESTRICT, related_name='apreciaciones')
    docente = models.ForeignKey('usuarios.Usuario', on_delete=models.RESTRICT, related_name='apreciaciones_registradas')
    fecha_registro = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Apreciación'
        verbose_name_plural = 'Apreciaciones'
        unique_together = ['alumno', 'periodo_evaluacion']

    def __str__(self):
        return f"Apreciación de {self.alumno} - {self.periodo_evaluacion.nombre}"

class AsignacionDocente(models.Model):
    docente = models.ForeignKey('usuarios.Usuario', on_delete=models.RESTRICT, related_name='asignaciones_academicas')
    aula = models.ForeignKey('estudiantes.Aula', on_delete=models.RESTRICT, related_name='asignaciones_docentes')
    area = models.ForeignKey('academico.Area', on_delete=models.RESTRICT, related_name='asignaciones_docentes')
    periodo_matricula = models.ForeignKey('matriculas.PeriodoAcademico', on_delete=models.RESTRICT, related_name='asignaciones_docentes')
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Asignación Docente'
        verbose_name_plural = 'Asignaciones Docentes'
        unique_together = ['docente', 'aula', 'area', 'periodo_matricula']

    def __str__(self):
        return f"{self.docente} - {self.area} - {self.aula} ({self.periodo_matricula.nombre if self.periodo_matricula else ''})"
