from rest_framework import serializers
from .models import Matricula
from estudiantes.serializers import AulaSerializer
from estudiantes.models import Estudiante


class EstudianteMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Estudiante
        fields = ['id', 'nombres', 'apellidos']


class MatriculaSerializer(serializers.ModelSerializer):
    alumno_detail = EstudianteMiniSerializer(source='alumno', read_only=True)
    aula_detail = AulaSerializer(source='aula', read_only=True)
    
    class Meta:
        model = Matricula
        fields = [
            'id', 'alumno', 'alumno_detail', 'aula', 'aula_detail',
            'anio', 'fecha_matricula',
            'estado', 'observaciones', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'fecha_matricula', 'created_at', 'updated_at']
