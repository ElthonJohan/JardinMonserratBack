from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
import calendar
from datetime import date
from matriculas.models import Matricula
from .models import Deuda, ConceptoPago


@receiver(post_save, sender=Matricula)
def generar_cronograma_pagos(sender, instance, created, **kwargs):
    """
    Signal post_save para Matricula.
    Al crear una nueva matrícula, genera automáticamente:
    1. Deuda de CUOTA_INGRESO (solo para primera matrícula del estudiante)
    2. Deuda de MATRICULA (anual)
    3. Deudas de PENSION (marzo a diciembre, mes vencido)
    """
    if not created:
        return
    
    try:
        with transaction.atomic():
            anio_actual = instance.periodo_academico.anio
            alumno = instance.alumno
            
            # Verificar si es la primera matrícula del alumno
            es_primera_matricula = not Matricula.objects.filter(
                alumno=alumno
            ).exclude(id=instance.id).exists()
            
            # 1. GENERAR CUOTA DE INGRESO (solo si es primera matrícula)
            if es_primera_matricula:
                concepto_ingreso = ConceptoPago.objects.filter(
                    tipo='CUOTA_INGRESO',
                    activo=True
                ).first()
                
                if concepto_ingreso:
                    Deuda.objects.get_or_create(
                        alumno=alumno,
                        concepto=concepto_ingreso,
                        anio=anio_actual,
                        mes__isnull=True,  # La cuota de ingreso no tiene mes
                        defaults={
                            'monto_total': concepto_ingreso.monto_base,
                            'monto_pagado': 0.00,
                            'fecha_vencimiento': instance.fecha_matricula,
                            'estado': 'Pendiente'
                        }
                    )
            
            # 2. GENERAR MATRÍCULA (anual)
            concepto_matricula = ConceptoPago.objects.filter(
                tipo='MATRICULA',
                activo=True
            ).first()
            
            if concepto_matricula:
                Deuda.objects.get_or_create(
                    alumno=alumno,
                    concepto=concepto_matricula,
                    anio=anio_actual,
                    mes__isnull=True,
                    defaults={
                        'monto_total': concepto_matricula.monto_base,
                        'monto_pagado': 0.00,
                        'fecha_vencimiento': instance.fecha_matricula,
                        'estado': 'Pendiente'
                    }
                )
            
            # 3. GENERAR PENSIONES (Marzo a Diciembre)
            concepto_pension = ConceptoPago.objects.filter(
                tipo='PENSION',
                activo=True
            ).first()
            
            if concepto_pension:
                for mes_num in range(3, 13):  # Marzo (3) a Diciembre (12)
                    # Calcular el último día del mes (mes vencido)
                    _, ultimo_dia_mes = calendar.monthrange(anio_actual, mes_num)
                    fecha_vencimiento = date(anio_actual, mes_num, ultimo_dia_mes)
                    
                    # Usar get_or_create para evitar duplicados
                    Deuda.objects.get_or_create(
                        alumno=alumno,
                        concepto=concepto_pension,
                        mes=mes_num,
                        anio=anio_actual,
                        defaults={
                            'monto_total': concepto_pension.monto_base,
                            'monto_pagado': 0.00,
                            'fecha_vencimiento': fecha_vencimiento,
                            'estado': 'Pendiente'
                        }
                    )
    
    except Exception as e:
        # Log el error pero no romper el flujo de creación de matrícula
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error al generar cronograma de pagos para matrícula {instance.id}: {str(e)}")