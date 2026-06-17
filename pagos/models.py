from django.db import models
from django.core.exceptions import ValidationError
from django.db.models import Sum
from django.utils import timezone
from decimal import Decimal

class ConceptoPago(models.Model):
    TIPO_CHOICES = [
        ('CUOTA_INGRESO', 'Cuota de Ingreso (Único)'),
        ('MATRICULA', 'Matrícula (Anual)'),
        ('PENSION', 'Pensión (Mensual)'),
        ('OTROS', 'Otros Pagos'),
    ]
    
    nombre = models.CharField(max_length=100, unique=True)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='PENSION')
    monto_base = models.DecimalField(max_digits=10, decimal_places=2)
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Concepto de Pago'
        verbose_name_plural = 'Conceptos de Pago'

    def __str__(self):
        return f"{self.nombre} - S/ {self.monto_base}"

class Deuda(models.Model):
    ESTADO_DEUDA = [
        ('Pendiente', 'Pendiente'),
        ('Parcial', 'Parcial'),
        ('Pagado', 'Pagado'),
        ('Anulado', 'Anulado'),
    ]

    alumno = models.ForeignKey('estudiantes.Estudiante', on_delete=models.CASCADE, related_name='deudas')
    periodo_academico = models.ForeignKey('matriculas.PeriodoAcademico', on_delete=models.CASCADE, related_name='deudas', null=True, blank=True)
    concepto = models.ForeignKey(ConceptoPago, on_delete=models.RESTRICT)
    detalle_adicional = models.CharField(max_length=255, blank=True, null=True)
    monto_total = models.DecimalField(max_digits=10, decimal_places=2)
    monto_pagado = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    mes = models.IntegerField(blank=True, null=True)
    anio = models.IntegerField()
    fecha_vencimiento = models.DateField()
    estado = models.CharField(max_length=20, choices=ESTADO_DEUDA, default='Pendiente')
    
    class Meta:
        verbose_name = 'Recibo de Cobranza'
        verbose_name_plural = 'Recibos de Cobranza'
        ordering = ['id']

    def clean(self):
        super().clean()
        if hasattr(self, 'concepto') and self.concepto and self.concepto.tipo in ['PENSION', 'MATRICULA']:
            qs = Deuda.objects.filter(
                alumno=self.alumno,
                concepto=self.concepto,
                mes=self.mes,
                anio=self.anio
            )
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError("Ya existe una deuda registrada para este alumno, concepto, mes y año.")

    @property
    def saldo_pendiente(self):
        return self.monto_total - self.monto_pagado

    def actualizar_estado(self):
        """Calcula el total pagado basado en las asignaciones y actualiza el estado."""
        total = self.asignaciones.filter(pago__estado='APROBADO').aggregate(Sum('monto_aplicado'))['monto_aplicado__sum'] or 0
        self.monto_pagado = total
        if self.monto_pagado >= self.monto_total:
            self.estado = 'Pagado'
        elif self.monto_pagado > 0:
            self.estado = 'Parcial'
        else:
            self.estado = 'Pendiente'
        self.save()

    def __str__(self):
        return f"{self.alumno} - {self.concepto.nombre} - {self.mes}/{self.anio}"

class Caja(models.Model):
    ESTADO_CAJA = [
        ('Abierta', 'Abierta'),
        ('Cerrada', 'Cerrada'),
    ]

    usuario = models.ForeignKey('usuarios.Usuario', on_delete=models.PROTECT) #
    fecha_apertura = models.DateTimeField(auto_now_add=True)
    fecha_cierre = models.DateTimeField(null=True, blank=True)
    monto_inicial = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    estado = models.CharField(max_length=10, choices=ESTADO_CAJA, default='Abierta')

    class Meta:
        verbose_name = 'Caja Diaria'
        verbose_name_plural = 'Control de Cajas'

    def __str__(self):
        return f"Caja {self.id} - {self.usuario} ({self.fecha_apertura.date()})"

