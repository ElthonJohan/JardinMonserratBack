from django.contrib import admin
from .models import Pago, ConceptoPago


@admin.register(ConceptoPago)
class ConceptoPagoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'monto_base', 'periodicidad', 'activo']
    list_filter = ['periodicidad', 'activo']
    search_fields = ['nombre']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Información del Concepto', {
            'fields': ('nombre', 'monto_base', 'periodicidad', 'activo')
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = ['alumno', 'concepto', 'monto', 'fecha_pago', 'numero_recibo', 'estado']
    list_filter = ['estado', 'metodo_pago', 'fecha_pago', 'anio', 'mes']
    search_fields = ['alumno__nombres', 'alumno__apellidos', 'numero_recibo']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Información del Pago', {
            'fields': ('alumno', 'concepto', 'monto', 'numero_recibo', 'metodo_pago', 'estado')
        }),
        ('Período', {
            'fields': ('anio', 'mes', 'fecha_pago', 'fecha_vencimiento')
        }),
        ('Comprobante', {
            'fields': ('comprobante_url', 'observaciones', 'usuario_registro'),
            'classes': ('collapse',)
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
