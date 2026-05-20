from rest_framework import serializers
from django.db import transaction
from .models import Estudiante, Aula, Apoderado

class AulaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Aula
        fields = '__all__'


class ApoderadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Apoderado
        fields = '__all__'

    def validate_dni(self, value):
        # 1. Validar que sean solo números y exactamente 8 dígitos
        if not value.isdigit() or len(value) != 8:
            raise serializers.ValidationError("El DNI debe contener exactamente 8 dígitos numéricos.")

        # 2. Validar unicidad considerando la instancia actual (para actualizaciones)
        # Excluimos la instancia actual de la búsqueda para permitir guardar si el DNI no cambió
        queryset = Apoderado.objects.filter(dni=value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        
        if queryset.exists():
            raise serializers.ValidationError("El DNI ya existe.")
            
        return value

class EstudianteSerializer(serializers.ModelSerializer):
    aula_nombre = serializers.CharField(source='aula.nombre', read_only=True)
    apoderado_nombre = serializers.CharField(source='apoderado.nombres', read_only=True)
    codigo_estudiante = serializers.CharField(read_only=True)

    apoderado = ApoderadoSerializer()

    class Meta:
        model = Estudiante
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Inyectamos la instancia del apoderado en el serializador anidado.
        # Esto es crucial para que ApoderadoSerializer sepa que estamos editando
        # y la validación de DNI único funcione correctamente en actualizaciones.
        if self.instance and hasattr(self.instance, 'apoderado'):
            self.fields['apoderado'].instance = self.instance.apoderado

    # def create(self, validated_data):
    #     apoderado_data = validated_data.pop('apoderado')
    #     # Usamos transaction.atomic para asegurar la integridad de los datos
    #     with transaction.atomic():
    #         apoderado = Apoderado.objects.create(**apoderado_data)
    #         estudiante = Estudiante.objects.create(apoderado=apoderado, **validated_data)
    #     return estudiante

    def update(self, instance, validated_data):
        apoderado_data = validated_data.pop('apoderado', None)

        if apoderado_data:
            # Actualizar datos del apoderado
            apoderado = instance.apoderado
            for attr, value in apoderado_data.items():
                setattr(apoderado, attr, value)
            apoderado.save()

        # Actualizar datos del estudiante
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
    
    #Hacer que el código se autogenere a partir de las iniciales del nombre y apellido del estudiante y un número secuencial
    def create(self, validated_data):
        # Obtener los datos del apoderado
        apoderado_data = validated_data.pop('apoderado')

        with transaction.atomic():

            # Crear el apoderado
            apoderado = Apoderado.objects.create(**apoderado_data)

            # Generar el código de estudiante a partir de las iniciales y un número secuencial
            nombres = validated_data.get('nombres', '')
            apellidos = validated_data.get('apellidos', '')
            codigo_estudiante = f"{nombres[0]}{apellidos[0]}{Estudiante.objects.count() + 1:04d}"
            validated_data['codigo_estudiante'] = codigo_estudiante
            # Crear el estudiante con el apoderado asociado
            estudiante = Estudiante.objects.create(apoderado=apoderado, **validated_data)
        return estudiante
    
    def validate(self, data):
        # Validar que codigo de estudiante sea único y dni también sea único
        dni = data.get('dni')

        # Al ser read_only, codigo_estudiante no vendrá en 'data'. 
        # La validación de unicidad para el código generado se puede omitir aquí 
        # ya que el modelo tiene unique=True y lo manejas en el create.

        if Estudiante.objects.filter(dni=dni).exclude(pk=self.instance.pk if self.instance else None).exists():
            raise serializers.ValidationError("El DNI ya existe.")
        return data
    