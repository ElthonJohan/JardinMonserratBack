from rest_framework import serializers
from django.db import transaction
from .models import ApoderadoEstudiante, Estudiante, Aula, Apoderado

class AulaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Aula
        fields = '__all__'


class ApoderadoSerializer(serializers.ModelSerializer):

    class Meta:
        model = Apoderado
        fields = '__all__'

    def validate_dni(self, value):
        if value:
            if not value.isdigit() or len(value) != 8:
                raise serializers.ValidationError(
                    "El DNI debe contener 8 dígitos."
                )

        return value
    
class ApoderadoMiniSerializer(
    serializers.ModelSerializer
):

    class Meta:
        model = Apoderado
        fields = [
            'id',
            'nombres',
            'apellidos',
            'dni'
        ]
    
class ApoderadoRelacionSerializer(
    serializers.ModelSerializer
):

    apoderado = ApoderadoMiniSerializer()

    class Meta:
        model = ApoderadoEstudiante
        fields = [
            'id',
            'tipo_relacion',
            'es_principal',
            'apoderado'
        ]

class EstudianteSerializer(
    serializers.ModelSerializer
):

    aula_nombre = serializers.CharField(
        source='aula.nombre',
        read_only=True
    )

    codigo_estudiante = serializers.CharField(
        read_only=True
    )

    apoderados_detail = (
        ApoderadoRelacionSerializer(
            source='apoderados',
            many=True,
            read_only=True
        )
    )

    class Meta:
        model = Estudiante
        fields = [
            'id',
            'nombres',
            'apellidos',
            'fecha_nacimiento',
            'codigo_estudiante',
            'dni',
            'aula',
            'aula_nombre',
            'apoderados_detail'
        ]
    
class ApoderadoEstudianteSerializer(
    serializers.ModelSerializer
):

    apoderado_nombre = serializers.CharField(
        source='apoderado.nombres',
        read_only=True
    )

    estudiante_nombre = serializers.CharField(
        source='estudiante.nombres',
        read_only=True
    )

    class Meta:
        model = ApoderadoEstudiante
        fields = [
            'id',
            'apoderado',
            'apoderado_nombre',
            'estudiante',
            'estudiante_nombre',
            'tipo_relacion',
            'es_principal'
        ]

    class Meta:
        model = ApoderadoEstudiante
        fields = '__all__'
        
class HijoSerializer(
    serializers.ModelSerializer
):

    aula_nombre = serializers.CharField(
        source='aula.nombre',
        read_only=True
    )

    class Meta:
        model = Estudiante
        fields = [
            'id',
            'nombres',
            'apellidos',
            'codigo_estudiante',
            'aula_nombre'
        ]

class ApoderadoProfileSerializer(
    serializers.ModelSerializer
):

    hijos = serializers.SerializerMethodField()

    class Meta:
        model = Apoderado
        fields = [
            'id',
            'nombres',
            'apellidos',
            'dni',
            'email',
            'telefono',
            'direccion',
            'hijos'
        ]

    def get_hijos(self, obj):

        relaciones = (
            ApoderadoEstudiante.objects
            .select_related('estudiante')
            .filter(apoderado=obj)
        )

        return HijoSerializer(
            [r.estudiante for r in relaciones],
            many=True
        ).data
    

class RegistroAlumnoSerializer(serializers.Serializer):

    estudiante = serializers.DictField()

    apoderado = serializers.DictField()

    tipo_relacion = serializers.CharField()

    es_principal = serializers.BooleanField(
        default=True
    )