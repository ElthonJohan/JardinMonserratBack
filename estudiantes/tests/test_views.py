# estudiantes/tests/test_views.py
import pytest
from decimal import Decimal
from datetime import date
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from django.db import transaction

from estudiantes.models import Aula, Apoderado, Estudiante, ApoderadoEstudiante
from usuarios.models import Usuario

User = get_user_model()


@pytest.fixture
def api_client():
    """Fixture para cliente API"""
    return APIClient()


@pytest.fixture
def admin_user(db):
    """Fixture para usuario administrador"""
    user = User.objects.create_user(
        username="admin_test",
        password="admin123",
        is_staff=True,
        is_superuser=True
    )
    return user


@pytest.fixture
def authenticated_client(api_client, admin_user):
    """Fixture para cliente autenticado como admin"""
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.fixture
def parent_user(db):
    """Fixture para usuario apoderado"""
    apoderado = Apoderado.objects.create(
        nombres="Carlos",
        apellidos="Gómez",
        dni="12345678",
        telefono="999888777",
        email="carlos@example.com"
    )
    user = User.objects.create_user(
        username="parent123",
        password="parent123",
        is_parent=True,
        apoderado_rel=apoderado
    )
    return user, apoderado


@pytest.fixture
def setup_basic_data(db):
    """Configuración básica para pruebas"""
    aula = Aula.objects.create(
        nombre="3 años",
        capacidad=20
    )
    
    apoderado = Apoderado.objects.create(
        nombres="Carlos",
        apellidos="Gómez",
        dni="12345678",
        telefono="999888777",
        email="carlos@example.com"
    )
    
    estudiante = Estudiante.objects.create(
        nombres="Luis",
        apellidos="Gómez",
        fecha_nacimiento=date(2020, 5, 15),
        dni="87654321"
    )
    
    relacion = ApoderadoEstudiante.objects.create(
        apoderado=apoderado,
        estudiante=estudiante,
        tipo_relacion="PADRE",
        es_principal=True
    )
    
    return {
        'aula': aula,
        'apoderado': apoderado,
        'estudiante': estudiante,
        'relacion': relacion
    }


