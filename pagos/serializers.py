from rest_framework import serializers
from .models import Pago, ConceptoPago, Deuda, Caja, PagoAsignacion
from estudiantes.models import Estudiante
from django.utils import timezone


class EstudianteMiniSerializer(serializers.ModelSerializer):
    """Serializer mínimo para mostrar datos del estudiante"""
    class Meta:
        model = Estudiante
        fields = ['id', 'nombres', 'apellidos']


class ConceptoPagoSerializer(serializers.ModelSerializer):
    """Serializer para conceptos de pago"""
    class Meta:
        model = ConceptoPago
        fields = ['id', 'nombre', 'tipo', 'monto_base', 'activo', 'created_at']
        read_only_fields = ['id', 'created_at']


class DeudaSerializer(serializers.ModelSerializer):
    """Serializer para deudas con información del estudiante y concepto"""
    alumno_detail = EstudianteMiniSerializer(source='alumno', read_only=True)
    concepto_detail = ConceptoPagoSerializer(source='concepto', read_only=True)
    saldo_pendiente = serializers.SerializerMethodField()
    
    class Meta:
        model = Deuda
        fields = [
            'id', 'alumno', 'alumno_detail', 'concepto', 'concepto_detail',
            'monto_total', 'monto_pagado', 'saldo_pendiente', 'mes', 'anio',
            'fecha_vencimiento', 'estado'
        ]
        read_only_fields = ['id', 'monto_pagado']
    
    def get_saldo_pendiente(self, obj):
        return obj.saldo_pendiente


class PagoAsignacionSerializer(serializers.ModelSerializer):
    """Serializer para detalles del pago (asignación a deudas)"""
    deuda_detail = serializers.SerializerMethodField()
    
    class Meta:
        model = PagoAsignacion
        fields = ['id', 'deuda', 'deuda_detail', 'monto_aplicado']
        read_only_fields = ['id']
    
    def get_deuda_detail(self, obj):
        return {
            'id': obj.deuda.id,
            'alumno_nombres': obj.deuda.alumno.nombres,
            'alumno_apellidos': obj.deuda.alumno.apellidos,
            'concepto': obj.deuda.concepto.nombre,
            'mes': obj.deuda.mes,
            'anio': obj.deuda.anio,
            'monto_total': str(obj.deuda.monto_total),
            'saldo_pendiente': str(obj.deuda.saldo_pendiente)
        }


class PagoSerializer(serializers.ModelSerializer):
    """Serializer para pagos (cabecera) con validaciones de seguridad"""
    alumno_detail = EstudianteMiniSerializer(source='alumno', read_only=True)
    usuario_detail = serializers.SerializerMethodField()
    asignaciones = PagoAsignacionSerializer(many=True, read_only=True)
    monto_aplicado = serializers.SerializerMethodField()
    
    class Meta:
        model = Pago
        fields = [
            'id', 'alumno', 'alumno_detail', 'caja', 'monto_total_entregado',
            'monto_aplicado', 'fecha_pago', 'metodo_pago', 'numero_operacion', 
            'comprobante_img', 'usuario_registro', 'usuario_detail', 'observaciones', 
            'asignaciones'
        ]
        read_only_fields = ['id', 'fecha_pago', 'usuario_registro', 'asignaciones', 'monto_aplicado']
    
    def validate_numero_operacion(self, value):
        """Valida que numero_operacion sea unico (excepto para Efectivo)"""
        metodo_pago = self.initial_data.get('metodo_pago')
        
        if metodo_pago == 'Efectivo':
            return value
        
        if not value:
            raise serializers.ValidationError(
                "El numero de operacion es obligatorio para pagos no en efectivo."
            )
        
        request = self.context.get('request')
        existing = Pago.objects.filter(numero_operacion=value).exclude(
            pk=self.instance.pk if self.instance else None
        ).exists()
        
        if existing:
            raise serializers.ValidationError(
                "Este numero de operacion ya esta registrado. Verifica el comprobante."
            )
        
        return value
    
    def validate(self, data):
        """Validaciones a nivel de objeto"""
        request = self.context.get('request')
        
        if request:
            caja_abierta = Caja.objects.filter(
                usuario=request.user,
                estado='Abierta'
            ).exists()
            
            if not caja_abierta:
                raise serializers.ValidationError({
                    'caja': 'No tienes una Caja abierta. Abre una caja antes de registrar pagos.'
                })
        
        if data.get('monto_total_entregado', 0) <= 0:
            raise serializers.ValidationError({
                'monto_total_entregado': 'El monto debe ser mayor a cero.'
            })
        
        return data
    
    def get_usuario_detail(self, obj):
        if obj.usuario_registro:
            return {
                'id': obj.usuario_registro.id,
                'username': obj.usuario_registro.username,
                'nombre': f"{obj.usuario_registro.first_name} {obj.usuario_registro.last_name}"
            }
        return None
    
    def get_monto_aplicado(self, obj):
        """Suma del monto_aplicado de todas las asignaciones"""
        total = obj.asignaciones.aggregate(
            total=serializers.Sum('monto_aplicado')
        )['total'] or 0
        return float(total)


class CajaSerializer(serializers.ModelSerializer):
    """Serializer para control de caja"""
    usuario_detail = serializers.SerializerMethodField()
    monto_total_pagos = serializers.SerializerMethodField()
    
    class Meta:
        model = Caja
        fields = [
            'id', 'usuario', 'usuario_detail', 'fecha_apertura', 'fecha_cierre',
            'monto_inicial', 'estado', 'monto_total_pagos'
        ]
        read_only_fields = ['id', 'fecha_apertura', 'fecha_cierre']
    
    def get_usuario_detail(self, obj):
        return {
            'id': obj.usuario.id,
            'username': obj.usuario.username,
            'nombre': f"{obj.usuario.first_name} {obj.usuario.last_name}"
        }
    
    def get_monto_total_pagos(self, obj):
        """Calcula el total de montos entregados en esta caja"""
        total = obj.pagos.aggregate(
            total=serializers.Sum('monto_total_entregado')
        )['total'] or 0
        return float(total)
