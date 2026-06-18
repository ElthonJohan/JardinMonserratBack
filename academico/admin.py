from django.contrib import admin
from .models import PeriodoEvaluacion, Area, Competencia, Calificacion, Apreciacion, AsignacionDocente

@admin.register(PeriodoEvaluacion)
class PeriodoEvaluacionAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'periodo_matricula', 'fecha_inicio', 'fecha_fin', 'activo')
    list_filter = ('activo', 'periodo_matricula')
    search_fields = ('nombre',)

@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'orden', 'activo')
    list_filter = ('activo',)
    search_fields = ('nombre',)
    ordering = ('orden',)

@admin.register(Competencia)
class CompetenciaAdmin(admin.ModelAdmin):
    list_display = ('descripcion_corta', 'area', 'orden', 'activo')
    list_filter = ('activo', 'area')
    search_fields = ('descripcion',)
    ordering = ('area', 'orden')

    def descripcion_corta(self, obj):
        return obj.descripcion[:50] + '...' if len(obj.descripcion) > 50 else obj.descripcion
    descripcion_corta.short_description = 'Descripción'

@admin.register(Calificacion)
class CalificacionAdmin(admin.ModelAdmin):
    list_display = ('alumno', 'competencia', 'periodo_evaluacion', 'valor', 'fecha_registro')
    list_filter = ('valor', 'periodo_evaluacion', 'competencia__area')
    search_fields = ('alumno__nombres', 'alumno__apellidos', 'competencia__descripcion')

@admin.register(Apreciacion)
class ApreciacionAdmin(admin.ModelAdmin):
    list_display = ('alumno', 'periodo_evaluacion', 'docente', 'fecha_registro')
    list_filter = ('periodo_evaluacion',)
    search_fields = ('alumno__nombres', 'alumno__apellidos', 'docente__nombres', 'docente__apellidos')

@admin.register(AsignacionDocente)
class AsignacionDocenteAdmin(admin.ModelAdmin):
    list_display = ('docente', 'aula', 'area', 'periodo_matricula', 'activo', 'created_at')
    list_filter = ('aula', 'area', 'periodo_matricula', 'activo')
    search_fields = ('docente__username', 'docente__first_name', 'docente__last_name', 'aula__nombre', 'area__nombre')
