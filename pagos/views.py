from rest_framework import viewsets, filters, status, serializers
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, DjangoModelPermissions
from rest_framework.response import Response
from django.db import transaction
from django.utils import timezone
from django.db.models import Q, Sum, Count
from django_filters.rest_framework import DjangoFilterBackend

from .models import Pago, ConceptoPago, Deuda, Caja, PagoAsignacion
from .serializers import (
    PagoSerializer, ConceptoPagoSerializer, DeudaSerializer,
    CajaSerializer, PagoAsignacionSerializer
)


class ConceptoPagoViewSet(viewsets.ModelViewSet):
    """ViewSet para conceptos de pago"""
    queryset = ConceptoPago.objects.all()
    serializer_class = ConceptoPagoSerializer
    permission_classes = [IsAuthenticated, DjangoModelPermissions]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['activo', 'tipo']
    search_fields = ['nombre', 'tipo']
    ordering_fields = ['nombre', 'monto_base', 'tipo']
    ordering = ['nombre']


class DeudaViewSet(viewsets.ModelViewSet):
    """ViewSet para deudas con filtros inteligentes por alumno y estado"""
    serializer_class = DeudaSerializer
    permission_classes = [IsAuthenticated, DjangoModelPermissions]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['alumno', 'estado', 'anio']
    search_fields = ['alumno__nombres', 'alumno__apellidos', 'concepto__nombre']
    ordering_fields = ['fecha_vencimiento', 'monto_total', 'estado', 'anio']
    ordering = ['fecha_vencimiento']
    
    def get_queryset(self):
        """
        Filtrado inteligente:
        - Por defecto: EXCLUYE deudas con estado='Pagado'
        - Parametro ?incluir_pagadas=true para mostrar todas
        """
        queryset = Deuda.objects.all()
        
        # Por defecto, NO mostrar deudas pagadas
        incluir_pagadas = self.request.query_params.get('incluir_pagadas', 'false').lower() == 'true'
        
        if not incluir_pagadas:
            queryset = queryset.exclude(estado='Pagado')
        
        return queryset


class PagoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para pagos con lógica FIFO de abono multinivel.
    Requiere que el usuario tenga una Caja abierta.
    """
    queryset = Pago.objects.all()
    serializer_class = PagoSerializer
    permission_classes = [IsAuthenticated, DjangoModelPermissions]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['alumno', 'metodo_pago']
    search_fields = ['alumno__nombres', 'alumno__apellidos', 'numero_operacion']
    ordering_fields = ['fecha_pago', 'monto_total_entregado']
    ordering = ['-fecha_pago']
    
    def perform_create(self, serializer):
        """
        Lógica de creación de Pago con abono FIFO:
        1. Valida que el usuario tenga una Caja abierta
        2. Reparte el monto entre las deudas pendientes (FIFO por fecha_vencimiento)
        3. Crea PagoAsignacion para cada deuda afectada
        """
        # Validar que el usuario tenga una Caja abierta
        caja_abierta = Caja.objects.filter(
            usuario=self.request.user,
            estado='Abierta'
        ).first()
        
        if not caja_abierta:
            raise serializers.ValidationError(
                {"detail": "No tienes una Caja abierta. Abre una caja antes de registrar pagos."}
            )
        
        try:
            with transaction.atomic():
                # Guardar el pago con el usuario y la caja
                pago = serializer.save(
                    usuario_registro=self.request.user,
                    caja=caja_abierta
                )
                
                # Aplicar la lógica FIFO de abono multinivel
                self._aplicar_abono_fifo(pago)
        
        except Exception as e:
            raise serializers.ValidationError({"detail": str(e)})
    
    def _aplicar_abono_fifo(self, pago):
        """
        Implementa el algoritmo FIFO automatico:
        1. Obtiene las deudas pendientes/parciales del alumno
        2. Las ordena por fecha_vencimiento ASC (mas antiguas primero)
        3. Reparte el monto_total_entregado entre ellas secuencialmente
        4. Crea PagoAsignacion para cada deuda afectada
        5. Si hay sobrante, se mantiene en el Pago sin asignacion (para futuras aplicaciones)
        """
        monto_disponible = pago.monto_total_entregado
        asignaciones_creadas = 0
        
        # Obtener deudas pendientes/parciales del alumno, ordenadas por fecha_vencimiento (ASC)
        deudas_pendientes = Deuda.objects.filter(
            alumno=pago.alumno,
            estado__in=['Pendiente', 'Parcial']
        ).order_by('fecha_vencimiento')
        
        for deuda in deudas_pendientes:
            if monto_disponible <= 0:
                break
            
            # Calcular cuanto falta por pagar en esta deuda
            saldo_pendiente = deuda.saldo_pendiente
            
            if saldo_pendiente <= 0:
                # Deuda ya esta completa, continuar a la siguiente
                continue
            
            # Aplicar la menor cantidad: disponible o saldo_pendiente
            monto_a_aplicar = min(monto_disponible, saldo_pendiente)
            
            # Crear la asignacion
            PagoAsignacion.objects.create(
                pago=pago,
                deuda=deuda,
                monto_aplicado=monto_a_aplicar
            )
            
            # Reducir el monto disponible para la siguiente deuda
            monto_disponible -= monto_a_aplicar
            asignaciones_creadas += 1
        
        # Si hay sobrante, se mantiene en pago.monto_total_entregado sin asignacion
        if monto_disponible > 0:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(
                f"Pago {pago.id}: Hay sobrante de S/ {monto_disponible} sin asignar. "
                f"Se crearon {asignaciones_creadas} asignaciones."
            )
    
    def retrieve(self, request, *args, **kwargs):
        """Obtiene un pago específico con sus asignaciones"""
        pago = self.get_object()
        serializer = self.get_serializer(pago)
        return Response(serializer.data)


class CajaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para control de cajas diarias.
    Permite apertura, cierre y consulta del estado.
    """
    queryset = Caja.objects.all()
    serializer_class = CajaSerializer
    permission_classes = [IsAuthenticated, DjangoModelPermissions]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['usuario', 'estado']
    ordering_fields = ['fecha_apertura', 'fecha_cierre']
    ordering = ['-fecha_apertura']
    
    def get_queryset(self):
        """Por defecto, mostrar cajas del usuario actual"""
        return Caja.objects.filter(usuario=self.request.user)
    
    @action(detail=False, methods=['get'])
    def mi_estado(self, request):
        """
        Acción para obtener el estado actual de la caja del usuario.
        Retorna la caja abierta si existe, o un estado cerrado si no.
        """
        caja_abierta = Caja.objects.filter(
            usuario=request.user,
            estado='Abierta'
        ).first()
        
        if caja_abierta:
            serializer = self.get_serializer(caja_abierta)
            return Response({
                'abierta': True,
                'caja': serializer.data
            })
        else:
            return Response({
                'abierta': False,
                'caja': None,
                'mensaje': 'No tienes una caja abierta actualmente.'
            })
    
    @action(detail=True, methods=['post'])
    def cerrar_caja(self, request, pk=None):
        """
        Accion para cerrar una caja:
        - Cambia estado a 'Cerrada'
        - Registra fecha_cierre
        - Calcula monto_final sumando todos los monto_total_entregado de pagos
        """
        caja = self.get_object()
        
        # Validar que sea del usuario actual
        if caja.usuario != request.user:
            return Response(
                {"detail": "No tienes permiso para cerrar esta caja."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Validar que este abierta
        if caja.estado != 'Abierta':
            return Response(
                {"detail": "Esta caja ya esta cerrada."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Calcular monto total recaudado
        monto_final = caja.pagos.aggregate(
            total=Sum('monto_total_entregado')
        )['total'] or 0
        
        # Cerrar la caja
        caja.fecha_cierre = timezone.now()
        caja.estado = 'Cerrada'
        caja.save()
        
        serializer = self.get_serializer(caja)
        return Response({
            'mensaje': 'Caja cerrada exitosamente.',
            'caja': serializer.data,
            'monto_final': float(monto_final),
            'resumen': {
                'monto_inicial': float(caja.monto_inicial),
                'monto_recaudado': float(monto_final),
                'total_con_inicial': float(caja.monto_inicial + monto_final)
            }
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['get'])
    def resumen_ingresos(self, request, pk=None):
        """
        Accion para obtener resumen de ingresos de una caja:
        - Total recaudado agrupado por metodo_pago
        - Count de transacciones por metodo
        - Datos de apertura y cierre
        """
        caja = self.get_object()
        
        # Validar que sea del usuario actual
        if caja.usuario != request.user:
            return Response(
                {"detail": "No tienes permiso para ver esta caja."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Obtener resumen de ingresos por metodo de pago
        resumen = caja.pagos.values('metodo_pago').annotate(
            total=Sum('monto_total_entregado'),
            cantidad=Count('id')
        ).order_by('-total')
        
        # Convertir QuerySet a lista con valores numericos
        resumen_list = [
            {
                'metodo_pago': item['metodo_pago'],
                'total': float(item['total']),
                'cantidad': item['cantidad']
            }
            for item in resumen
        ]
        
        # Calcular totales generales
        total_general = caja.pagos.aggregate(
            total=Sum('monto_total_entregado')
        )['total'] or 0
        
        return Response({
            'caja_id': caja.id,
            'usuario': caja.usuario.username,
            'fecha_apertura': caja.fecha_apertura,
            'fecha_cierre': caja.fecha_cierre,
            'estado': caja.estado,
            'monto_inicial': float(caja.monto_inicial),
            'resumen_por_metodo': resumen_list,
            'total_recaudado': float(total_general),
            'cantidad_pagos': caja.pagos.count(),
            'total_con_inicial': float(caja.monto_inicial + total_general)
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'])
    def abrir_caja(self, request):
        """
        Acción para abrir una nueva caja.
        Si ya existe una caja abierta, retorna error.
        """
        # Verificar que no haya una caja abierta
        caja_existente = Caja.objects.filter(
            usuario=request.user,
            estado='Abierta'
        ).first()
        
        if caja_existente:
            return Response(
                {"detail": "Ya tienes una caja abierta."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Crear nueva caja
        monto_inicial = request.data.get('monto_inicial', 0.00)
        
        caja = Caja.objects.create(
            usuario=request.user,
            monto_inicial=monto_inicial,
            estado='Abierta'
        )
        
        serializer = self.get_serializer(caja)
        return Response({
            'mensaje': 'Caja abierta exitosamente.',
            'caja': serializer.data
        }, status=status.HTTP_201_CREATED)
