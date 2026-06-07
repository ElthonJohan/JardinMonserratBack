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

        # Determinar si tenemos un id explícito en los datos entrantes (por ejemplo cuando
        # el frontend envía {id: X} para reutilizar un apoderado). Si existe, excluirlo
        # de la comprobación de unicidad para evitar falso positivo.
        current_id = None
        if self.instance:
            current_id = getattr(self.instance, 'pk', None)
        else:
            # initial_data puede venir del serializador padre
            try:
                current_id = int(self.initial_data.get('id')) if isinstance(self.initial_data, dict) and self.initial_data.get('id') else None
            except Exception:
                current_id = None

        if current_id:
            queryset = queryset.exclude(pk=current_id)

        if queryset.exists():
            raise serializers.ValidationError("El DNI ya existe.")
            
        return value

class EstudianteSerializer(serializers.ModelSerializer):
    aula_nombre = serializers.CharField(source='aula.nombre', read_only=True)
    apoderado_nombre = serializers.CharField(source='apoderado.nombres', read_only=True)
    codigo_estudiante = serializers.CharField(read_only=True)
    generated_credentials = serializers.SerializerMethodField()

    # Read-only nested representation
    apoderado = ApoderadoSerializer(read_only=True)
    # Write-only field to accept an existing apoderado by id from the frontend
    apoderado_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = Estudiante
        fields = '__all__'

    def get_generated_credentials(self, obj):
        return getattr(obj, '_generated_credentials', None)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Inyectamos la instancia del apoderado en el serializador anidado.
        # Esto es crucial para que ApoderadoSerializer sepa que estamos editando
        # y la validación de DNI único funcione correctamente en actualizaciones.
        # Caso 1: cuando estamos editando un estudiante existente
        if self.instance and hasattr(self.instance, 'apoderado'):
            self.fields['apoderado'].instance = self.instance.apoderado

        # Caso 2: cuando se recibe payload de creación/actualización y el frontend
        # envía { apoderado: { id: X } } para reutilizar un apoderado existente.
        # En ese caso pre-inyectamos la instancia y marcamos el serializer anidado
        # como parcial para que no falle por campos requeridos ausentes.
        try:
            incoming = self.initial_data.get('apoderado') if isinstance(self.initial_data, dict) else None
        except Exception:
            incoming = None

        if isinstance(incoming, dict):
            ap_id = incoming.get('id')
            if ap_id:
                apoderado_obj = Apoderado.objects.filter(pk=ap_id).first()
                if apoderado_obj:
                    self.fields['apoderado'].instance = apoderado_obj
                    # permitir que falten campos en el payload (solo id enviado)
                    self.fields['apoderado'].partial = True

    def update(self, instance, validated_data):
        # Support either nested apoderado data (to create/update) or apoderado_id (to reuse)
        apoderado_data = validated_data.pop('apoderado', None)
        apoderado_id = validated_data.pop('apoderado_id', None)

        if apoderado_data:
            # Actualizar datos del apoderado
            # Si se especifica un `id` o un `dni`, intentar reutilizar ese Apoderado
            apoderado = None
            apoderado_id = apoderado_data.get('id')
            apoderado_dni = apoderado_data.get('dni')

            if apoderado_id:
                apoderado = Apoderado.objects.filter(pk=apoderado_id).first()
            elif apoderado_dni:
                apoderado = Apoderado.objects.filter(dni=apoderado_dni).first()

            if apoderado:
                for attr, value in apoderado_data.items():
                    if attr != 'id':
                        setattr(apoderado, attr, value)
                apoderado.save()
                instance.apoderado = apoderado
            else:
                # Si no existe, actualizar el apoderado actual o crear uno nuevo
                if instance.apoderado:
                    ap = instance.apoderado
                    for attr, value in apoderado_data.items():
                        setattr(ap, attr, value)
                    ap.save()
                else:
                    ap = Apoderado.objects.create(**apoderado_data)
                    instance.apoderado = ap

        # Actualizar datos del estudiante
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
    
    def create(self, validated_data):
        apoderado_data = validated_data.pop('apoderado', None)
        apoderado_id = validated_data.pop('apoderado_id', None)

        with transaction.atomic():
            apoderado = None
            # Priority: explicit apoderado_id (reuse existing)
            if apoderado_id:
                apoderado = Apoderado.objects.filter(pk=apoderado_id).first()

            # If nested apoderado object was provided, try to find or create/update
            if apoderado_data and not apoderado:
                nested_id = apoderado_data.get('id')
                nested_dni = apoderado_data.get('dni')
                if nested_id:
                    apoderado = Apoderado.objects.filter(pk=nested_id).first()
                elif nested_dni:
                    apoderado = Apoderado.objects.filter(dni=nested_dni).first()

                if apoderado:
                    for attr, value in apoderado_data.items():
                        if attr != 'id':
                            setattr(apoderado, attr, value)
                    apoderado.save()
                else:
                    apoderado = Apoderado.objects.create(**apoderado_data)

            estudiante = Estudiante.objects.create(apoderado=apoderado, **validated_data)
        return estudiante
    
    def validate_dni(self, value):
        if value:
            # 1. Validar formato
            if not value.isdigit() or len(value) != 8:
                raise serializers.ValidationError("El DNI debe tener 8 dígitos numéricos.")
            
            # 2. Validar unicidad
            queryset = Estudiante.objects.filter(dni=value)
            if self.instance:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise serializers.ValidationError("Este DNI ya pertenece a otro estudiante.")
        return value
    
class EstudianteProfileSerializer(serializers.ModelSerializer):

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
            'dni',
            'aula_nombre'
        ]


class ApoderadoProfileSerializer(serializers.ModelSerializer):

    estudiantes = EstudianteProfileSerializer(
        many=True,
        read_only=True
    )

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
            'estudiantes'
        ]
