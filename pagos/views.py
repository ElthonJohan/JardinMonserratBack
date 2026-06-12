from rest_framework import viewsets, filters, status, serializers
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, DjangoModelPermissions
from rest_framework.response import Response
from django.db import transaction
from django.utils import timezone
from django.db.models import Q, Sum, Count
from django_filters.rest_framework import DjangoFilterBackend

from .models import Pago, ConceptoPago, Deuda, Caja, PagoAsignacion, Banco
from estudiantes.models import Estudiante, ApoderadoEstudiante
from .serializers import (
    PagoSerializer, ConceptoPagoSerializer, DeudaSerializer,
    PagoPendienteSerializer,
    RechazarPagoSerializer,
    CajaSerializer, PagoAsignacionSerializer, PagoManualSerializer, RegistrarPagoSerializer, BancoSerializer, RegistrarPagoSerializer
)
# pagos/views.py

from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.utils import timezone


from notificaciones.models import Notificacion
from usuarios.models import Usuario


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
    ordering_fields = ['fecha_vencimiento', 'monto_total', 'estado', 'anio', 'id']
    ordering = ['-id']
    
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
    
    def get_serializer_class(self):
        if self.action == 'create':
            return PagoManualSerializer
        return PagoSerializer

    def perform_create(self, serializer):
        """
        Lógica de creación de Pago con asignación manual.
        - Si es un apoderado: Estado REGISTRADO, sin caja. Los saldos no se actualizan.
        - Si es administración: Estado APROBADO, asigna caja y validador. Los saldos se actualizan inmediatamente.
        """
        try:
            with transaction.atomic():
                # Extraemos el detalle de pagos validado por el serializer
                detalles_pago = serializer.validated_data.pop('detalles_pago', [])
                
                # Determinamos si el usuario es apoderado
                es_apoderado = hasattr(self.request.user, 'apoderado_rel') and self.request.user.apoderado_rel is not None
                
                if es_apoderado:
                    # Lógica para apoderados desde su casa
                    pago = serializer.save(
                        usuario_creador=self.request.user,
                        estado='REGISTRADO',
                        caja=None
                    )
                else:
                    # Lógica para administración (cajero, admin, etc)
                    caja_form = serializer.validated_data.get('caja')
                    pago = serializer.save(
                        usuario_creador=self.request.user,
                        estado='APROBADO',
                        caja=caja_form,
                        fecha_aprobacion=timezone.now(),
                        usuario_validador=self.request.user
                    )
                
                # Crear las asignaciones manualmente
                asignaciones = []
                for detalle in detalles_pago:
                    asignaciones.append(
                        PagoAsignacion(
                            pago=pago,
                            deuda_id=detalle['deuda_id'],
                            monto_aplicado=detalle['monto_asignado']
                        )
                    )
                
                # Guardar las asignaciones en bloque
                PagoAsignacion.objects.bulk_create(asignaciones)
                
                # Si el pago ya nace APROBADO, debemos actualizar los saldos inmediatamente
                if pago.estado == 'APROBADO':
                    # Recuperar las asignaciones desde la DB para tener la instancia de deuda correcta
                    for asignacion in pago.asignaciones.all():
                        asignacion.deuda.actualizar_estado()
                
        except Exception as e:
            raise serializers.ValidationError({"detail": str(e)})
            
    @action(detail=False, methods=['get'])
    def pendientes_aprobacion(self, request):
        """Lista pagos en estado REGISTRADO"""
        pagos = self.get_queryset().filter(estado='REGISTRADO')
        page = self.paginate_queryset(pagos)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(pagos, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def pendientes_count(self, request):
        """Devuelve la cantidad de pagos pendientes (REGISTRADO)"""
        count = self.get_queryset().filter(estado='REGISTRADO').count()
        return Response({"count": count})
            
    @action(detail=True, methods=['post'])
    def procesar_aprobacion(self, request, pk=None):
        """
        Procesa la aprobación o rechazo de un pago manual.
        Recibe JSON con: estado ('APROBADO', 'RECHAZADO'), caja_id (opcional), motivo_rechazo (opcional)
        """
        pago = self.get_object()
        estado_nuevo = request.data.get('estado')
        caja_id = request.data.get('caja_id')
        motivo_rechazo = request.data.get('motivo_rechazo')

        if pago.estado != 'REGISTRADO':
            return Response(
                {"detail": f"El pago no puede ser procesado porque su estado actual es {pago.estado}."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if estado_nuevo not in ['APROBADO', 'RECHAZADO']:
            return Response(
                {"detail": "Estado inválido. Debe ser APROBADO o RECHAZADO."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with transaction.atomic():
                from notificaciones.models import Notificacion
                
                if estado_nuevo == 'RECHAZADO':
                    if not motivo_rechazo:
                        return Response(
                            {"detail": "El motivo de rechazo es obligatorio."},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    
                    pago.estado = 'RECHAZADO'
                    pago.motivo_rechazo = motivo_rechazo
                    pago.usuario_validador = request.user
                    pago.save()
                    
                    # Intentar obtener el usuario creador o el usuario del apoderado principal del alumno
                    usuario_notif = pago.usuario_creador
                    if not usuario_notif:
                        from estudiantes.models import ApoderadoEstudiante
                        relacion = ApoderadoEstudiante.objects.filter(
                            estudiante=pago.alumno,
                            es_principal=True
                        ).select_related('apoderado').first()
                        if relacion and hasattr(relacion.apoderado, 'usuarios'):
                            usuario_notif = relacion.apoderado.usuarios.first()

                    if usuario_notif:
                        Notificacion.objects.create(
                            usuario=usuario_notif,
                            alumno=pago.alumno,
                            titulo="Pago Rechazado",
                            mensaje=f"Tu pago por S/{pago.monto_total_entregado} ha sido rechazado. Motivo: {motivo_rechazo}",
                            tipo='PAGO_RECHAZADO',
                            ruta='/intranet/pagos'
                        )

                elif estado_nuevo == 'APROBADO':
                    if not caja_id:
                        return Response(
                            {"detail": "Debe especificar una caja_id para aprobar el pago."},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                        
                    caja = Caja.objects.filter(id=caja_id, estado='Abierta').first()
                    if not caja:
                        return Response(
                            {"detail": "La caja especificada no existe o no está abierta."},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                        
                    pago.estado = 'APROBADO'
                    pago.caja = caja
                    pago.fecha_aprobacion = timezone.now()
                    pago.usuario_validador = request.user
                    pago.save()
                    
                    # Si el pago fue creado con deuda directa (flujo antiguo) y no tiene asignaciones, crearla
                    if pago.deuda and not pago.asignaciones.exists():
                        PagoAsignacion.objects.create(
                            pago=pago,
                            deuda=pago.deuda,
                            monto_aplicado=pago.monto_total_entregado
                        )
                    
                    # Actualizar saldo de cada deuda afectada
                    for asignacion in pago.asignaciones.all():
                        asignacion.deuda.actualizar_estado()
                        
                    # Intentar obtener el usuario creador o el usuario del apoderado principal del alumno
                    usuario_notif = pago.usuario_creador
                    if not usuario_notif:
                        from estudiantes.models import ApoderadoEstudiante
                        relacion = ApoderadoEstudiante.objects.filter(
                            estudiante=pago.alumno,
                            es_principal=True
                        ).select_related('apoderado').first()
                        if relacion and hasattr(relacion.apoderado, 'usuarios'):
                            usuario_notif = relacion.apoderado.usuarios.first()

                    if usuario_notif:
                        Notificacion.objects.create(
                            usuario=usuario_notif,
                            alumno=pago.alumno,
                            titulo="Pago Aprobado",
                            mensaje=f"Tu pago por S/{pago.monto_total_entregado} ha sido aprobado exitosamente.",
                            tipo='PAGO_APROBADO',
                            ruta='/intranet/pagos'
                        )

            return Response({"detail": f"Pago {estado_nuevo.lower()} exitosamente."}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
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
        
        # Obtener deudas pendientes/parciales del alumno, ordenadas por ID (orden de creación: Cuota -> Matrícula -> Pensiones)
        deudas_pendientes = Deuda.objects.filter(
            alumno=pago.alumno,
            estado__in=['Pendiente', 'Parcial']
        ).order_by('id')
        
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
        
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def parent_payment_dashboard(request):

    usuario = request.user

    apoderado = usuario.apoderado_rel

    if not apoderado:

        return Response({
            "total_pendiente": 0,
            "alumnos": []
        })

    alumnos = Estudiante.objects.filter(
        apoderados__apoderado=apoderado
    ).distinct()

    alumnos_data = []

    total_familiar = 0

    for alumno in alumnos:

        deudas = (
            Deuda.objects
            .filter(
                alumno=alumno,
                estado__in=[
                    'Pendiente',
                    'Parcial'
                ]
            )
            .select_related(
                'concepto'
            )
            .order_by(
                'id'
            )
        )

        pagos = (
            Pago.objects
            .filter(
                alumno=alumno
            )
            .order_by(
                '-fecha_pago'
            )[:5]
        )

        total_alumno = sum(
            d.saldo_pendiente
            for d in deudas
        )

        total_familiar += total_alumno

        # Calcular progreso financiero real (monto pagado / monto total de deudas activas)
        todas_deudas = Deuda.objects.filter(alumno=alumno).exclude(estado='Anulado')
        total_monto = sum(d.monto_total for d in todas_deudas)
        total_pagado = sum(d.monto_pagado for d in todas_deudas)
        
        porcentaje_progreso = 100.0
        if total_monto > 0:
            porcentaje_progreso = float((total_pagado / total_monto) * 100)

        alumnos_data.append({

            "id":
                alumno.id,

            "codigo":
                alumno.codigo_estudiante,

            "nombre":
                f"{alumno.nombres} "
                f"{alumno.apellidos}",

            "total_pendiente":
                float(total_alumno),
                
            "total_monto":
                float(total_monto),
                
            "total_pagado":
                float(total_pagado),
                
            "porcentaje_progreso":
                round(porcentaje_progreso, 2),

            "deudas":
                DeudaSerializer(
                    deudas,
                    many=True
                ).data,

            "pagos_recientes":
                PagoSerializer(
                    pagos,
                    many=True
                ).data
        })

    return Response({

        "apoderado_nombre":
            f"{apoderado.nombres} "
            f"{apoderado.apellidos}",

        "cantidad_hijos":
            alumnos.count(),

        "total_pendiente":
            float(total_familiar),

        "alumnos":
            alumnos_data
    })

class BancoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar bancos (CRUD).
    """
    queryset = Banco.objects.all()
    serializer_class = BancoSerializer
    permission_classes = [IsAuthenticated, DjangoModelPermissions]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['activo']
    search_fields = ['nombre', 'numero_cuenta', 'cci']
    ordering_fields = ['nombre', 'activo']
    ordering = ['nombre']
    pagination_class = None
    
class RegistrarPagoParentView(APIView):

    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):

        serializer = RegistrarPagoSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        deudas = serializer.validated_data['deudas']
        deuda = serializer.validated_data['deuda']
        alumno = deudas[0].alumno if deudas else None

        pago = Pago.objects.create(

            alumno=alumno,
            deuda=deuda,
            banco=serializer.validated_data.get('banco'),
            monto_total_entregado=
                serializer.validated_data['monto'],

            metodo_pago=
                serializer.validated_data['metodo_pago'],

            numero_operacion=
                serializer.validated_data.get(
                    'numero_operacion'
                ),

            comprobante_img=
                serializer.validated_data[
                    'comprobante_img'
                ],

            estado='REGISTRADO'
        )

        # Crear asignaciones para las deudas en lote (bulk_create no dispara actualizar_estado,
        # lo cual es correcto porque el pago está en estado REGISTRADO)
        monto_disponible = serializer.validated_data['monto']
        asignaciones = []
        for d in deudas:
            if monto_disponible <= 0:
                break
            saldo_pendiente = d.saldo_pendiente
            monto_a_asignar = min(monto_disponible, saldo_pendiente)
            asignaciones.append(
                PagoAsignacion(
                    pago=pago,
                    deuda=d,
                    monto_aplicado=monto_a_asignar
                )
            )
            monto_disponible -= monto_a_asignar

        if asignaciones:
            PagoAsignacion.objects.bulk_create(asignaciones)

        admins = Usuario.objects.filter(
            is_staff=True
        )

        for admin in admins:

            Notificacion.objects.create(

                usuario=admin,

                alumno=alumno,

                tipo='PAGO_REGISTRADO',

                titulo='Nuevo pago registrado',

                mensaje=(
                    f'Se registró un pago '
                    f'de S/ {pago.monto_total_entregado} '
                    f'para {alumno}'
                ),
                ruta=f'/pagos?tab=validacion&alumnoId={alumno.id}'
            )

        return Response(
            {
                "message":
                    "Pago registrado correctamente. "
                    "Pendiente de validación.",

                "pago_id":
                    pago.id
            },
            status=status.HTTP_201_CREATED
        )
        
class PagosPendientesView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        pagos = (
            Pago.objects
            .filter(
                estado='REGISTRADO'
            )
            .select_related(
                'alumno',
                'deuda',
                'deuda__concepto'
            )
            .order_by(
                '-fecha_pago'
            )
        )

        serializer = (
            PagoPendienteSerializer(
                pagos,
                many=True
            )
        )

        return Response(
            serializer.data
        )
        
class AprobarPagoView(APIView):

    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, pago_id):

        pago = get_object_or_404(
            Pago.objects.select_related(
                'alumno',
                'deuda'
            ),
            id=pago_id
        )

        if pago.estado != 'REGISTRADO':

            return Response(
                {
                    "message":
                    "El pago ya fue procesado."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        if not pago.deuda:

            return Response(
                {
                    "message":
                    "El pago no tiene deuda asociada."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        if (
            pago.monto_total_entregado >
            pago.deuda.saldo_pendiente
        ):

            return Response(
                {
                    "message":
                    "El monto excede la deuda pendiente."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        PagoAsignacion.objects.create(
            pago=pago,
            deuda=pago.deuda,
            monto_aplicado=
                pago.monto_total_entregado
        )

        caja = Caja.objects.filter(
            estado='Abierta'
        ).first()

        if not caja:

            return Response(
                {
                    "message":
                    "No existe una caja abierta para registrar el pago."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        pago.caja = caja

        pago.estado = 'APROBADO'
        pago.fecha_aprobacion = timezone.now()
        pago.usuario_validador = request.user
        pago.save()

        # Notificación al apoderado
        relacion = (
            ApoderadoEstudiante.objects
            .filter(
                estudiante=pago.alumno,
                es_principal=True
            )
            .select_related(
                'apoderado'
            )
            .first()
        )

        if (
            relacion and
            hasattr(relacion.apoderado, 'usuarios')
        ):

            usuario_apoderado = (
                relacion.apoderado.usuarios.first()
            )

            if usuario_apoderado:

                Notificacion.objects.create(
                    usuario=usuario_apoderado,
                    alumno=pago.alumno,
                    tipo='PAGO_APROBADO',
                    titulo='Pago aprobado',
                    mensaje=(
                        f'Su pago de '
                        f'S/ {pago.monto_total_entregado} '
                        f'ha sido aprobado.'
                    ),
                    ruta='/intranet/pagos'
                )

        return Response(
            {
                "message":
                "Pago aprobado exitosamente."
            }
        )

class RechazarPagoView(APIView):

    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(
        self,
        request,
        pago_id
    ):

        serializer = (
            RechazarPagoSerializer(
                data=request.data
            )
        )

        serializer.is_valid(
            raise_exception=True
        )

        pago = get_object_or_404(
            Pago.objects.select_related(
                'alumno'
            ),
            id=pago_id
        )

        if pago.estado != 'REGISTRADO':

            return Response(
                {
                    "message":
                    "El pago ya fue procesado."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        pago.estado = 'RECHAZADO'

        pago.motivo_rechazo = (
            serializer.validated_data[
                'motivo'
            ]
        )

        pago.usuario_validador = (
            request.user
        )

        pago.fecha_aprobacion = (
            timezone.now()
        )

        pago.save()

        # Buscar apoderado principal
        relacion = (
            ApoderadoEstudiante.objects
            .filter(
                estudiante=pago.alumno,
                es_principal=True
            )
            .select_related(
                'apoderado'
            )
            .first()
        )

        if relacion:

            usuario_apoderado = (
                relacion.apoderado
                .usuarios
                .first()
            )

            if usuario_apoderado:

                Notificacion.objects.create(

                    usuario=usuario_apoderado,

                    alumno=pago.alumno,

                    tipo='PAGO_RECHAZADO',

                    titulo='Pago rechazado',

                    mensaje=(
                        f'Su pago de '
                        f'S/ {pago.monto_total_entregado} '
                        f'fue rechazado. '
                        f'Motivo: '
                        f'{pago.motivo_rechazo}'
                    ),
                    ruta='/intranet/pagos'
                )

        return Response(
            {
                "message":
                "Pago rechazado correctamente."
            },
            status=status.HTTP_200_OK
        )
        
# pagos/views.py

class PagosPendientesView(
    APIView
):

    permission_classes = [
        IsAuthenticated
    ]

    def get(
        self,
        request
    ):

        pagos = (
            Pago.objects
            .filter(
                estado='REGISTRADO'
            )
            .select_related(
                'alumno',
                'deuda',
                'deuda__concepto'
            )
            .order_by(
                '-fecha_pago'
            )
        )

        serializer = (
            PagoPendienteSerializer(
                pagos,
                many=True,
                context={
                    'request':
                    request
                }
            )
        )

        return Response(
            serializer.data
        )