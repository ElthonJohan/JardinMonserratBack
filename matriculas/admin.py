from django.contrib import admin
from .models import Matricula, PeriodoAcademico


@admin.register(Matricula)
class MatriculaAdmin(admin.ModelAdmin):
    list_display = ['alumno', 'periodo_academico', 'aula', 'estado']
    list_filter = ['periodo_academico', 'estado', 'aula', 'fecha_matricula']
    search_fields = ['alumno__nombres', 'alumno__apellidos']
    readonly_fields = ['fecha_matricula', 'created_at', 'updated_at']
    fieldsets = (
        ('Información de Matrícula', {
            'fields': ('alumno', 'aula', 'periodo_academico', 'estado')
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

@admin.register(PeriodoAcademico)
class PeriodoAcademicoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'anio', 'fecha_inicio', 'fecha_fin', 'activo']
    list_filter = ['activo']
    search_fields = ['nombre', 'anio']
    readonly_fields = ['fecha_inicio', 'fecha_fin']
    fieldsets = (
        ('Información del Periodo Académico', {
            'fields': ('nombre', 'anio', 'activo')
        }),
        ('Fechas', {
            'fields': ('fecha_inicio', 'fecha_fin'),
            'classes': ('collapse',)
        }),
    )