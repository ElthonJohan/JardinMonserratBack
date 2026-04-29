from rest_framework import serializers
from .models import Pago, ConceptoPago
from estudiantes.models import Estudiante


class EstudianteMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Estudiante
        fields = ['id', 'nombres', 'apellidos']


class ConceptoPagoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConceptoPago
        fields = [
            'id', 'nombre', 'monto_base', 'periodicidad', 'activo',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class PagoSerializer(serializers.ModelSerializer):
    alumno_detail = EstudianteMiniSerializer(source='alumno', read_only=True)
    concepto_detail = ConceptoPagoSerializer(source='concepto', read_only=True)
    
    class Meta:
        model = Pago
        fields = [
            'id', 'alumno', 'alumno_detail', 'concepto', 'concepto_detail',
            'monto', 'mes', 'anio', 'fecha_pago', 'fecha_vencimiento',
            'metodo_pago', 'numero_recibo', 'comprobante_url', 'observaciones',
            'estado', 'usuario_registro', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
