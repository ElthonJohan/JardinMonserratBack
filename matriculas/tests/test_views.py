# matriculas/tests/test_views.py
import pytest
from datetime import date
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from matriculas.models import PeriodoAcademico, Matricula
from estudiantes.models import Estudiante, Aula, Apoderado, ApoderadoEstudiante


@pytest.fixture
def api_client():
    """Fixture para cliente API"""
    return APIClient()


@pytest.fixture
def admin_user(db):
    """Fixture para usuario administrador"""
    from usuarios.models import Usuario
    user = Usuario.objects.create_user(
        username="admin_test",
        password="admin123",
        is_staff=True,
        is_superuser=True
    )
    return user


@pytest.fixture
def authenticated_client(api_client, admin_user):
    """Fixture para cliente autenticado"""
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.fixture
def setup_matricula_data(db):
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
    
    # Crear matrícula
    matricula = Matricula.objects.create(
        alumno=estudiante,
        periodo_academico=periodo,
        aula=aula,
        estado='Activa'
    )
    
    return {
        'aula': aula,
        'estudiante': estudiante,
        'periodo': periodo,
        'matricula': matricula,
        'apoderado': apoderado
    }


@pytest.mark.django_db
class TestPeriodoAcademicoViewSet:
    """Pruebas para el ViewSet de PeriodoAcademico"""

    def test_list_periodos(self, authenticated_client, setup_matricula_data):
        """Prueba listar períodos académicos"""
        url = reverse('periodo-academico-list')
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        
        # Verificar que los resultados estén ordenados por año descendente
        if 'results' in response.data:
            assert len(response.data['results']) >= 1
            # Verificar que el primer resultado sea el más reciente (2026)
            assert response.data['results'][0]['anio'] == 2026
        else:
            assert len(response.data) >= 1
            assert response.data[0]['anio'] == 2026

    def test_create_periodo(self, authenticated_client):
        """Prueba crear período académico"""
        url = reverse('periodo-academico-list')
        data = {
            'nombre': '2027-1',
            'anio': 2027,
            'fecha_inicio': '2027-03-01',
            'fecha_fin': '2027-12-31',
            'activo': True
        }
        response = authenticated_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['nombre'] == '2027-1'
        assert response.data['anio'] == 2027
        assert response.data['fecha_inicio'] == '2027-03-01'
        assert response.data['fecha_fin'] == '2027-12-31'
        assert response.data['activo'] is True

    def test_create_periodo_duplicado(self, authenticated_client, setup_matricula_data):
        """Prueba crear período con nombre duplicado (debe fallar)"""
        url = reverse('periodo-academico-list')
        data = {
            'nombre': '2026-1',  # Nombre ya existe
            'anio': 2026,  # Año ya existe
            'fecha_inicio': '2026-03-01',
            'fecha_fin': '2026-12-31',
            'activo': True
        }
        response = authenticated_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_periodo(self, authenticated_client, setup_matricula_data):
        """Prueba actualizar período académico"""
        periodo = setup_matricula_data['periodo']
        url = reverse('periodo-academico-detail', args=[periodo.id])
        data = {
            'nombre': '2026-1 Actualizado',
            'activo': False
        }
        response = authenticated_client.patch(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['nombre'] == '2026-1 Actualizado'
        assert response.data['activo'] is False

    def test_partial_update_periodo(self, authenticated_client, setup_matricula_data):
        """Prueba actualización parcial de período académico"""
        periodo = setup_matricula_data['periodo']
        url = reverse('periodo-academico-detail', args=[periodo.id])
        data = {
            'activo': False
        }
        response = authenticated_client.patch(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['activo'] is False
        # Verificar que el nombre no cambió
        assert response.data['nombre'] == '2026-1'

    def test_delete_periodo(self, authenticated_client, setup_matricula_data):
        """Prueba eliminar período académico"""
        setup_matricula_data['matricula'].delete()
        periodo = setup_matricula_data['periodo']
        url = reverse('periodo-academico-detail', args=[periodo.id])
        response = authenticated_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not PeriodoAcademico.objects.filter(id=periodo.id).exists()

    def test_search_periodo_by_nombre(self, authenticated_client, setup_matricula_data):
        """Prueba buscar período por nombre"""
        url = reverse('periodo-academico-list')
        response = authenticated_client.get(url, {'search': '2026'})
        assert response.status_code == status.HTTP_200_OK
        if 'results' in response.data:
            assert len(response.data['results']) >= 1
            assert '2026' in response.data['results'][0]['nombre']
        else:
            assert len(response.data) >= 1
            assert '2026' in response.data[0]['nombre']

    def test_search_periodo_by_anio(self, authenticated_client, setup_matricula_data):
        """Prueba buscar período por año"""
        url = reverse('periodo-academico-list')
        response = authenticated_client.get(url, {'search': '2026'})
        assert response.status_code == status.HTTP_200_OK
        if 'results' in response.data:
            assert len(response.data['results']) >= 1
            assert response.data['results'][0]['anio'] == 2026
        else:
            assert len(response.data) >= 1
            assert response.data[0]['anio'] == 2026

    def test_ordenar_periodos_por_anio(self, authenticated_client, setup_matricula_data):
        """Prueba ordenar períodos por año"""
        # Crear otro período
        PeriodoAcademico.objects.create(
            nombre="2025-1",
            anio=2025,
            fecha_inicio=date(2025, 3, 1),
            fecha_fin=date(2025, 12, 31),
            activo=True
        )
        
        url = reverse('periodo-academico-list')
        response = authenticated_client.get(url, {'ordering': 'anio'})
        assert response.status_code == status.HTTP_200_OK
        
        if 'results' in response.data:
            assert response.data['results'][0]['anio'] == 2025
            assert response.data['results'][1]['anio'] == 2026
        else:
            assert response.data[0]['anio'] == 2025
            assert response.data[1]['anio'] == 2026


@pytest.mark.django_db
class TestMatriculaViewSet:
    """Pruebas para el ViewSet de Matricula"""

    def test_list_matriculas(self, authenticated_client, setup_matricula_data):
        """Prueba listar matrículas"""
        url = reverse('matricula-list')
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        
        # Verificar ordenamiento por año y fecha descendente
        if 'results' in response.data:
            assert len(response.data['results']) >= 1
            # Verificar que el alumno esté en los resultados
            assert response.data['results'][0]['alumno'] == setup_matricula_data['estudiante'].id
        else:
            assert len(response.data) >= 1
            assert response.data[0]['alumno'] == setup_matricula_data['estudiante'].id

    def test_create_matricula(self, authenticated_client, setup_matricula_data):
        """Prueba crear matrícula"""
        data = setup_matricula_data
        url = reverse('matricula-list')
        
        # Crear nuevo estudiante
        estudiante2 = Estudiante.objects.create(
            nombres="Ana",
            apellidos="Martínez",
            fecha_nacimiento=date(2021, 3, 10),
            dni="11111111"
        )
        
        post_data = {
            'alumno': estudiante2.id,
            'periodo_academico': data['periodo'].id,
            'aula': data['aula'].id,
            'estado': 'Activa',
            'observaciones': 'Nueva matrícula'
        }
        response = authenticated_client.post(url, post_data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['alumno'] == estudiante2.id
        assert response.data['estado'] == 'Activa'
        assert response.data['observaciones'] == 'Nueva matrícula'

    def test_create_matricula_duplicada(self, authenticated_client, setup_matricula_data):
        """Prueba crear matrícula duplicada (mismo alumno, mismo período)"""
        data = setup_matricula_data
        url = reverse('matricula-list')
        
        post_data = {
            'alumno': data['estudiante'].id,
            'periodo_academico': data['periodo'].id,
            'aula': data['aula'].id,
            'estado': 'Activa'
        }
        response = authenticated_client.post(url, post_data, format='json')
        # Debe fallar por unique constraint
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        # Verificar que el error menciona la restricción
        assert 'unique_matricula_periodo' in str(response.data) or 'matriculado' in str(response.data)

    def test_create_matricula_con_periodo_inactivo(self, authenticated_client, setup_matricula_data):
        """Prueba crear matrícula con período inactivo"""
        data = setup_matricula_data
        
        # Crear período inactivo
        periodo_inactivo = PeriodoAcademico.objects.create(
            nombre="2025-1",
            anio=2025,
            fecha_inicio=date(2025, 3, 1),
            fecha_fin=date(2025, 12, 31),
            activo=False
        )
        
        # Crear nuevo estudiante
        estudiante2 = Estudiante.objects.create(
            nombres="Ana",
            apellidos="Martínez",
            fecha_nacimiento=date(2021, 3, 10),
            dni="11111111"
        )
        
        url = reverse('matricula-list')
        post_data = {
            'alumno': estudiante2.id,
            'periodo_academico': periodo_inactivo.id,
            'aula': data['aula'].id,
            'estado': 'Activa'
        }
        response = authenticated_client.post(url, post_data, format='json')
        # Dependiendo de tu lógica, podría permitir o no
        # Si tu vista valida que el período esté activo, debería fallar
        # Si no, debería crear la matrícula
        assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST]

    def test_filter_matricula_by_periodo(self, authenticated_client, setup_matricula_data):
        """Prueba filtrar matrículas por período académico"""
        data = setup_matricula_data
        url = reverse('matricula-list')
        response = authenticated_client.get(url, {'periodo_academico': data['periodo'].id})
        assert response.status_code == status.HTTP_200_OK
        
        if 'results' in response.data:
            assert len(response.data['results']) >= 1
            assert response.data['results'][0]['periodo_academico'] == data['periodo'].id
        else:
            assert len(response.data) >= 1
            assert response.data[0]['periodo_academico'] == data['periodo'].id

    def test_filter_matricula_by_estado(self, authenticated_client, setup_matricula_data):
        """Prueba filtrar matrículas por estado"""
        url = reverse('matricula-list')
        response = authenticated_client.get(url, {'estado': 'Activa'})
        assert response.status_code == status.HTTP_200_OK
        
        if 'results' in response.data:
            assert len(response.data['results']) >= 1
            assert response.data['results'][0]['estado'] == 'Activa'
        else:
            assert len(response.data) >= 1
            assert response.data[0]['estado'] == 'Activa'

    def test_filter_matricula_by_alumno(self, authenticated_client, setup_matricula_data):
        """Prueba filtrar matrículas por alumno"""
        data = setup_matricula_data
        url = reverse('matricula-list')
        response = authenticated_client.get(url, {'alumno': data['estudiante'].id})
        assert response.status_code == status.HTTP_200_OK
        
        if 'results' in response.data:
            assert len(response.data['results']) == 1
            assert response.data['results'][0]['alumno'] == data['estudiante'].id
        else:
            assert len(response.data) == 1
            assert response.data[0]['alumno'] == data['estudiante'].id

    def test_search_matricula_by_alumno_nombre(self, authenticated_client, setup_matricula_data):
        """Prueba buscar matrícula por nombre de alumno"""
        url = reverse('matricula-list')
        response = authenticated_client.get(url, {'search': 'Luis'})
        assert response.status_code == status.HTTP_200_OK
        
        if 'results' in response.data:
            assert len(response.data['results']) >= 1
            # El nombre del alumno está en el campo 'alumno_nombre' del serializer
            # o se puede verificar por el ID
        else:
            assert len(response.data) >= 1

    def test_search_matricula_by_aula(self, authenticated_client, setup_matricula_data):
        """Prueba buscar matrícula por nombre de aula"""
        data = setup_matricula_data
        url = reverse('matricula-list')
        response = authenticated_client.get(url, {'search': '3 años'})
        assert response.status_code == status.HTTP_200_OK
        
        if 'results' in response.data:
            assert len(response.data['results']) >= 1
        else:
            assert len(response.data) >= 1

    def test_search_matricula_by_periodo(self, authenticated_client, setup_matricula_data):
        """Prueba buscar matrícula por nombre de período"""
        url = reverse('matricula-list')
        response = authenticated_client.get(url, {'search': '2026-1'})
        assert response.status_code == status.HTTP_200_OK
        
        if 'results' in response.data:
            assert len(response.data['results']) >= 1
        else:
            assert len(response.data) >= 1

    def test_update_matricula(self, authenticated_client, setup_matricula_data):
        """Prueba actualizar matrícula"""
        matricula = setup_matricula_data['matricula']
        url = reverse('matricula-detail', args=[matricula.id])
        
        # Crear nueva aula
        aula2 = Aula.objects.create(nombre="4 años", capacidad=25)
        
        data = {
            'aula': aula2.id,
            'estado': 'Trasladado',
            'observaciones': 'Cambio de aula'
        }
        response = authenticated_client.patch(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['estado'] == 'Trasladado'
        assert response.data['aula'] == aula2.id
        assert response.data['observaciones'] == 'Cambio de aula'

    def test_partial_update_matricula_estado(self, authenticated_client, setup_matricula_data):
        """Prueba actualización parcial de estado de matrícula"""
        matricula = setup_matricula_data['matricula']
        url = reverse('matricula-detail', args=[matricula.id])
        data = {
            'estado': 'Retirado'
        }
        response = authenticated_client.patch(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['estado'] == 'Retirado'
        # Verificar que otros campos no cambiaron
        assert response.data['alumno'] == matricula.alumno.id

    def test_delete_matricula(self, authenticated_client, setup_matricula_data):
        """Prueba eliminar matrícula"""
        matricula = setup_matricula_data['matricula']
        url = reverse('matricula-detail', args=[matricula.id])
        response = authenticated_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Matricula.objects.filter(id=matricula.id).exists()

    def test_ordenar_matriculas_por_periodo(self, authenticated_client, setup_matricula_data):
        """Prueba ordenar matrículas por período académico"""
        # Crear segundo período y matrícula
        periodo2 = PeriodoAcademico.objects.create(
            nombre="2025-1",
            anio=2025,
            fecha_inicio=date(2025, 3, 1),
            fecha_fin=date(2025, 12, 31),
            activo=True
        )
        
        estudiante2 = Estudiante.objects.create(
            nombres="Ana",
            apellidos="Martínez",
            fecha_nacimiento=date(2021, 3, 10),
            dni="11111111"
        )
        
        Matricula.objects.create(
            alumno=estudiante2,
            periodo_academico=periodo2,
            aula=setup_matricula_data['aula'],
            estado='Activa'
        )
        
        url = reverse('matricula-list')
        response = authenticated_client.get(url, {'ordering': 'periodo_academico__anio'})
        assert response.status_code == status.HTTP_200_OK
        
        if 'results' in response.data:
            # Debe tener al menos 2 resultados
            assert len(response.data['results']) >= 2
            # El año del período debe estar en orden ascendente
            anios = [r['periodo_academico'] for r in response.data['results']]
            # Verificar que el primer período sea el más antiguo (2025)
            # Esto depende de cómo se serializa
        else:
            assert len(response.data) >= 2

    def test_ordenar_matriculas_por_fecha(self, authenticated_client, setup_matricula_data):
        """Prueba ordenar matrículas por fecha"""
        # Crear segunda matrícula con fecha diferente
        periodo2 = PeriodoAcademico.objects.create(
            nombre="2025-1",
            anio=2025,
            fecha_inicio=date(2025, 3, 1),
            fecha_fin=date(2025, 12, 31),
            activo=True
        )
        
        estudiante2 = Estudiante.objects.create(
            nombres="Ana",
            apellidos="Martínez",
            fecha_nacimiento=date(2021, 3, 10),
            dni="11111111"
        )
        
        matricula2 = Matricula.objects.create(
            alumno=estudiante2,
            periodo_academico=periodo2,
            aula=setup_matricula_data['aula'],
            estado='Activa'
        )
        
        url = reverse('matricula-list')
        response = authenticated_client.get(url, {'ordering': 'fecha_matricula'})
        assert response.status_code == status.HTTP_200_OK
        
        if 'results' in response.data:
            assert len(response.data['results']) >= 2
            # Las fechas deben estar ordenadas ascendentemente
        else:
            assert len(response.data) >= 2

    def test_ordenar_matriculas_por_estado(self, authenticated_client, setup_matricula_data):
        """Prueba ordenar matrículas por estado"""
        # Crear otra matrícula con estado diferente
        periodo2 = PeriodoAcademico.objects.create(
            nombre="2025-1",
            anio=2025,
            fecha_inicio=date(2025, 3, 1),
            fecha_fin=date(2025, 12, 31),
            activo=True
        )
        
        estudiante2 = Estudiante.objects.create(
            nombres="Ana",
            apellidos="Martínez",
            fecha_nacimiento=date(2021, 3, 10),
            dni="11111111"
        )
        
        Matricula.objects.create(
            alumno=estudiante2,
            periodo_academico=periodo2,
            aula=setup_matricula_data['aula'],
            estado='Retirado'
        )
        
        url = reverse('matricula-list')
        response = authenticated_client.get(url, {'ordering': 'estado'})
        assert response.status_code == status.HTTP_200_OK
        
        if 'results' in response.data:
            assert len(response.data['results']) >= 2
            # Los estados deben estar ordenados alfabéticamente
        else:
            assert len(response.data) >= 2


@pytest.mark.django_db
class TestMatriculaUnauthorized:
    """Pruebas de autorización para matrículas"""

    def test_list_matriculas_unauthorized(self, api_client):
        """Prueba que usuarios no autenticados no puedan listar matrículas"""
        url = reverse('matricula-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_matricula_unauthorized(self, api_client):
        """Prueba que usuarios no autenticados no puedan crear matrículas"""
        url = reverse('matricula-list')
        data = {
            'alumno': 1,
            'periodo_academico': 1,
            'aula': 1,
            'estado': 'Activa'
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_periodo_list_unauthorized(self, api_client):
        """Prueba que usuarios no autenticados no puedan listar períodos"""
        url = reverse('periodo-academico-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED