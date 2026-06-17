# core/tests/test_views.py
import pytest
from datetime import date
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from core.models import Grado, Seccion, Alumno
from usuarios.models import Usuario


@pytest.fixture
def api_client():
    """Fixture para cliente API"""
    return APIClient()


@pytest.fixture
def admin_user(db):
    """Fixture para usuario administrador"""
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
def setup_core_data(db):
    """Configuración base para pruebas de core"""
    grado = Grado.objects.create(
        nombre="1ro de Primaria",
        nivel="Primaria",
        orden=1,
        activo=True
    )
    
    seccion = Seccion.objects.create(
        nombre="A",
        activo=True
    )
    
    alumno = Alumno.objects.create(
        nro_matricula="2026-0001",
        nombres="Luis",
        apellidos="Gómez",
        dni="12345678",
        fecha_nacimiento=date(2020, 5, 15),
        nombre_apoderado="Carlos Gómez",
        telefono_apoderado="999888777",
        estado="Activo"
    )
    
    return {
        'grado': grado,
        'seccion': seccion,
        'alumno': alumno
    }


@pytest.mark.django_db
class TestGradoViewSet:
    """Pruebas para el ViewSet de Grados"""

    def test_list_grados(self, authenticated_client, setup_core_data):
        """Prueba listar grados"""
        url = reverse('grado-list')
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        
        if 'results' in response.data:
            assert len(response.data['results']) >= 1
        else:
            assert len(response.data) >= 1

    def test_create_grado(self, authenticated_client):
        """Prueba crear grado"""
        url = reverse('grado-list')
        data = {
            'nombre': '2do de Primaria',
            'nivel': 'Primaria',
            'orden': 2,
            'activo': True
        }
        response = authenticated_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['nombre'] == '2do de Primaria'
        assert response.data['nivel'] == 'Primaria'
        assert response.data['orden'] == 2

    def test_update_grado(self, authenticated_client, setup_core_data):
        """Prueba actualizar grado"""
        grado = setup_core_data['grado']
        url = reverse('grado-detail', args=[grado.id])
        data = {
            'nombre': '1ro de Primaria Actualizado',
            'activo': False
        }
        response = authenticated_client.patch(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['nombre'] == '1ro de Primaria Actualizado'
        assert response.data['activo'] is False

    def test_delete_grado(self, authenticated_client, setup_core_data):
        """Prueba eliminar grado (soft delete)"""
        grado = setup_core_data['grado']
        url = reverse('grado-detail', args=[grado.id])
        response = authenticated_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verificar que ya no aparece en listado (solo activos)
        grados = Grado.objects.filter(activo=True)
        assert grados.count() == 0

    def test_search_grado_by_nombre(self, authenticated_client, setup_core_data):
        """Prueba buscar grado por nombre"""
        url = reverse('grado-list')
        response = authenticated_client.get(url, {'search': 'Primaria'})
        assert response.status_code == status.HTTP_200_OK
        
        if 'results' in response.data:
            assert len(response.data['results']) >= 1
        else:
            assert len(response.data) >= 1

    def test_ordenar_grados_por_orden(self, authenticated_client, setup_core_data):
        """Prueba ordenar grados por orden"""
        # Crear otro grado
        Grado.objects.create(
            nombre="2do de Primaria",
            nivel="Primaria",
            orden=2,
            activo=True
        )
        
        url = reverse('grado-list')
        response = authenticated_client.get(url, {'ordering': 'orden'})
        assert response.status_code == status.HTTP_200_OK
        
        if 'results' in response.data:
            assert response.data['results'][0]['orden'] == 1
            assert response.data['results'][1]['orden'] == 2


@pytest.mark.django_db
class TestSeccionViewSet:
    """Pruebas para el ViewSet de Secciones"""

    def test_list_secciones(self, authenticated_client, setup_core_data):
        """Prueba listar secciones"""
        url = reverse('seccion-list')
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        
        if 'results' in response.data:
            assert len(response.data['results']) >= 1
        else:
            assert len(response.data) >= 1

    def test_create_seccion(self, authenticated_client):
        """Prueba crear sección"""
        url = reverse('seccion-list')
        data = {
            'nombre': 'B',
            'activo': True
        }
        response = authenticated_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['nombre'] == 'B'

    def test_update_seccion(self, authenticated_client, setup_core_data):
        """Prueba actualizar sección"""
        seccion = setup_core_data['seccion']
        url = reverse('seccion-detail', args=[seccion.id])
        data = {
            'nombre': 'Única',
            'activo': False
        }
        response = authenticated_client.patch(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['nombre'] == 'Única'
        assert response.data['activo'] is False

    def test_delete_seccion(self, authenticated_client, setup_core_data):
        """Prueba eliminar sección (soft delete)"""
        seccion = setup_core_data['seccion']
        url = reverse('seccion-detail', args=[seccion.id])
        response = authenticated_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verificar que ya no aparece en listado (solo activas)
        secciones = Seccion.objects.filter(activo=True)
        assert secciones.count() == 0

    def test_search_seccion_by_nombre(self, authenticated_client, setup_core_data):
        """Prueba buscar sección por nombre"""
        url = reverse('seccion-list')
        response = authenticated_client.get(url, {'search': 'A'})
        assert response.status_code == status.HTTP_200_OK
        
        if 'results' in response.data:
            assert len(response.data['results']) >= 1
        else:
            assert len(response.data) >= 1


@pytest.mark.django_db
class TestAlumnoViewSet:
    """Pruebas para el ViewSet de Alumnos"""

    def test_list_alumnos(self, authenticated_client, setup_core_data):
        """Prueba listar alumnos"""
        url = reverse('alumno-list')
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        
        if 'results' in response.data:
            assert len(response.data['results']) >= 1
        else:
            assert len(response.data) >= 1

    def test_create_alumno(self, authenticated_client):
        """Prueba crear alumno"""
        url = reverse('alumno-list')
        data = {
            'nro_matricula': '2026-0002',
            'nombres': 'Ana',
            'apellidos': 'Martínez',
            'dni': '87654321',
            'fecha_nacimiento': '2021-03-10',
            'nombre_apoderado': 'Pedro Martínez',
            'telefono_apoderado': '999888777',
            'estado': 'Activo'
        }
        response = authenticated_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['nombres'] == 'Ana'
        assert response.data['apellidos'] == 'Martínez'

    def test_create_alumno_duplicado(self, authenticated_client, setup_core_data):
        """Prueba crear alumno con datos duplicados"""
        url = reverse('alumno-list')
        data = {
            'nro_matricula': '2026-0001',  # Ya existe
            'nombres': 'Ana',
            'apellidos': 'Martínez',
            'dni': '87654321',
            'fecha_nacimiento': '2021-03-10',
            'nombre_apoderado': 'Pedro Martínez',
            'telefono_apoderado': '999888777'
        }
        response = authenticated_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_alumno(self, authenticated_client, setup_core_data):
        """Prueba actualizar alumno"""
        alumno = setup_core_data['alumno']
        url = reverse('alumno-detail', args=[alumno.id])
        data = {
            'nombres': 'Luis Carlos',
            'telefono': '999888666',
            'estado': 'Retirado'
        }
        response = authenticated_client.patch(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['nombres'] == 'Luis Carlos'
        assert response.data['telefono'] == '999888666'
        assert response.data['estado'] == 'Retirado'

    def test_delete_alumno(self, authenticated_client, setup_core_data):
        """Prueba eliminar alumno"""
        alumno = setup_core_data['alumno']
        url = reverse('alumno-detail', args=[alumno.id])
        response = authenticated_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Alumno.objects.filter(id=alumno.id).exists()

    def test_search_alumno_by_nombre(self, authenticated_client, setup_core_data):
        """Prueba buscar alumno por nombre"""
        url = reverse('alumno-list')
        response = authenticated_client.get(url, {'search': 'Luis'})
        assert response.status_code == status.HTTP_200_OK
        
        if 'results' in response.data:
            assert len(response.data['results']) >= 1
        else:
            assert len(response.data) >= 1

    def test_search_alumno_by_dni(self, authenticated_client, setup_core_data):
        """Prueba buscar alumno por DNI"""
        url = reverse('alumno-list')
        response = authenticated_client.get(url, {'search': '12345678'})
        assert response.status_code == status.HTTP_200_OK
        
        if 'results' in response.data:
            assert len(response.data['results']) >= 1
        else:
            assert len(response.data) >= 1

    def test_search_alumno_by_nro_matricula(self, authenticated_client, setup_core_data):
        """Prueba buscar alumno por número de matrícula"""
        url = reverse('alumno-list')
        response = authenticated_client.get(url, {'search': '2026-0001'})
        assert response.status_code == status.HTTP_200_OK
        
        if 'results' in response.data:
            assert len(response.data['results']) >= 1
        else:
            assert len(response.data) >= 1

    def test_action_alumnos_activos(self, authenticated_client, setup_core_data):
        """Prueba el action 'activos' - listar solo alumnos activos"""
        # Crear alumno inactivo
        Alumno.objects.create(
            nro_matricula="2026-0003",
            nombres="Carlos",
            apellidos="Pérez",
            dni="11111111",
            fecha_nacimiento=date(2020, 5, 15),
            nombre_apoderado="Carlos Pérez",
            telefono_apoderado="999888777",
            estado="Retirado"
        )
        
        url = reverse('alumno-activos')
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1
        
        # Verificar que solo retorna alumnos activos
        for alumno in response.data:
            assert alumno['estado'] == 'Activo'

    def test_action_alumnos_por_estado(self, authenticated_client, setup_core_data):
        """Prueba el action 'por_estado' - filtrar alumnos por estado"""
        # Crear alumno inactivo
        Alumno.objects.create(
            nro_matricula="2026-0003",
            nombres="Carlos",
            apellidos="Pérez",
            dni="11111111",
            fecha_nacimiento=date(2020, 5, 15),
            nombre_apoderado="Carlos Pérez",
            telefono_apoderado="999888777",
            estado="Retirado"
        )
        
        url = reverse('alumno-por-estado')
        
        # Filtrar por estado 'Retirado'
        response = authenticated_client.get(url, {'estado': 'Retirado'})
        assert response.status_code == status.HTTP_200_OK
        
        for alumno in response.data:
            assert alumno['estado'] == 'Retirado'

    def test_action_alumnos_por_estado_sin_parametro(self, authenticated_client, setup_core_data):
        """Prueba el action 'por_estado' sin parámetro - debería retornar todos"""
        url = reverse('alumno-por-estado')
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        # Debe retornar todos los alumnos
        assert len(response.data) >= 1

    def test_alumno_ordenamiento(self, authenticated_client, setup_core_data):
        """Prueba ordenar alumnos por apellidos"""
        # Crear más alumnos
        Alumno.objects.create(
            nro_matricula="2026-0002",
            nombres="Ana",
            apellidos="Martínez",
            dni="87654321",
            fecha_nacimiento=date(2021, 3, 10),
            nombre_apoderado="Pedro Martínez",
            telefono_apoderado="999888777",
            estado="Activo"
        )
        
        url = reverse('alumno-list')
        response = authenticated_client.get(url, {'ordering': 'apellidos'})
        assert response.status_code == status.HTTP_200_OK
        
        if 'results' in response.data:
            assert response.data['results'][0]['apellidos'] == 'Gómez'
            assert response.data['results'][1]['apellidos'] == 'Martínez'


@pytest.mark.django_db
class TestCoreAuthorization:
    """Pruebas de autorización para core"""

    def test_list_grados_unauthorized(self, api_client):
        """Prueba que usuarios no autenticados no puedan listar grados"""
        url = reverse('grado-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_secciones_unauthorized(self, api_client):
        """Prueba que usuarios no autenticados no puedan listar secciones"""
        url = reverse('seccion-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_alumnos_unauthorized(self, api_client):
        """Prueba que usuarios no autenticados no puedan listar alumnos"""
        url = reverse('alumno-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_alumnos_activos_unauthorized(self, api_client):
        """Prueba que usuarios no autenticados no puedan acceder a alumnos activos"""
        url = reverse('alumno-activos')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED