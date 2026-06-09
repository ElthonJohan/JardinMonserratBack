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
        
class HijoSerializer(serializers.ModelSerializer):

    nombre_completo = serializers.SerializerMethodField()

    class Meta:
        model = Estudiante

        fields = [
            'id',
            'codigo_estudiante',
            'dni',
            'nombre_completo'
        ]

    def get_nombre_completo(self, obj):
        return f"{obj.nombres} {obj.apellidos}"

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

        return [
            {
                "id": r.estudiante.id,
                "codigo_estudiante":
                    r.estudiante.codigo_estudiante,

                "nombre":
                    f"{r.estudiante.nombres} "
                    f"{r.estudiante.apellidos}",

                "tipo_relacion":
                    r.tipo_relacion,

                "es_principal":
                    r.es_principal
            }
            for r in relaciones
        ]

class AgregarApoderadoSerializer(serializers.Serializer):

    dni = serializers.CharField(max_length=8)

    nombres = serializers.CharField(
        max_length=100,
        required=False
    )

    apellidos = serializers.CharField(
        max_length=100,
        required=False
    )

    telefono = serializers.CharField(
        max_length=20,
        required=False
    )

    email = serializers.EmailField(
        required=False
    )

    direccion = serializers.CharField(
        required=False,
        allow_blank=True
    )

    tipo_relacion = serializers.ChoiceField(
        choices=[
            'PADRE',
            'MADRE',
            'TUTOR',
            'ABUELO',
            'OTRO'
        ]
    )

    es_principal = serializers.BooleanField(
        default=False
    ) 

class ApoderadoEstudianteDetalleSerializer(
    serializers.ModelSerializer
):

    relacion_id = serializers.IntegerField(
        source='id',
        read_only=True
    )

    apoderado_id = serializers.IntegerField(
        source='apoderado.id'
    )

    nombres = serializers.CharField(
        source='apoderado.nombres'
    )

    apellidos = serializers.CharField(
        source='apoderado.apellidos'
    )

    dni = serializers.CharField(
        source='apoderado.dni'
    )

    telefono = serializers.CharField(
        source='apoderado.telefono'
    )

    email = serializers.CharField(
        source='apoderado.email'
    )

    direccion = serializers.CharField(
        source='apoderado.direccion'
    )

    class Meta:
        model = ApoderadoEstudiante

        fields = [
            'relacion_id',
            'apoderado_id',
            'nombres',
            'apellidos',
            'dni',
            'telefono',
            'email',
            'direccion',
            'tipo_relacion',
            'es_principal'
        ]
        
class RegistroAlumnoSerializer(serializers.Serializer):

    estudiante = serializers.DictField()

    apoderado = serializers.DictField()

    tipo_relacion = serializers.CharField()

    es_principal = serializers.BooleanField(
        default=True
    )