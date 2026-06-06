from rest_framework import serializers
from .models import Matricula, PeriodoAcademico
from estudiantes.serializers import AulaSerializer
from estudiantes.models import Estudiante


class EstudianteMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Estudiante
        fields = ['id', 'nombres', 'apellidos']

class PeriodoAcademicoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PeriodoAcademico
        fields = ['id', 'nombre', 'anio', 'fecha_inicio', 'fecha_fin', 'activo']
        read_only_fields = ['id']

    
class MatriculaSerializer(serializers.ModelSerializer):
    alumno_detail = EstudianteMiniSerializer(source='alumno', read_only=True)
    aula_detail = AulaSerializer(source='aula', read_only=True)
    periodo_academico_detail = PeriodoAcademicoSerializer(source='periodo_academico', read_only=True)
    class Meta:
        model = Matricula
        fields = [
            'id', 'alumno', 'alumno_detail', 'aula', 'aula_detail', 'periodo_academico', 'periodo_academico_detail',
            'fecha_matricula',
            'estado', 'observaciones', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'fecha_matricula', 'created_at', 'updated_at']
    
    def validate(self, data):
        alumno = data.get('alumno')
        periodo = data.get('periodo_academico')

        existe = Matricula.objects.filter(
            alumno=alumno,
            periodo_academico=periodo
        )

        if self.instance:
            existe = existe.exclude(pk=self.instance.pk)

        if existe.exists():
            raise serializers.ValidationError(
                "El alumno ya está matriculado en este período académico."
            )

        return data
    
    def validate_periodo_academico(self, value):
        if not value.activo:
            raise serializers.ValidationError(
                "El período académico está cerrado."
            )
        return value

    