class Banco(models.Model):
    nombre = models.CharField(max_length=100)
    numero_cuenta = models.CharField(max_length=30, null=True, blank=True)
    cci = models.CharField(max_length=20, null=True, blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Banco'
        verbose_name_plural = 'Bancos'

    def __str__(self):
        return self.nombre

class Pago(models.Model):
    METODO_PAGO_CHOICES = [
        ('Efectivo', 'Efectivo'),
        ('Yape', 'Yape'),
        ('Plin', 'Plin'),
        ('Transferencia', 'Transferencia'),
        ('Depósito', 'Depósito'),
    ]
    
    ESTADO_PAGO_CHOICES = [
        ('REGISTRADO', 'Registrado'),
        ('APROBADO', 'Aprobado'),
        ('RECHAZADO', 'Rechazado'),
    ]
    
    # Cabecera del Pago
    alumno = models.ForeignKey('estudiantes.Estudiante', on_delete=models.CASCADE, related_name='pagos_realizados', null=True)
    caja = models.ForeignKey(Caja, on_delete=models.PROTECT, related_name='pagos', null=True, blank=True)
    monto_total_entregado = models.DecimalField(max_digits=10, decimal_places=2, help_text="Total de dinero recibido en el voucher/efectivo")
    fecha_pago = models.DateTimeField(default=timezone.now)
    metodo_pago = models.CharField(max_length=20, choices=METODO_PAGO_CHOICES, default='Efectivo')
    
    # Relación con Deudas a través de PagoAsignacion
    deuda = models.ForeignKey(
    Deuda,
    on_delete=models.CASCADE,
    related_name='pagos_reportados',
    null=True,
    blank=True
)
    # Datos Bancarios y Comprobante
    banco = models.ForeignKey(Banco, on_delete=models.PROTECT, null=True, blank=True)
    numero_operacion = models.CharField(max_length=50, blank=True, null=True)
    comprobante_img = models.ImageField(upload_to='vouchers/', blank=True, null=True)
    
    # Estados y Flujo de Aprobación
    estado = models.CharField(max_length=20, choices=ESTADO_PAGO_CHOICES, default='REGISTRADO')
    fecha_aprobacion = models.DateTimeField(null=True, blank=True)
    motivo_rechazo = models.TextField(null=True, blank=True)
    
    # Usuarios (Creador y Validador)
    usuario_creador = models.ForeignKey('usuarios.Usuario', on_delete=models.SET_NULL, null=True, blank=True, related_name='pagos_creados')
    usuario_validador = models.ForeignKey('usuarios.Usuario', on_delete=models.SET_NULL, null=True, blank=True, related_name='pagos_validados')
    
    observaciones = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = 'Transacción de Pago'
        verbose_name_plural = 'Transacciones de Pago'
        unique_together = ['numero_operacion', 'banco']

    def clean(self):
        super().clean()
        if self.metodo_pago in ['Transferencia', 'Depósito']:
            if not self.banco:
                raise ValidationError({"banco": "El banco es obligatorio para transferencias o depósitos."})
            if not self.numero_operacion:
                raise ValidationError({"numero_operacion": "El número de operación es obligatorio."})
        elif self.metodo_pago in ['Yape', 'Plin']:
            if not self.numero_operacion:
                raise ValidationError({"numero_operacion": "El número de operación es obligatorio para pagos digitales."})
            self.banco = None
        elif self.metodo_pago == 'Efectivo':
            self.banco = None
            self.numero_operacion = None
        
        if self.estado == 'APROBADO' and not self.caja:
            raise ValidationError("Debe asignarse a una caja receptora para ser aprobado.")
            
        if self.estado == 'RECHAZADO' and not self.motivo_rechazo:
            raise ValidationError("Debe especificarse un motivo de rechazo.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Pago {self.id} - {self.alumno} - S/ {self.monto_total_entregado}"

class PagoAsignacion(models.Model):
    """
    Esta tabla permite que un Pago (voucher) se reparta entre múltiples Deudas.
    """
    pago = models.ForeignKey(Pago, on_delete=models.CASCADE, related_name='asignaciones')
    deuda = models.ForeignKey(Deuda, on_delete=models.CASCADE, related_name='asignaciones')
    monto_aplicado = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Al guardar una asignación, notificamos a la deuda para que actualice su saldo y estado
        self.deuda.actualizar_estado()

    class Meta:
        verbose_name = 'Asignación de Pago'
        verbose_name_plural = 'Asignaciones de Pago'