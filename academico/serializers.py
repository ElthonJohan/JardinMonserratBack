from rest_framework import serializers
from .models import PeriodoEvaluacion, Area, Competencia, Calificacion, Apreciacion, AsignacionDocente

class PeriodoEvaluacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PeriodoEvaluacion
        fields = '__all__'

class AreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Area
        fields = '__all__'

class CompetenciaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Competencia
        fields = '__all__'

class CalificacionSerializer(serializers.ModelSerializer):
    competencia_nombre = serializers.CharField(source='competencia.descripcion', read_only=True)
    docente_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Calificacion
        fields = '__all__'
        read_only_fields = ['docente_evaluador']

    def get_docente_nombre(self, obj):
        if obj.docente_evaluador:
            nombres = getattr(obj.docente_evaluador, 'nombres', '') or getattr(obj.docente_evaluador, 'first_name', '')
            apellidos = getattr(obj.docente_evaluador, 'apellidos', '') or getattr(obj.docente_evaluador, 'last_name', '')
            full_name = f"{nombres} {apellidos}".strip()
            return full_name if full_name else obj.docente_evaluador.username
        return ""

class ApreciacionSerializer(serializers.ModelSerializer):
    docente_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Apreciacion
        fields = '__all__'
        read_only_fields = ['docente']

    def get_docente_nombre(self, obj):
        if obj.docente:
            nombres = getattr(obj.docente, 'nombres', '') or getattr(obj.docente, 'first_name', '')
            apellidos = getattr(obj.docente, 'apellidos', '') or getattr(obj.docente, 'last_name', '')
            full_name = f"{nombres} {apellidos}".strip()
            return full_name if full_name else obj.docente.username
        return ""

class AsignacionDocenteSerializer(serializers.ModelSerializer):
    docente_nombre = serializers.SerializerMethodField()
    aula_nombre = serializers.ReadOnlyField(source='aula.nombre')
    areas = serializers.PrimaryKeyRelatedField(queryset=Area.objects.all(), many=True)
    areas_detalle = AreaSerializer(source='areas', many=True, read_only=True)
    periodo_nombre = serializers.ReadOnlyField(source='periodo_matricula.nombre')

    class Meta:
        model = AsignacionDocente
        fields = '__all__'

    def get_docente_nombre(self, obj):
        if obj.docente:
            nombres = getattr(obj.docente, 'nombres', '') or getattr(obj.docente, 'first_name', '')
            apellidos = getattr(obj.docente, 'apellidos', '') or getattr(obj.docente, 'last_name', '')
            full_name = f"{nombres} {apellidos}".strip()
            return full_name if full_name else obj.docente.username
        return ""
