from rest_framework import serializers
from .models import Pago, ConceptoPago, Deuda, Caja, PagoAsignacion, Banco
from estudiantes.models import Estudiante
from django.utils import timezone
from django.db.models import Sum  # Importar esto al inicio del archivo


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
            'detalle_adicional', 'monto_total', 'monto_pagado', 'saldo_pendiente', 'mes', 'anio',
            'fecha_vencimiento', 'estado'
        ]
        read_only_fields = ['id', 'monto_pagado']
    
    def get_saldo_pendiente(self, obj):
        return obj.saldo_pendiente

    def validate(self, data):
        concepto = data.get('concepto')
        
        if not concepto and self.instance:
            concepto = self.instance.concepto
            
        monto_total = data.get('monto_total')
        if monto_total is None and concepto:
            if not self.instance or 'monto_total' in data:
                data['monto_total'] = concepto.monto_base

        if concepto and concepto.tipo == 'OTROS':
            detalle = data.get('detalle_adicional')
            if not detalle and (not self.instance or 'detalle_adicional' in data):
                raise serializers.ValidationError({"detalle_adicional": "Este campo es obligatorio para cargos de tipo OTROS."})
        
        if concepto and concepto.tipo in ['PENSION', 'MATRICULA']:
            alumno = data.get('alumno', self.instance.alumno if self.instance else None)
            mes = data.get('mes', self.instance.mes if self.instance else None)
            anio = data.get('anio', self.instance.anio if self.instance else None)
            
            qs = Deuda.objects.filter(
                alumno=alumno,
                concepto=concepto,
                mes=mes,
                anio=anio
            )
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
                
            if qs.exists():
                raise serializers.ValidationError("Ya existe una deuda registrada para este alumno, concepto, mes y año.")
                
        return data


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


class BancoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Banco
        fields = ['id', 'nombre', 'numero_cuenta', 'cci', 'activo']


class PagoSerializer(serializers.ModelSerializer):
    """Serializer para pagos (cabecera) con validaciones de seguridad"""
    alumno_detail = EstudianteMiniSerializer(source='alumno', read_only=True)
    usuario_detail = serializers.SerializerMethodField()
    asignaciones = PagoAsignacionSerializer(many=True, read_only=True)
    banco_detail = BancoSerializer(source='banco', read_only=True)
    monto_aplicado = serializers.SerializerMethodField()
    
    class Meta:
        model = Pago
        fields = [
            'id', 'alumno', 'alumno_detail', 'caja', 'monto_total_entregado',
            'monto_aplicado', 'fecha_pago', 'metodo_pago', 'numero_operacion', 
            'comprobante_img', 'usuario_creador', 'usuario_validador', 'usuario_detail', 'observaciones', 
            'asignaciones', 'banco', 'banco_detail', 'estado', 'fecha_aprobacion', 'motivo_rechazo'
        ]
        read_only_fields = ['id', 'fecha_pago', 'usuario_creador', 'usuario_validador', 'asignaciones', 'monto_aplicado']
    
    def validate_numero_operacion(self, value):
        """Valida que numero_operacion sea unico (excepto para Efectivo)"""
        metodo_pago = self.initial_data.get('metodo_pago')
        banco = self.initial_data.get('banco')
        
        if metodo_pago == 'Efectivo':
            return value
        
        if not value:
            raise serializers.ValidationError(
                "El numero de operacion es obligatorio para pagos no en efectivo."
            )
        
        # Validacion delegada al clean() del modelo para el unique_together
        return value
    
    def validate(self, data):
        """Validaciones a nivel de objeto"""
        request = self.context.get('request')
        
        if data.get('monto_total_entregado', 0) <= 0:
            raise serializers.ValidationError({
                'monto_total_entregado': 'El monto debe ser mayor a cero.'
            })
        
        return data
    
    def get_usuario_detail(self, obj):
        if obj.usuario_creador:
            return {
                'id': obj.usuario_creador.id,
                'username': obj.usuario_creador.username,
                'nombre': f"{obj.usuario_creador.first_name} {obj.usuario_creador.last_name}"
            }
        return None
    
    def get_monto_aplicado(self, obj):
        """Suma del monto_aplicado de todas las asignaciones"""
        total = obj.asignaciones.aggregate(
                    total=Sum('monto_aplicado')
        )['total'] or 0
        return float(total)


class PagoAsignacionCreateSerializer(serializers.Serializer):
    deuda_id = serializers.IntegerField()
    monto_asignado = serializers.DecimalField(max_digits=10, decimal_places=2)

class PagoManualSerializer(serializers.ModelSerializer):
    detalles_pago = PagoAsignacionCreateSerializer(many=True, write_only=True)
    
    class Meta:
        model = Pago
        fields = [
            'alumno', 'caja', 'monto_total_entregado', 'metodo_pago',
            'banco', 'numero_operacion', 'comprobante_img', 'observaciones',
            'detalles_pago'
        ]

    def validate(self, data):
        monto_total_entregado = data.get('monto_total_entregado', 0)
        detalles_pago = data.get('detalles_pago', [])
        
        if not detalles_pago:
            raise serializers.ValidationError({
                "detalles_pago": "Debe incluir al menos una deuda a pagar."
            })
            
        suma_detalles = sum(detalle['monto_asignado'] for detalle in detalles_pago)
        if suma_detalles != monto_total_entregado:
            raise serializers.ValidationError({
                "detalles_pago": f"La suma de los montos asignados ({suma_detalles}) no cuadra con el monto total entregado ({monto_total_entregado})."
            })
            
        return data


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
            total=Sum('monto_total_entregado')
        )['total'] or 0
        return float(total)
