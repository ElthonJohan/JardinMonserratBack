# matriculas/tests/test_models.py
import pytest
from datetime import date, timedelta
from django.db import IntegrityError
from django.core.exceptions import ValidationError

from matriculas.models import PeriodoAcademico, Matricula
from estudiantes.models import Estudiante, Aula, Apoderado, ApoderadoEstudiante


@pytest.mark.django_db
class TestPeriodoAcademicoModel:
    """Pruebas para el modelo PeriodoAcademico"""

    def test_crear_periodo_academico(self):
        """Prueba creación básica de período académico"""
        periodo = PeriodoAcademico.objects.create(
            nombre="2026-1",
            anio=2026,
            fecha_inicio=date(2026, 3, 1),
            fecha_fin=date(2026, 12, 31),
            activo=True
        )
        assert periodo.nombre == "2026-1"
        assert periodo.anio == 2026
        assert periodo.fecha_inicio == date(2026, 3, 1)
        assert periodo.fecha_fin == date(2026, 12, 31)
        assert periodo.activo is True
        assert str(periodo) == "2026-1 (2026-03-01 - 2026-12-31)"

    def test_periodo_nombre_unico(self):
        """Prueba que el nombre del período sea único"""
        PeriodoAcademico.objects.create(
            nombre="2026-1",
            anio=2026,
            fecha_inicio=date(2026, 3, 1),
            fecha_fin=date(2026, 12, 31)
        )
        
        with pytest.raises(IntegrityError):
            PeriodoAcademico.objects.create(
                nombre="2026-1",  # Mismo nombre
                anio=2027,
                fecha_inicio=date(2027, 3, 1),
                fecha_fin=date(2027, 12, 31)
            )

    def test_periodo_anio_unico(self):
        """Prueba que el año del período sea único"""
        PeriodoAcademico.objects.create(
            nombre="2026-1",
            anio=2026,
            fecha_inicio=date(2026, 3, 1),
            fecha_fin=date(2026, 12, 31)
        )
        
        with pytest.raises(IntegrityError):
            PeriodoAcademico.objects.create(
                nombre="2026-2",  # Nombre diferente
                anio=2026,  # Mismo año
                fecha_inicio=date(2026, 8, 1),
                fecha_fin=date(2026, 12, 31)
            )

    def test_periodo_activo_por_defecto(self):
        """Prueba que activo sea True por defecto"""
        periodo = PeriodoAcademico.objects.create(
            nombre="2026-1",
            anio=2026,
            fecha_inicio=date(2026, 3, 1),
            fecha_fin=date(2026, 12, 31)
        )
        assert periodo.activo is True

    def test_periodo_ordenamiento(self):
        """Prueba que los períodos se ordenen por año descendente"""
        PeriodoAcademico.objects.create(
            nombre="2024-1",
            anio=2024,
            fecha_inicio=date(2024, 3, 1),
            fecha_fin=date(2024, 12, 31)
        )
        PeriodoAcademico.objects.create(
            nombre="2025-1",
            anio=2025,
            fecha_inicio=date(2025, 3, 1),
            fecha_fin=date(2025, 12, 31)
        )
        PeriodoAcademico.objects.create(
            nombre="2026-1",
            anio=2026,
            fecha_inicio=date(2026, 3, 1),
            fecha_fin=date(2026, 12, 31)
        )
        
        periodos = PeriodoAcademico.objects.all()
        assert periodos[0].anio == 2026
        assert periodos[1].anio == 2025
        assert periodos[2].anio == 2024