@pytest.mark.django_db
class TestAulaViewSet:
    """Pruebas para el ViewSet de Aulas"""

    def test_list_aulas(self, authenticated_client, setup_basic_data):
        """Prueba listar aulas"""
        url = reverse('aula-list')
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 1

    def test_create_aula(self, authenticated_client):
        """Prueba crear aula"""
        url = reverse('aula-list')
        data = {
            'nombre': '4 años',
            'capacidad': 25
        }
        response = authenticated_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['nombre'] == '4 años'
        assert response.data['capacidad'] == 25

    def test_update_aula(self, authenticated_client, setup_basic_data):
        """Prueba actualizar aula"""
        aula = setup_basic_data['aula']
        url = reverse('aula-detail', args=[aula.id])
        data = {
            'nombre': '3 años Actualizado',
            'capacidad': 22
        }
        response = authenticated_client.patch(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['nombre'] == '3 años Actualizado'

    def test_delete_aula(self, authenticated_client, setup_basic_data):
        """Prueba eliminar aula"""
        aula = setup_basic_data['aula']
        url = reverse('aula-detail', args=[aula.id])
        response = authenticated_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Aula.objects.filter(id=aula.id).exists()


@pytest.mark.django_db
class TestApoderadoViewSet:
    """Pruebas para el ViewSet de Apoderados"""

    def test_list_apoderados(self, authenticated_client, setup_basic_data):
        """Prueba listar apoderados"""
        url = reverse('apoderado-list')
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 1

    def test_create_apoderado(self, authenticated_client):
        """Prueba crear apoderado"""
        url = reverse('apoderado-list')
        data = {
            'nombres': 'María',
            'apellidos': 'López',
            'dni': '87654321',
            'telefono': '999888777',
            'email': 'maria@example.com'
        }
        response = authenticated_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['nombres'] == 'María'

    def test_buscar_apoderado_por_dni_existente(self, authenticated_client, setup_basic_data):
        """Prueba buscar apoderado por DNI (existente)"""
        url = reverse('apoderado-buscar')
        response = authenticated_client.get(url, {'dni': '12345678'})
        assert response.status_code == status.HTTP_200_OK
        assert response.data['exists'] is True
        assert response.data['data']['dni'] == '12345678'

    def test_buscar_apoderado_por_dni_no_existente(self, authenticated_client):
        """Prueba buscar apoderado por DNI (no existente)"""
        url = reverse('apoderado-buscar')
        response = authenticated_client.get(url, {'dni': '99999999'})
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data['exists'] is False

    def test_buscar_apoderado_sin_dni(self, authenticated_client):
        """Prueba buscar apoderado sin proporcionar DNI"""
        url = reverse('apoderado-buscar')
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data


@pytest.mark.django_db
class TestParentProfileView:
    """Pruebas para la vista ParentProfileView"""

    def test_get_parent_profile_success(self, api_client, parent_user):
        """Prueba obtener perfil de apoderado (autenticado como parent)"""
        user, apoderado = parent_user
        api_client.force_authenticate(user=user)
        
        url = reverse('parent-profile')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == apoderado.id
        assert response.data['nombres'] == apoderado.nombres

    def test_get_parent_profile_unauthorized(self, api_client, admin_user):
        """Prueba que un usuario no-parent no pueda acceder"""
        api_client.force_authenticate(user=admin_user)
        
        url = reverse('parent-profile')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_parent_profile_no_apoderado(self, api_client):
        """Prueba que un usuario parent sin apoderado asociado falle"""
        user = User.objects.create_user(
            username="parent_sin_apoderado",
            password="pass123",
            is_parent=True,
            apoderado_rel=None
        )
        api_client.force_authenticate(user=user)
        
        url = reverse('parent-profile')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestEstudianteApoderadosView:
    """Pruebas para EstudianteApoderadosView"""

    def test_get_apoderados_by_estudiante(self, authenticated_client, setup_basic_data):
        """Prueba obtener apoderados de un estudiante"""
        estudiante = setup_basic_data['estudiante']
        url = reverse('estudiante-apoderados', args=[estudiante.id])
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['dni'] == '12345678'

    def test_get_apoderados_estudiante_no_existente(self, authenticated_client):
        """Prueba obtener apoderados de estudiante inexistente"""
        url = reverse('estudiante-apoderados', args=[9999])
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestRegistroAlumnoView:
    """Pruebas para RegistroAlumnoView (CRÍTICO)"""

    def test_registro_alumno_completo(self, authenticated_client, setup_basic_data):
        """Prueba registro completo de alumno (estudiante + apoderado)"""
        url = reverse('registro-alumno')
        data = {
            'estudiante': {
                'nombres': 'Ana',
                'apellidos': 'Martínez',
                'fecha_nacimiento': '2021-03-10',
                'dni': '11111111'
            },
            'apoderado': {
                'nombres': 'Pedro',
                'apellidos': 'Martínez',
                'dni': '88888888',
                'telefono': '999888777',
                'email': 'pedro@example.com',
                'direccion': 'Calle 456'
            },
            'tipo_relacion': 'PADRE',
            'es_principal': True
        }
        response = authenticated_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert 'estudiante_id' in response.data
        assert 'apoderado_id' in response.data
        assert 'generated_credentials' in response.data
        assert response.data['generated_credentials']['username'] == '88888888'

        # Verificar que se crearon en BD
        estudiante = Estudiante.objects.get(dni='11111111')
        assert estudiante.nombres == 'Ana'
        
        apoderado = Apoderado.objects.get(dni='88888888')
        assert apoderado.nombres == 'Pedro'
        
        # Verificar relación
        relacion = ApoderadoEstudiante.objects.filter(
            apoderado=apoderado,
            estudiante=estudiante
        ).first()
        assert relacion is not None
        assert relacion.tipo_relacion == 'PADRE'
        assert relacion.es_principal is True

        # Verificar creación de usuario
        usuario = User.objects.filter(username='88888888').first()
        assert usuario is not None
        assert usuario.is_parent is True
        assert usuario.first_login is True

    def test_registro_alumno_apoderado_existente(self, authenticated_client, setup_basic_data):
        """Prueba registro con apoderado ya existente"""
        url = reverse('registro-alumno')
        data = {
            'estudiante': {
                'nombres': 'Luis',
                'apellidos': 'Gómez',
                'fecha_nacimiento': '2020-05-15',
                'dni': '22222222'
            },
            'apoderado': {
                'nombres': 'Carlos',
                'apellidos': 'Gómez',
                'dni': '12345678',
                'telefono': '999888777'
            },
            'tipo_relacion': 'PADRE',
            'es_principal': True
        }
        response = authenticated_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        
        # Verificar que NO se creó un nuevo apoderado
        apoderados_count = Apoderado.objects.filter(dni='12345678').count()
        assert apoderados_count == 1

    def test_registro_alumno_dni_duplicado(self, authenticated_client, setup_basic_data):
        """Prueba registro con DNI de estudiante ya existente"""
        url = reverse('registro-alumno')
        data = {
            'estudiante': {
                'nombres': 'Luis',
                'apellidos': 'Gómez',
                'fecha_nacimiento': '2020-05-15',
                'dni': '87654321'  # DNI duplicado
            },
            'apoderado': {
                'nombres': 'Carlos',
                'apellidos': 'Gómez',
                'dni': '12345678',
                'telefono': '999888777'
            },
            'tipo_relacion': 'PADRE'
        }
        response = authenticated_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'Ya existe un estudiante' in str(response.data)

    def test_registro_alumno_crea_usuario_apoderado(self, authenticated_client):
        """Prueba que se cree usuario para el apoderado si no tiene uno"""
        url = reverse('registro-alumno')
        data = {
            'estudiante': {
                'nombres': 'Ana',
                'apellidos': 'Martínez',
                'fecha_nacimiento': '2021-03-10',
                'dni': '11111111'
            },
            'apoderado': {
                'nombres': 'Pedro',
                'apellidos': 'Martínez',
                'dni': '88888888',
                'telefono': '999888777',
                'email': 'pedro@example.com'
            },
            'tipo_relacion': 'PADRE'
        }
        response = authenticated_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        
        # Verificar usuario creado
        usuario = User.objects.filter(username='88888888').first()
        assert usuario is not None
        assert usuario.apoderado_rel is not None
        assert usuario.is_parent is True


@pytest.mark.django_db
class TestCambiarApoderadoPrincipalView:
    """Pruebas para CambiarApoderadoPrincipalView"""

    def test_cambiar_apoderado_principal(self, authenticated_client, setup_basic_data):
        """Prueba cambiar apoderado principal"""
        estudiante = setup_basic_data['estudiante']
        
        # Crear segundo apoderado
        apoderado2 = Apoderado.objects.create(
            nombres="María",
            apellidos="López",
            dni="87654321",
            telefono="999888777"
        )
        relacion2 = ApoderadoEstudiante.objects.create(
            apoderado=apoderado2,
            estudiante=estudiante,
            tipo_relacion="MADRE",
            es_principal=False
        )
        
        url = reverse('cambiar-apoderado-principal', args=[relacion2.id])
        response = authenticated_client.patch(url)
        assert response.status_code == status.HTTP_200_OK
        assert 'actualizado correctamente' in response.data['message']
        
        # Verificar en BD
        relacion1 = setup_basic_data['relacion']
        relacion1.refresh_from_db()
        relacion2.refresh_from_db()
        
        assert relacion1.es_principal is False
        assert relacion2.es_principal is True

    def test_cambiar_apoderado_principal_no_existente(self, authenticated_client):
        """Prueba cambiar apoderado principal con relación inexistente"""
        url = reverse('cambiar-apoderado-principal', args=[9999])
        response = authenticated_client.patch(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestAgregarApoderadoView:
    """Pruebas para AgregarApoderadoView"""

    def test_agregar_apoderado_existente(self, authenticated_client, setup_basic_data):
        """Prueba agregar apoderado existente a estudiante"""
        estudiante = setup_basic_data['estudiante']
        
        # Crear apoderado existente
        apoderado = Apoderado.objects.create(
            nombres="María",
            apellidos="López",
            dni="87654321",
            telefono="999888777"
        )
        
        url = reverse('agregar-apoderado', args=[estudiante.id])
        data = {
            'dni': '87654321',
            'tipo_relacion': 'MADRE',
            'es_principal': False
        }
        response = authenticated_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert 'agregado correctamente' in response.data['message']
        
        # Verificar relación creada
        relacion = ApoderadoEstudiante.objects.filter(
            apoderado=apoderado,
            estudiante=estudiante
        ).first()
        assert relacion is not None
        assert relacion.tipo_relacion == 'MADRE'

    def test_agregar_apoderado_nuevo(self, authenticated_client, setup_basic_data):
        """Prueba agregar apoderado nuevo a estudiante"""
        estudiante = setup_basic_data['estudiante']
        
        url = reverse('agregar-apoderado', args=[estudiante.id])
        data = {
            'dni': '99999999',
            'nombres': 'Nuevo',
            'apellidos': 'Apoderado',
            'telefono': '999888777',
            'tipo_relacion': 'TUTOR',
            'es_principal': False
        }
        response = authenticated_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        
        # Verificar apoderado creado
        apoderado = Apoderado.objects.filter(dni='99999999').first()
        assert apoderado is not None
        assert apoderado.nombres == 'Nuevo'

    def test_agregar_apoderado_ya_asociado(self, authenticated_client, setup_basic_data):
        """Prueba agregar apoderado que ya está asociado al estudiante"""
        estudiante = setup_basic_data['estudiante']
        apoderado = setup_basic_data['apoderado']
        
        url = reverse('agregar-apoderado', args=[estudiante.id])
        data = {
            'dni': '12345678',
            'tipo_relacion': 'PADRE',
            'es_principal': False
        }
        response = authenticated_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'ya está asociado' in str(response.data)

    def test_agregar_apoderado_estudiante_no_existente(self, authenticated_client):
        """Prueba agregar apoderado a estudiante inexistente"""
        url = reverse('agregar-apoderado', args=[9999])
        data = {
            'dni': '12345678',
            'tipo_relacion': 'PADRE',
            'es_principal': True
        }
        response = authenticated_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestEliminarRelacionApoderadoView:
    """Pruebas para EliminarRelacionApoderadoView"""

    def test_eliminar_relacion(self, authenticated_client, setup_basic_data):
        """Prueba eliminar relación apoderado-estudiante"""
        # Crear segundo apoderado para poder eliminar el principal
        estudiante = setup_basic_data['estudiante']
        apoderado2 = Apoderado.objects.create(
            nombres="María",
            apellidos="López",
            dni="87654321",
            telefono="999888777"
        )
        relacion2 = ApoderadoEstudiante.objects.create(
            apoderado=apoderado2,
            estudiante=estudiante,
            tipo_relacion="MADRE",
            es_principal=False
        )
        
        url = reverse('eliminar-relacion-apoderado', args=[setup_basic_data['relacion'].id])
        response = authenticated_client.delete(url)
        assert response.status_code == status.HTTP_200_OK
        assert 'eliminada correctamente' in response.data['message']
        
        # Verificar que se eliminó
        assert not ApoderadoEstudiante.objects.filter(id=setup_basic_data['relacion'].id).exists()

    def test_eliminar_relacion_ultimo_apoderado(self, authenticated_client, setup_basic_data):
        """Prueba eliminar el último apoderado de un estudiante (debe fallar)"""
        url = reverse('eliminar-relacion-apoderado', args=[setup_basic_data['relacion'].id])
        response = authenticated_client.delete(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'al menos un apoderado' in str(response.data)
        
        # Verificar que no se eliminó
        assert ApoderadoEstudiante.objects.filter(id=setup_basic_data['relacion'].id).exists()

    def test_eliminar_relacion_principal(self, authenticated_client, setup_basic_data):
        """Prueba eliminar apoderado principal (debe asignar otro como principal)"""
        estudiante = setup_basic_data['estudiante']
        
        # Crear segundo apoderado
        apoderado2 = Apoderado.objects.create(
            nombres="María",
            apellidos="López",
            dni="87654321",
            telefono="999888777"
        )
        relacion2 = ApoderadoEstudiante.objects.create(
            apoderado=apoderado2,
            estudiante=estudiante,
            tipo_relacion="MADRE",
            es_principal=False
        )
        
        url = reverse('eliminar-relacion-apoderado', args=[setup_basic_data['relacion'].id])
        response = authenticated_client.delete(url)
        assert response.status_code == status.HTTP_200_OK
        
        # Verificar que el segundo apoderado ahora es principal
        relacion2.refresh_from_db()
        assert relacion2.es_principal is True

    def test_eliminar_relacion_no_existente(self, authenticated_client):
        """Prueba eliminar relación inexistente"""
        url = reverse('eliminar-relacion-apoderado', args=[9999])
        response = authenticated_client.delete(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestEstudianteViewSet:
    """Pruebas para EstudianteViewSet"""

    def test_list_estudiantes(self, authenticated_client, setup_basic_data):
        """Prueba listar estudiantes"""
        url = reverse('estudiante-list')
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 1

    def test_search_estudiante_by_nombre(self, authenticated_client, setup_basic_data):
        """Prueba buscar estudiante por nombre"""
        url = reverse('estudiante-list')
        response = authenticated_client.get(url, {'search': 'Luis'})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 1
        assert 'Luis' in response.data['results'][0]['nombres']

    def test_search_estudiante_by_apoderado_dni(self, authenticated_client, setup_basic_data):
        """Prueba buscar estudiante por DNI de apoderado"""
        url = reverse('estudiante-list')
        response = authenticated_client.get(url, {'search': '12345678'})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 1

    def test_filter_estudiante_by_fecha_nacimiento(self, authenticated_client, setup_basic_data):
        """Prueba filtrar estudiante por fecha de nacimiento"""
        url = reverse('estudiante-list')
        response = authenticated_client.get(url, {'fecha_nacimiento': '2020-05-15'})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 1

    def test_create_estudiante(self, authenticated_client):
        """Prueba crear estudiante"""
        url = reverse('estudiante-list')
        data = {
            'nombres': 'Nuevo',
            'apellidos': 'Estudiante',
            'fecha_nacimiento': '2020-01-01',
            'dni': '55555555'
        }
        response = authenticated_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['nombres'] == 'Nuevo'
        assert response.data['codigo_estudiante'] is not None