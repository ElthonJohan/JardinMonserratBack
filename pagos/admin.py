from django.contrib import admin
from django.db.models import Sum
from .models import Pago, ConceptoPago, Deuda, Caja, PagoAsignacion

@admin.register(ConceptoPago)
class ConceptoPagoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'tipo', 'monto_base', 'activo']
    list_filter = ['tipo', 'activo']
    search_fields = ['nombre']
    readonly_fields = ['created_at']
    fieldsets = (
        ('Información del Concepto', {
            'fields': ('nombre', 'monto_base', 'tipo', 'activo')
        }),
        ('Fechas', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

@admin.register(Deuda)
class DeudaAdmin(admin.ModelAdmin):
    list_display = ['alumno', 'concepto', 'monto_total', 'monto_pagado', 'saldo_pendiente', 'mes', 'anio', 'estado']
    list_filter = ['estado', 'anio', 'mes', 'concepto']
    search_fields = ['alumno__nombres', 'alumno__apellidos']
    readonly_fields = ['monto_pagado']
    
    def saldo_pendiente(self, obj):
        return obj.saldo_pendiente
    saldo_pendiente.short_description = 'Saldo Pendiente'

@admin.register(Caja)
class CajaAdmin(admin.ModelAdmin):
    list_display = ['id', 'usuario', 'fecha_apertura', 'fecha_cierre', 'monto_inicial', 'estado']
    list_filter = ['estado', 'fecha_apertura']
    search_fields = ['usuario__username']
    readonly_fields = ['fecha_apertura']

@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = ['id', 'alumno', 'monto_total_entregado', 'monto_asignado', 'saldo_no_asignado', 'fecha_pago', 'metodo_pago', 'caja']
    list_filter = ['metodo_pago', 'fecha_pago', 'caja']
    search_fields = ['alumno__nombres', 'alumno__apellidos', 'numero_operacion']
    readonly_fields = ['fecha_pago']
    
    fieldsets = (
        ('Información del Pago', {
            'fields': ('alumno', 'caja', 'monto_total_entregado', 'metodo_pago', 'numero_operacion')
        }),
        ('Evidencia', {
            'fields': ('comprobante_img', 'observaciones', 'usuario_registro'),
            'classes': ('collapse',)
        }),
        ('Fechas', {
            'fields': ('fecha_pago',),
            'classes': ('collapse',)
        }),
    )
    
    def monto_asignado(self, obj):
        total = obj.asignaciones.aggregate(Sum('monto_aplicado'))['monto_aplicado__sum'] or 0
        return total
    monto_asignado.short_description = 'Monto Asignado'
    
    def saldo_no_asignado(self, obj):
        return obj.monto_total_entregado - self.monto_asignado(obj)
    saldo_no_asignado.short_description = 'Saldo No Asignado'

@admin.register(PagoAsignacion)
class PagoAsignacionAdmin(admin.ModelAdmin):
    list_display = ['pago', 'deuda', 'monto_aplicado']
    list_filter = ['pago__metodo_pago', 'deuda__estado']
    search_fields = ['pago__alumno__nombres', 'deuda__alumno__nombres']
    readonly_fields = ['pago', 'deuda']  # Opcional: hacer que solo se puedan crear, no editar
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # Si es edición
            return ['pago', 'deuda', 'monto_aplicado']
        return []