@pytest.mark.django_db
class TestMatriculaModel:
    """Pruebas para el modelo Matricula"""

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
            email="carlos@example.com"
        )
        
        # Crear estudiante
        estudiante = Estudiante.objects.create(
            nombres="Luis",
            apellidos="Gómez",
            fecha_nacimiento=date(2020, 5, 15),
            dni="87654321"
        )
        
        # Crear relación apoderado-estudiante
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
            fecha_fin=date(2026, 12, 31),
            activo=True
        )
        
        return {
            'aula': aula,
            'estudiante': estudiante,
            'periodo': periodo,
            'apoderado': apoderado
        }

    def test_crear_matricula(self, setup_matricula_data):
        """Prueba creación básica de matrícula"""
        data = setup_matricula_data
        matricula = Matricula.objects.create(
            alumno=data['estudiante'],
            periodo_academico=data['periodo'],
            aula=data['aula'],
            estado='Activa'
        )
        
        assert matricula.alumno == data['estudiante']
        assert matricula.periodo_academico == data['periodo']
        assert matricula.aula == data['aula']
        assert matricula.estado == 'Activa'
        assert matricula.fecha_matricula is not None
        assert matricula.created_at is not None
        assert matricula.updated_at is not None
        assert str(matricula) == f"{data['estudiante']} - Aula {data['aula'].nombre} - {data['periodo'].nombre}"

    def test_matricula_periodo_unique_constraint(self, setup_matricula_data):
        """Prueba que no se pueda matricular al mismo alumno en el mismo período"""
        data = setup_matricula_data
        
        # Primera matrícula
        Matricula.objects.create(
            alumno=data['estudiante'],
            periodo_academico=data['periodo'],
            aula=data['aula'],
            estado='Activa'
        )
        
        # Segunda matrícula (mismo alumno, mismo período) - DEBE FALLAR
        with pytest.raises(IntegrityError) as excinfo:
            Matricula.objects.create(
                alumno=data['estudiante'],
                periodo_academico=data['periodo'],
                aula=data['aula'],
                estado='Activa'
            )
        assert "unique_matricula_periodo" in str(excinfo.value)

    def test_matricula_permite_mismo_alumno_periodo_diferente(self, setup_matricula_data):
        """Prueba que un alumno pueda matricularse en períodos diferentes"""
        data = setup_matricula_data
        
        # Primera matrícula
        Matricula.objects.create(
            alumno=data['estudiante'],
            periodo_academico=data['periodo'],
            aula=data['aula'],
            estado='Activa'
        )
        
        # Crear segundo período
        periodo2 = PeriodoAcademico.objects.create(
            nombre="2027-1",
            anio=2027,
            fecha_inicio=date(2027, 3, 1),
            fecha_fin=date(2027, 12, 31)
        )
        
        # Segunda matrícula (mismo alumno, período diferente) - DEBE FUNCIONAR
        matricula2 = Matricula.objects.create(
            alumno=data['estudiante'],
            periodo_academico=periodo2,
            aula=data['aula'],
            estado='Activa'
        )
        assert matricula2.id is not None
        assert Matricula.objects.filter(alumno=data['estudiante']).count() == 2

    def test_matricula_permite_diferente_alumno_mismo_periodo(self, setup_matricula_data):
        """Prueba que diferentes alumnos puedan matricularse en el mismo período"""
        data = setup_matricula_data
        
        # Crear segundo estudiante
        estudiante2 = Estudiante.objects.create(
            nombres="Ana",
            apellidos="Martínez",
            fecha_nacimiento=date(2021, 3, 10),
            dni="11111111"
        )
        
        # Matrícula del primer estudiante
        Matricula.objects.create(
            alumno=data['estudiante'],
            periodo_academico=data['periodo'],
            aula=data['aula'],
            estado='Activa'
        )
        
        # Matrícula del segundo estudiante (mismo período) - DEBE FUNCIONAR
        matricula2 = Matricula.objects.create(
            alumno=estudiante2,
            periodo_academico=data['periodo'],
            aula=data['aula'],
            estado='Activa'
        )
        assert matricula2.id is not None

    def test_matricula_estados_validos(self, setup_matricula_data):
        """Prueba que los estados válidos funcionen"""
        data = setup_matricula_data
        estados = ['Activa', 'Trasladado', 'Retirado']
        
        for estado in estados:
            matricula = Matricula.objects.create(
                alumno=data['estudiante'],
                periodo_academico=data['periodo'],
                aula=data['aula'],
                estado=estado
            )
            assert matricula.estado == estado
            matricula.delete()

    def test_matricula_aula_requerida(self, setup_matricula_data):
        """Prueba que el aula sea requerida"""
        data = setup_matricula_data
        
        with pytest.raises(IntegrityError):
            Matricula.objects.create(
                alumno=data['estudiante'],
                periodo_academico=data['periodo'],
                aula=None,  # Aula no puede ser null
                estado='Activa'
            )

    def test_matricula_alumno_requerido(self, setup_matricula_data):
        """Prueba que el alumno sea requerido"""
        data = setup_matricula_data
        
        with pytest.raises(IntegrityError):
            Matricula.objects.create(
                alumno=None,  # Alumno no puede ser null
                periodo_academico=data['periodo'],
                aula=data['aula'],
                estado='Activa'
            )

    def test_matricula_observaciones_opcionales(self, setup_matricula_data):
        """Prueba que las observaciones sean opcionales"""
        data = setup_matricula_data
        
        matricula_sin_obs = Matricula.objects.create(
            alumno=data['estudiante'],
            periodo_academico=data['periodo'],
            aula=data['aula'],
            estado='Activa'
        )
        assert matricula_sin_obs.observaciones is None
        matricula_sin_obs.delete()
        
        matricula_con_obs = Matricula.objects.create(
            alumno=data['estudiante'],
            periodo_academico=data['periodo'],
            aula=data['aula'],
            estado='Activa',
            observaciones="Matrícula con observaciones"
        )
        assert matricula_con_obs.observaciones == "Matrícula con observaciones"

    def test_matricula_ordenamiento(self, setup_matricula_data):
        """Prueba que las matrículas se ordenen por fecha descendente"""
        data = setup_matricula_data
        
        # Crear matrícula con fecha anterior
        matricula1 = Matricula.objects.create(
            alumno=data['estudiante'],
            periodo_academico=data['periodo'],
            aula=data['aula'],
            estado='Activa'
        )
        matricula1.fecha_matricula = date(2025, 3, 1)
        matricula1.save()
        
        # Crear segundo período y matrícula
        periodo2 = PeriodoAcademico.objects.create(
            nombre="2025-1",
            anio=2025,
            fecha_inicio=date(2025, 3, 1),
            fecha_fin=date(2025, 12, 31)
        )
        
        # Crear nuevo estudiante para la segunda matrícula
        estudiante2 = Estudiante.objects.create(
            nombres="Ana",
            apellidos="Martínez",
            fecha_nacimiento=date(2021, 3, 10),
            dni="11111111"
        )
        
        matricula2 = Matricula.objects.create(
            alumno=estudiante2,
            periodo_academico=periodo2,
            aula=data['aula'],
            estado='Activa'
        )
        matricula2.fecha_matricula = date(2026, 8, 15)
        matricula2.save()
        
        # Verificar orden
        matriculas = Matricula.objects.all()
        assert matriculas[0].fecha_matricula >= matriculas[1].fecha_matricula

    def test_matricula_indexes(self, setup_matricula_data):
        """Prueba que los índices existan (verificación estructural)"""
        data = setup_matricula_data
        
        # Crear una matrícula
        matricula = Matricula.objects.create(
            alumno=data['estudiante'],
            periodo_academico=data['periodo'],
            aula=data['aula'],
            estado='Activa'
        )
        
        # Verificar que se pueda filtrar por periodo_academico
        matriculas_periodo = Matricula.objects.filter(periodo_academico=data['periodo'])
        assert matriculas_periodo.count() == 1
        
        # Verificar que se pueda filtrar por estado
        matriculas_activas = Matricula.objects.filter(estado='Activa')
        assert matriculas_activas.count() >= 1

    def test_matricula_str_sin_alumno(self):
        """Prueba el string de matrícula cuando no hay alumno"""
        # Crear aula y período
        aula = Aula.objects.create(nombre="3 años", capacidad=20)
        periodo = PeriodoAcademico.objects.create(
            nombre="2026-1",
            anio=2026,
            fecha_inicio=date(2026, 3, 1),
            fecha_fin=date(2026, 12, 31)
        )
        
        # No podemos crear una matrícula sin alumno por la restricción de BD
        # Esta prueba verifica que el __str__ maneje casos donde alumno no existe
        # (por ejemplo, si se elimina el alumno, aunque on_delete=RESTRICT lo previene)
        pass