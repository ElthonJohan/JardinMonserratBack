from django.contrib import admin
from .models import Matricula


@admin.register(Matricula)
class MatriculaAdmin(admin.ModelAdmin):
    list_display = ['alumno', 'anio', 'aula', 'estado']
    list_filter = ['anio', 'estado', 'aula', 'fecha_matricula']
    search_fields = ['alumno__nombres', 'alumno__apellidos']
    readonly_fields = ['fecha_matricula', 'created_at', 'updated_at']
    fieldsets = (
        ('Información de Matrícula', {
            'fields': ('alumno', 'aula', 'anio', 'estado')
        }),
        ('Observaciones', {
            'fields': ('observaciones',),
            'classes': ('collapse',)
        }),
        ('Fechas', {
            'fields': ('fecha_matricula', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
