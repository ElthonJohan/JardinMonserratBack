from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from estudiantes.models import Estudiante
from matriculas.models import Matricula
from pagos.models import Deuda, Pago
from django.db.models import Sum, Count, F, Value, CharField
from django.db.models.functions import Concat
from django.utils import timezone
import datetime

class DashboardStatsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        hoy = timezone.now()
        
        # Permitir filtrar por año desde frontend, por defecto el actual
        anio_filtro = request.query_params.get('anio', hoy.year)
        try:
            anio_filtro = int(anio_filtro)
        except ValueError:
            anio_filtro = hoy.year

        # --- 1. KPIs Generales ---
        total_alumnos_activos = Matricula.objects.filter(estado='Activa', anio=anio_filtro).values('alumno').distinct().count()
        matriculas_anio = Matricula.objects.filter(anio=anio_filtro).count()

        deudas_pendientes = Deuda.objects.filter(estado__in=['Pendiente', 'Parcial'])
        pagos_pendientes_cantidad = deudas_pendientes.count()
        
        monto_calculado = deudas_pendientes.aggregate(
            total=Sum(F('monto_total') - F('monto_pagado'))
        )['total']
        pagos_pendientes_monto = float(monto_calculado) if monto_calculado else 0.0

        # --- 2. Recaudación Mes Actual vs Mes Anterior ---
        mes_actual = hoy.month
        anio_actual_mes = hoy.year
        mes_anterior = 12 if mes_actual == 1 else mes_actual - 1
        anio_anterior_mes = anio_actual_mes - 1 if mes_actual == 1 else anio_actual_mes

        recaudacion_actual = Pago.objects.filter(
            fecha_pago__year=anio_actual_mes, fecha_pago__month=mes_actual
        ).aggregate(total=Sum('monto_total_entregado'))['total'] or 0.0

        recaudacion_anterior = Pago.objects.filter(
            fecha_pago__year=anio_anterior_mes, fecha_pago__month=mes_anterior
        ).aggregate(total=Sum('monto_total_entregado'))['total'] or 0.0

        # --- 3. Distribución por Aulas (Año Seleccionado) ---
        distribucion_aulas = Matricula.objects.filter(anio=anio_filtro, estado='Activa').values(
            nombre_aula=F('aula__nombre'),
            capacidad=F('aula__capacidad')
        ).annotate(
            total=Count('id')
        ).order_by('-total')

        # --- 4. Estado de Matrículas (Desglose) ---
        estado_matriculas = Matricula.objects.filter(anio=anio_filtro).values('estado').annotate(
            total=Count('id')
        )

        # --- 5. Top 5 Alumnos con Mayores Deudas ---
        top_deudores = Deuda.objects.filter(estado__in=['Pendiente', 'Parcial']).annotate(
            nombre_completo=Concat('alumno__nombres', Value(' '), 'alumno__apellidos', output_field=CharField())
        ).values('alumno__id', 'nombre_completo').annotate(
            deuda_total=Sum(F('monto_total') - F('monto_pagado'))
        ).order_by('-deuda_total')[:5]

        # Serialización de la respuesta
        return Response({
            "kpis": {
                "total_alumnos_activos": total_alumnos_activos,
                "matriculas_anio": matriculas_anio,
                "pagos_pendientes_cantidad": pagos_pendientes_cantidad,
                "pagos_pendientes_monto": pagos_pendientes_monto,
                "recaudacion_actual": float(recaudacion_actual),
                "recaudacion_anterior": float(recaudacion_anterior)
            },
            "distribucion_aulas": list(distribucion_aulas),
            "estado_matriculas": list(estado_matriculas),
            "top_deudores": list(top_deudores)
        })
