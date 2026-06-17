# pagos/tests/test_signals.py
import pytest
from decimal import Decimal
from datetime import date
from django.db import IntegrityError

from pagos.models import Deuda, ConceptoPago
from matriculas.models import Matricula, PeriodoAcademico
from estudiantes.models import Estudiante, Apoderado, ApoderadoEstudiante, Aula


@pytest.mark.django_db
class TestGenerarCronogramaPagos:
    """Pruebas para la señal que genera el cronograma de pagos al matricular"""

    @pytest.fixture
    def setup_matricula_data(self):
        """Configuración base para pruebas de matrícula"""
        # Crear aula
        aula = Aula.objects.create(
            nombre="3 años",
            capacidad=20
        )
        
        # Crear apoderado
        apoderado = Apoderado.objects.create(
            nombres="Carlos",
            apellidos="Gómez",
            dni="12345678",
            telefono="999888777",
            email="carlos@example.com",
            direccion="Calle 123"
        )
        
        # Crear estudiante (SIN apoderado directo)
        estudiante = Estudiante.objects.create(
            nombres="Luis",
            apellidos="Gómez",
            fecha_nacimiento=date(2020, 5, 15),
            dni="87654321"
        )
        
        # Crear relación Apoderado-Estudiante
        ApoderadoEstudiante.objects.create(
            apoderado=apoderado,
            estudiante=estudiante,
            tipo_relacion="PADRE",
            es_principal=True
        )
        
        # Crear período académico
        periodo = PeriodoAcademico.objects.create(
            nombre="2026-1",
            anio=2026,
            fecha_inicio=date(2026, 3, 1),
            fecha_fin=date(2026, 12, 31)
        )
        
        # Crear conceptos de pago necesarios
        concepto_ingreso = ConceptoPago.objects.create(
            nombre="Cuota de Ingreso",
            tipo="CUOTA_INGRESO",
            monto_base=Decimal("200.00"),
            activo=True
        )
        
        # Usar nombres únicos para evitar IntegrityError si ya existe
        concepto_matricula = ConceptoPago.objects.create(
            nombre="Matrícula Anual",
            tipo="MATRICULA",
            monto_base=Decimal("300.00"),
            activo=True
        )
        
        concepto_pension = ConceptoPago.objects.create(
            nombre="Pensión Mensual",
            tipo="PENSION",
            monto_base=Decimal("500.00"),
            activo=True
        )
        
        return {
            'estudiante': estudiante,
            'periodo': periodo,
            'apoderado': apoderado,
            'aula': aula,
            'concepto_ingreso': concepto_ingreso,
            'concepto_matricula': concepto_matricula,
            'concepto_pension': concepto_pension
        }

    def test_generar_cronograma_primera_matricula(self, setup_matricula_data):
        """Prueba que al crear la primera matrícula se generen todas las deudas"""
        data = setup_matricula_data
        estudiante = data['estudiante']
        periodo = data['periodo']
        aula = data['aula']
        
        # Crear matrícula (esto dispara la señal)
        matricula = Matricula.objects.create(
            alumno=estudiante,
            periodo_academico=periodo,
            aula=aula,
            fecha_matricula=date(2026, 3, 1),
            estado='Activa'
        )
        
        # Verificar deudas generadas
        deudas = Deuda.objects.filter(alumno=estudiante)
        
        # 1 Cuota Ingreso + 1 Matrícula + 10 Pensiones (Marzo-Diciembre) = 12 deudas
        assert deudas.count() == 12
        
        # Verificar Cuota de Ingreso
        deuda_ingreso = deudas.filter(concepto__tipo='CUOTA_INGRESO').first()
        assert deuda_ingreso is not None
        assert deuda_ingreso.monto_total == Decimal("200.00")
        assert deuda_ingreso.estado == "Pendiente"
        assert deuda_ingreso.mes is None  # No tiene mes
        assert deuda_ingreso.anio == 2026
        
        # Verificar Matrícula
        deuda_matricula = deudas.filter(concepto__tipo='MATRICULA').first()
        assert deuda_matricula is not None
        assert deuda_matricula.monto_total == Decimal("300.00")
        assert deuda_matricula.estado == "Pendiente"
        assert deuda_matricula.mes is None
        
        # Verificar Pensiones (10 meses: Marzo a Diciembre)
        deudas_pension = deudas.filter(concepto__tipo='PENSION')
        assert deudas_pension.count() == 10
        
        # Verificar que todos los meses están cubiertos
        meses = sorted(deudas_pension.values_list('mes', flat=True))
        meses_esperados = list(range(3, 13))  # 3 a 12
        assert meses == meses_esperados
        
        # Verificar montos de pensiones
        for deuda in deudas_pension:
            assert deuda.monto_total == Decimal("500.00")
            assert deuda.estado == "Pendiente"
            assert deuda.anio == 2026

    def test_no_genera_cuota_ingreso_en_segunda_matricula(self, setup_matricula_data):
        """Prueba que NO se genere Cuota de Ingreso en matrículas subsecuentes"""
        data = setup_matricula_data
        estudiante = data['estudiante']
        periodo = data['periodo']
        aula = data['aula']
        
        # Primera matrícula
        matricula1 = Matricula.objects.create(
            alumno=estudiante,
            periodo_academico=periodo,
            aula=aula,
            fecha_matricula=date(2026, 3, 1),
            estado='Activa'
        )
        
        # Crear nuevo período para segunda matrícula
        periodo2 = PeriodoAcademico.objects.create(
            nombre="2027-1",
            anio=2027,
            fecha_inicio=date(2027, 3, 1),
            fecha_fin=date(2027, 12, 31)
        )
        
        # Segunda matrícula (mismo estudiante)
        matricula2 = Matricula.objects.create(
            alumno=estudiante,
            periodo_academico=periodo2,
            aula=aula,
            fecha_matricula=date(2027, 3, 1),
            estado='Activa'
        )
        
        # Verificar deudas
        deudas_2026 = Deuda.objects.filter(alumno=estudiante, anio=2026)
        deudas_2027 = Deuda.objects.filter(alumno=estudiante, anio=2027)
        
        # 2026: 1 Ingreso + 1 Matrícula + 10 Pensiones = 12
        assert deudas_2026.count() == 12
        
        # 2027: 1 Matrícula + 10 Pensiones (SIN Cuota Ingreso) = 11
        assert deudas_2027.count() == 11
        
        # Verificar que NO hay Cuota de Ingreso en 2027
        deuda_ingreso_2027 = deudas_2027.filter(concepto__tipo='CUOTA_INGRESO').first()
        assert deuda_ingreso_2027 is None

    def test_genera_cronograma_sin_conceptos_activos(self, setup_matricula_data):
        """Prueba que no genere deudas si los conceptos no están activos"""
        data = setup_matricula_data
        
        # Desactivar conceptos
        data['concepto_ingreso'].activo = False
        data['concepto_ingreso'].save()
        data['concepto_matricula'].activo = False
        data['concepto_matricula'].save()
        data['concepto_pension'].activo = False
        data['concepto_pension'].save()
        
        # Crear matrícula
        matricula = Matricula.objects.create(
            alumno=data['estudiante'],
            periodo_academico=data['periodo'],
            aula=data['aula'],
            fecha_matricula=date(2026, 3, 1),
            estado='Activa'
        )
        
        # No debería generar ninguna deuda
        deudas = Deuda.objects.filter(alumno=data['estudiante'])
        assert deudas.count() == 0

    def test_generar_cronograma_con_fechas_correctas(self, setup_matricula_data):
        """Prueba que las fechas de vencimiento sean correctas (último día del mes)"""
        data = setup_matricula_data
        estudiante = data['estudiante']
        periodo = data['periodo']
        aula = data['aula']
        
        matricula = Matricula.objects.create(
            alumno=estudiante,
            periodo_academico=periodo,
            aula=aula,
            fecha_matricula=date(2026, 3, 1),
            estado='Activa'
        )
        
        # Verificar fechas de vencimiento de pensiones
        deudas_pension = Deuda.objects.filter(
            alumno=estudiante,
            concepto__tipo='PENSION'
        ).order_by('mes')
        
        # Marzo -> 31/03/2026
        assert deudas_pension[0].fecha_vencimiento == date(2026, 3, 31)
        
        # Abril -> 30/04/2026
        assert deudas_pension[1].fecha_vencimiento == date(2026, 4, 30)
        
        # Mayo -> 31/05/2026
        assert deudas_pension[2].fecha_vencimiento == date(2026, 5, 31)
        
        # Diciembre -> 31/12/2026
        assert deudas_pension[9].fecha_vencimiento == date(2026, 12, 31)

    def test_generar_cronograma_con_periodo_diferente(self, setup_matricula_data):
        """Prueba que el cronograma se adapte al año del período académico"""
        data = setup_matricula_data
        
        # Crear período para 2027
        periodo_2027 = PeriodoAcademico.objects.create(
            nombre="2027-1",
            anio=2027,
            fecha_inicio=date(2027, 3, 1),
            fecha_fin=date(2027, 12, 31)
        )
        
        # Crear matrícula en 2027
        matricula = Matricula.objects.create(
            alumno=data['estudiante'],
            periodo_academico=periodo_2027,
            aula=data['aula'],
            fecha_matricula=date(2027, 3, 1),
            estado='Activa'
        )
        
        # Verificar que todas las deudas sean de 2027
        deudas = Deuda.objects.filter(alumno=data['estudiante'])
        for deuda in deudas:
            assert deuda.anio == 2027

    def test_no_duplica_deudas_si_ya_existen(self, setup_matricula_data):
        """Prueba que no se dupliquen deudas si ya existen"""
        data = setup_matricula_data
        estudiante = data['estudiante']
        periodo = data['periodo']
        aula = data['aula']
        
        # Primera matrícula
        matricula1 = Matricula.objects.create(
            alumno=estudiante,
            periodo_academico=periodo,
            aula=aula,
            fecha_matricula=date(2026, 3, 1),
            estado='Activa'
        )
        
        deudas_iniciales = Deuda.objects.filter(alumno=estudiante).count()
        
        from django.db import transaction
        # Intentar crear otra matrícula en el mismo período
        # Nota: Ajusta según las restricciones de tu modelo Matricula
        try:
            with transaction.atomic():
                matricula2 = Matricula.objects.create(
                    alumno=estudiante,
                    periodo_academico=periodo,
                    aula=aula,
                    fecha_matricula=date(2026, 3, 1),
                    estado='Activa'
                )
        except IntegrityError:
            # Si no permite duplicados, está bien
            pass
        
        # Verificar que no hayan duplicados
        deudas_finales = Deuda.objects.filter(alumno=estudiante).count()
        assert deudas_finales == deudas_iniciales

    def test_error_en_signal_no_rompe_creacion_matricula(self, setup_matricula_data):
        """Prueba que si la señal falla, la matrícula se crea igual"""
        data = setup_matricula_data
        
        # Eliminar conceptos para forzar error en la señal
        ConceptoPago.objects.all().delete()
        
        # Crear matrícula (la señal intentará generar deudas pero fallará)
        try:
            matricula = Matricula.objects.create(
                alumno=data['estudiante'],
                periodo_academico=data['periodo'],
                aula=data['aula'],
                fecha_matricula=date(2026, 3, 1),
                estado='Activa'
            )
            # La matrícula debería crearse aunque la señal falle
            assert matricula.id is not None
        except Exception as e:
            # Si la señal no maneja bien los errores, podría fallar
            pytest.fail(f"La señal debería manejar errores sin romper la creación: {e}")

    def test_genera_cronograma_solo_en_creacion(self, setup_matricula_data):
        """Prueba que la señal solo se ejecute en creación, no en actualización"""
        data = setup_matricula_data
        estudiante = data['estudiante']
        periodo = data['periodo']
        aula = data['aula']
        
        # Crear matrícula
        matricula = Matricula.objects.create(
            alumno=estudiante,
            periodo_academico=periodo,
            aula=aula,
            fecha_matricula=date(2026, 3, 1),
            estado='Activa'
        )
        
        deudas_iniciales = Deuda.objects.filter(alumno=estudiante).count()
        
        # Actualizar matrícula (no debería generar nuevas deudas)
        matricula.estado = 'Retirado'
        matricula.save()
        
        deudas_finales = Deuda.objects.filter(alumno=estudiante).count()
        assert deudas_finales == deudas_iniciales

    def test_generar_cronograma_con_todas_las_deudas(self, setup_matricula_data):
        """Prueba que se generen todos los tipos de deuda correctamente"""
        data = setup_matricula_data
        estudiante = data['estudiante']
        periodo = data['periodo']
        aula = data['aula']
        
        matricula = Matricula.objects.create(
            alumno=estudiante,
            periodo_academico=periodo,
            aula=aula,
            fecha_matricula=date(2026, 3, 1),
            estado='Activa'
        )
        
        # Verificar tipos de deudas
        deudas = Deuda.objects.filter(alumno=estudiante)
        
        tipos = set(deudas.values_list('concepto__tipo', flat=True))
        assert 'CUOTA_INGRESO' in tipos
        assert 'MATRICULA' in tipos
        assert 'PENSION' in tipos
        
        # Verificar cantidades por tipo
        assert deudas.filter(concepto__tipo='CUOTA_INGRESO').count() == 1
        assert deudas.filter(concepto__tipo='MATRICULA').count() == 1
        assert deudas.filter(concepto__tipo='PENSION').count() == 10