# usuarios/tests/test_views.py
import pytest
from datetime import date
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth.models import Group

from usuarios.models import Usuario
from estudiantes.models import Apoderado, Estudiante, ApoderadoEstudiante


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
    
    user = Usuario.objects.create_user(
        username="carlos.gomez",
        password="parent123",
        apoderado_rel=apoderado,
        is_parent=True,
        first_login=True
    )
    
    # Crear estudiante relacionado
    estudiante = Estudiante.objects.create(
        nombres="Luis",
        apellidos="Gómez",
        fecha_nacimiento=date(2020, 5, 15),
        dni="87654321"
    )
    
    ApoderadoEstudiante.objects.create(
        apoderado=apoderado,
        estudiante=estudiante,
        tipo_relacion="PADRE",
        es_principal=True
    )
    
    return {
        'user': user,
        'apoderado': apoderado,
        'estudiante': estudiante
    }


@pytest.mark.django_db
class TestCustomTokenObtainPairView:
    """Pruebas para el login con JWT"""

    def test_login_success(self, api_client, parent_user):
        """Prueba login exitoso con credenciales correctas"""
        url = reverse('login_admin')
        data = {
            'username': 'carlos.gomez',
            'password': 'parent123'
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
        assert 'refresh' in response.data

    def test_login_failed_wrong_password(self, api_client, parent_user):
        """Prueba login con contraseña incorrecta"""
        url = reverse('login_admin')
        data = {
            'username': 'carlos.gomez',
            'password': 'wrongpassword'
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_failed_user_not_found(self, api_client):
        """Prueba login con usuario inexistente"""
        url = reverse('login_admin')
        data = {
            'username': 'usuario_inexistente',
            'password': 'password123'
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestLoginParentView:
    """Pruebas para el login de apoderados"""

    def test_login_parent_success(self, api_client, parent_user):
        """Prueba login de apoderado exitoso"""
        url = reverse('login-parent')
        data = {
            'dni': '12345678',
            'password': 'parent123'
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert 'token' in response.data
        assert 'refresh' in response.data
        assert response.data['user']['user_type'] == 'parent'
        assert response.data['user']['first_login'] is True
        assert len(response.data['hijos']) == 1
        assert response.data['hijos'][0]['nombre'] == 'Luis Gómez'
        assert response.data['requires_password_change'] is True

    def test_login_parent_success_after_password_change(self, api_client, parent_user):
        """Prueba login de apoderado después de cambiar contraseña"""
        # Cambiar first_login a False
        user = parent_user['user']
        user.first_login = False
        user.save()
        
        url = reverse('login-parent')
        data = {
            'dni': '12345678',
            'password': 'parent123'
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert response.data.get('requires_password_change', False) is False
        assert 'message' not in response.data

    def test_login_parent_wrong_dni(self, api_client):
        """Prueba login con DNI incorrecto"""
        url = reverse('login-parent')
        data = {
            'dni': '99999999',
            'password': 'parent123'
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert 'DNI no registrado' in str(response.data)

    def test_login_parent_wrong_password(self, api_client, parent_user):
        """Prueba login con contraseña incorrecta"""
        url = reverse('login-parent')
        data = {
            'dni': '12345678',
            'password': 'wrongpassword'
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert 'Credenciales incorrectas' in str(response.data)

    def test_login_parent_missing_dni(self, api_client):
        """Prueba login sin DNI"""
        url = reverse('login-parent')
        data = {
            'password': 'parent123'
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'DNI y contraseña son requeridos' in str(response.data)

    def test_login_parent_missing_password(self, api_client):
        """Prueba login sin contraseña"""
        url = reverse('login-parent')
        data = {
            'dni': '12345678'
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'DNI y contraseña son requeridos' in str(response.data)

    def test_login_parent_apoderado_sin_usuario(self, api_client):
        """Prueba login con apoderado que no tiene usuario asociado"""
        # Crear apoderado sin usuario
        apoderado = Apoderado.objects.create(
            nombres="Pedro",
            apellidos="Martínez",
            dni="87654321",
            telefono="999888777"
        )
        
        url = reverse('login-parent')
        data = {
            'dni': '87654321',
            'password': 'password123'
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert 'Usuario no encontrado' in str(response.data)

    def test_login_parent_apoderado_con_varios_hijos(self, api_client, parent_user):
        """Prueba login con apoderado que tiene varios hijos"""
        apoderado = parent_user['apoderado']
        
        # Crear segundo estudiante
        estudiante2 = Estudiante.objects.create(
            nombres="Ana",
            apellidos="Gómez",
            fecha_nacimiento=date(2021, 3, 10),
            dni="11111111"
        )
        
        ApoderadoEstudiante.objects.create(
            apoderado=apoderado,
            estudiante=estudiante2,
            tipo_relacion="PADRE",
            es_principal=False
        )
        
        url = reverse('login-parent')
        data = {
            'dni': '12345678',
            'password': 'parent123'
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['hijos']) == 2


@pytest.mark.django_db
class TestChangePasswordFirstLogin:
    """Pruebas para cambio de contraseña en primer login"""

    def test_change_password_success(self, authenticated_client, parent_user):
        """Prueba cambio de contraseña exitoso"""
        user = parent_user['user']
        # Autenticar como el usuario apoderado
        client = APIClient()
        client.force_authenticate(user=user)
        
        url = reverse('change-password-first')
        data = {
            'old_password': 'parent123',
            'new_password': 'newpassword123',
            'confirm_password': 'newpassword123'
        }
        response = client.post(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert 'contraseña cambiada' in response.data['message'].lower()
        
        # Verificar que la contraseña cambió
        user.refresh_from_db()
        assert user.check_password('newpassword123') is True
        assert user.first_login is False

    def test_change_password_wrong_old_password(self, authenticated_client, parent_user):
        """Prueba cambio de contraseña con contraseña actual incorrecta"""
        user = parent_user['user']
        client = APIClient()
        client.force_authenticate(user=user)
        
        url = reverse('change-password-first')
        data = {
            'old_password': 'wrongpassword',
            'new_password': 'newpassword123',
            'confirm_password': 'newpassword123'
        }
        response = client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'contraseña actual es incorrecta' in str(response.data)

    def test_change_password_passwords_dont_match(self, authenticated_client, parent_user):
        """Prueba cambio de contraseña con contraseñas que no coinciden"""
        user = parent_user['user']
        client = APIClient()
        client.force_authenticate(user=user)
        
        url = reverse('change-password-first')
        data = {
            'old_password': 'parent123',
            'new_password': 'newpassword123',
            'confirm_password': 'differentpassword'
        }
        response = client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'no coinciden' in str(response.data)

    def test_change_password_too_short(self, authenticated_client, parent_user):
        """Prueba cambio de contraseña con contraseña demasiado corta"""
        user = parent_user['user']
        client = APIClient()
        client.force_authenticate(user=user)
        
        url = reverse('change-password-first')
        data = {
            'old_password': 'parent123',
            'new_password': '123',
            'confirm_password': '123'
        }
        response = client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'al menos 6 caracteres' in str(response.data)

    def test_change_password_missing_fields(self, authenticated_client, parent_user):
        """Prueba cambio de contraseña con campos faltantes"""
        user = parent_user['user']
        client = APIClient()
        client.force_authenticate(user=user)
        
        url = reverse('change-password-first')
        data = {
            'old_password': 'parent123',
            'new_password': 'newpassword123'
            # Falta confirm_password
        }
        response = client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'Todos los campos son requeridos' in str(response.data)

    def test_change_password_unauthorized(self, api_client):
        """Prueba cambio de contraseña sin autenticación"""
        url = reverse('change-password-first')
        data = {
            'old_password': 'parent123',
            'new_password': 'newpassword123',
            'confirm_password': 'newpassword123'
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestUsuarioViewSet:
    """Pruebas para el ViewSet de Usuarios"""

    def test_list_usuarios(self, authenticated_client, parent_user):
        """Prueba listar usuarios"""
        url = reverse('usuarios-list')
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        
        if 'results' in response.data:
            assert len(response.data['results']) >= 1
        else:
            assert len(response.data) >= 1

    def test_create_usuario(self, authenticated_client):
        """Prueba crear usuario"""
        url = reverse('usuarios-list')
        data = {
            'username': 'nuevo_usuario',
            'password': 'password123',
            'email': 'nuevo@example.com',
            'first_name': 'Nuevo',
            'last_name': 'Usuario',
            'is_parent': False
        }
        response = authenticated_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['username'] == 'nuevo_usuario'

    def test_update_usuario(self, authenticated_client, parent_user):
        """Prueba actualizar usuario"""
        user = parent_user['user']
        url = reverse('usuarios-detail', args=[user.id])
        data = {
            'email': 'nuevo_email@example.com',
            'first_name': 'Carlos Actualizado'
        }
        response = authenticated_client.patch(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['email'] == 'nuevo_email@example.com'
        assert response.data['first_name'] == 'Carlos Actualizado'

    def test_delete_usuario(self, authenticated_client, parent_user):
        """Prueba eliminar usuario"""
        user = parent_user['user']
        url = reverse('usuarios-detail', args=[user.id])
        response = authenticated_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Usuario.objects.filter(id=user.id).exists()


@pytest.mark.django_db
class TestRegisterView:
    """Pruebas para el registro de usuarios"""

    def test_register_usuario(self, authenticated_client):
        """Prueba registrar nuevo usuario"""
        url = reverse('register')
        data = {
            'username': 'registro_test',
            'password': 'password123',
            'email': 'registro@example.com',
            'first_name': 'Registro',
            'last_name': 'Test'
        }
        response = authenticated_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['username'] == 'registro_test'
        
        # Verificar que el usuario existe en BD
        usuario = Usuario.objects.get(username='registro_test')
        assert usuario.email == 'registro@example.com'

    def test_register_usuario_duplicado(self, authenticated_client, parent_user):
        """Prueba registrar usuario con username duplicado"""
        url = reverse('register')
        data = {
            'username': 'carlos.gomez',  # Ya existe
            'password': 'password123',
            'email': 'test@example.com'
        }
        response = authenticated_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestPermisoViewSet:
    """Pruebas para el ViewSet de Permisos"""

    def test_list_permisos(self, authenticated_client):
        """Prueba listar permisos"""
        url = reverse('permisos-list')
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)


@pytest.mark.django_db
class TestRoleViewSet:
    """Pruebas para el ViewSet de Roles (Groups)"""

    def test_list_roles(self, authenticated_client):
        """Prueba listar roles"""
        # Crear un grupo de prueba
        Group.objects.create(name='Test Group')
        
        url = reverse('roles-list')
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        
        if 'results' in response.data:
            assert len(response.data['results']) >= 1
        else:
            assert len(response.data) >= 1

    def test_create_role(self, authenticated_client):
        """Prueba crear rol"""
        url = reverse('roles-list')
        data = {
            'name': 'Nuevo Rol'
        }
        response = authenticated_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'Nuevo Rol'
        
        # Verificar en BD
        group = Group.objects.get(name='Nuevo Rol')
        assert group is not None

    def test_update_role(self, authenticated_client):
        """Prueba actualizar rol"""
        group = Group.objects.create(name='Rol Original')
        
        url = reverse('roles-detail', args=[group.id])
        data = {
            'name': 'Rol Actualizado'
        }
        response = authenticated_client.patch(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Rol Actualizado'

    def test_delete_role(self, authenticated_client):
        """Prueba eliminar rol"""
        group = Group.objects.create(name='Rol a Eliminar')
        
        url = reverse('roles-detail', args=[group.id])
        response = authenticated_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Group.objects.filter(id=group.id).exists()


@pytest.mark.django_db
class TestUsuarioAuthorization:
    """Pruebas de autorización para usuarios"""

    def test_list_usuarios_unauthorized(self, api_client):
        """Prueba que usuarios no autenticados no puedan listar usuarios"""
        url = reverse('usuarios-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_parent_unauthorized_access(self, api_client):
        """Prueba que el endpoint login_parent sea público"""
        url = reverse('login-parent')
        data = {
            'dni': '12345678',
            'password': 'test'
        }
        # No necesita autenticación
        response = api_client.post(url, data, format='json')
        # No debe ser 401, debe ser 404 o 400 por DNI incorrecto
        assert response.status_code in [status.HTTP_404_NOT_FOUND, status.HTTP_400_BAD_REQUEST]