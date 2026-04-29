from django.db import models


class ConceptoPago(models.Model):
    PERIODICIDAD_CHOICES = [
        ('Mensual', 'Mensual'),
        ('Trimestral', 'Trimestral'),
        ('Anual', 'Anual'),
        ('Único', 'Único'),
    ]
    
    nombre = models.CharField(max_length=100, unique=True)
    monto_base = models.DecimalField(max_digits=10, decimal_places=2)
    periodicidad = models.CharField(max_length=20, choices=PERIODICIDAD_CHOICES, default='Mensual')
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['nombre']
        verbose_name = 'Concepto de Pago'
        verbose_name_plural = 'Conceptos de Pago'
    
    def __str__(self):
        return f"{self.nombre} - ${self.monto_base}"


class Pago(models.Model):
    METODO_PAGO_CHOICES = [
        ('Efectivo', 'Efectivo'),
        ('Transferencia', 'Transferencia'),
        ('Depósito', 'Depósito'),
        ('Tarjeta', 'Tarjeta'),
    ]
    
    ESTADO_CHOICES = [
        ('Pagado', 'Pagado'),
        ('Pendiente', 'Pendiente'),
        ('Vencido', 'Vencido'),
        ('Anulado', 'Anulado'),
    ]
    
    alumno = models.ForeignKey('estudiantes.Estudiante', on_delete=models.RESTRICT, related_name='pagos')
    concepto = models.ForeignKey(ConceptoPago, on_delete=models.RESTRICT, related_name='pagos')
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    mes = models.IntegerField(blank=True, null=True)  # 1=Enero, 2=Febrero... (NULL si no es mensual)
    anio = models.IntegerField()  # Año del pago
    fecha_pago = models.DateField()
    fecha_vencimiento = models.DateField()
    metodo_pago = models.CharField(max_length=20, choices=METODO_PAGO_CHOICES)
    numero_recibo = models.CharField(max_length=20, unique=True)
    comprobante_url = models.FileField(upload_to='comprobantes/', blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='Pagado')
    usuario_registro = models.CharField(max_length=50)  # Quién registró el pago
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-fecha_pago']
        indexes = [
            models.Index(fields=['alumno']),
            models.Index(fields=['fecha_pago']),
            models.Index(fields=['estado']),
            models.Index(fields=['anio', 'mes']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['alumno', 'concepto', 'anio', 'mes'],
                condition=models.Q(mes__isnull=False),
                name='unique_pago_mensual',
                violation_error_message='Este alumno ya tiene un pago registrado para este mes'
            )
        ]
        verbose_name = 'Pago'
        verbose_name_plural = 'Pagos'
    
    def __str__(self):
        mes_str = f" - Mes {self.mes}" if self.mes else ""
        alumno_nombre = '-'
        if self.alumno_id:
            nombres = getattr(self.alumno, 'nombres', '')
            apellidos = getattr(self.alumno, 'apellidos', '')
            alumno_nombre = f"{nombres} {apellidos}".strip() or str(self.alumno_id)
        return f"{alumno_nombre} - {self.concepto.nombre} ({self.anio}){mes_str}"
