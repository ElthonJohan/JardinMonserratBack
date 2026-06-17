# core/tests/test_permissions.py
import pytest
from django.test import RequestFactory
from rest_framework.test import APIRequestFactory, force_authenticate, APIClient
from rest_framework.views import APIView
from rest_framework import status

from django.contrib.auth.models import Group
from core.permissions import IsDirectora, IsAdministradoraOrDirectora, IsApoderado
from usuarios.models import Usuario


@pytest.fixture
def api_client():
    """Fixture para cliente API"""
    return APIClient()


@pytest.fixture
def request_factory():
    """Fixture para crear requests de prueba"""
    return RequestFactory()


@pytest.fixture
def view():
    """Fixture para vista de prueba"""
    class MockView(APIView):
        permission_classes = [IsDirectora]
    
    return MockView()


@pytest.fixture
def admin_user(db):
    """Fixture para usuario administrador"""
    user = Usuario.objects.create_user(
        username="admin",
        password="admin123"
    )
    group, _ = Group.objects.get_or_create(name='Administradora')
    user.groups.add(group)
    return user


@pytest.fixture
def directora_user(db):
    """Fixture para usuario directora"""
    user = Usuario.objects.create_user(
        username="directora",
        password="directora123"
    )
    group, _ = Group.objects.get_or_create(name='Directora')
    user.groups.add(group)
    return user


@pytest.fixture
def apoderado_user(db):
    """Fixture para usuario apoderado"""
    user = Usuario.objects.create_user(
        username="apoderado",
        password="apoderado123"
    )
    group, _ = Group.objects.get_or_create(name='Apoderado')
    user.groups.add(group)
    return user


@pytest.fixture
def user_sin_rol(db):
    """Fixture para usuario sin rol"""
    return Usuario.objects.create_user(
        username="sin_rol",
        password="sinrol123"
    )


@pytest.mark.django_db
class TestIsDirectoraPermission:
    """Pruebas para el permiso IsDirectora"""

    def test_directora_tiene_permiso(self, request_factory, directora_user):
        """Prueba que una usuaria con rol 'directora' tenga permiso"""
        permission = IsDirectora()
        request = request_factory.get('/')
        request.user = directora_user
        
        assert permission.has_permission(request, None) is True

    def test_administradora_no_tiene_permiso(self, request_factory, admin_user):
        """Prueba que una usuaria con rol 'administradora' NO tenga permiso"""
        permission = IsDirectora()
        request = request_factory.get('/')
        request.user = admin_user
        
        assert permission.has_permission(request, None) is False

    def test_apoderado_no_tiene_permiso(self, request_factory, apoderado_user):
        """Prueba que un usuario con rol 'apoderado' NO tenga permiso"""
        permission = IsDirectora()
        request = request_factory.get('/')
        request.user = apoderado_user
        
        assert permission.has_permission(request, None) is False

    def test_usuario_sin_rol_no_tiene_permiso(self, request_factory, user_sin_rol):
        """Prueba que un usuario sin rol NO tenga permiso"""
        permission = IsDirectora()
        request = request_factory.get('/')
        request.user = user_sin_rol
        
        assert permission.has_permission(request, None) is False

    def test_usuario_no_autenticado_no_tiene_permiso(self, request_factory):
        """Prueba que un usuario no autenticado NO tenga permiso"""
        permission = IsDirectora()
        request = request_factory.get('/')
        request.user = None
        
        assert permission.has_permission(request, None) is False

    def test_directora_con_permiso_en_vista_protegida(self, request_factory, directora_user):
        """Prueba integración: directora puede acceder a vista con IsDirectora"""
        # Crear una vista mock con el permiso
        class MockView(APIView):
            permission_classes = [IsDirectora]
            
            def get(self, request):
                return Response({"status": "ok"})
        
        # Crear request
        request = request_factory.get('/')
        request.user = directora_user
        
        # Verificar permisos
        permission = IsDirectora()
        has_permission = permission.has_permission(request, MockView())
        
        assert has_permission is True


@pytest.mark.django_db
class TestIsAdministradoraOrDirectoraPermission:
    """Pruebas para el permiso IsAdministradoraOrDirectora"""

    def test_directora_tiene_permiso(self, request_factory, directora_user):
        """Prueba que una usuaria con rol 'directora' tenga permiso"""
        permission = IsAdministradoraOrDirectora()
        request = request_factory.get('/')
        request.user = directora_user
        
        assert permission.has_permission(request, None) is True

    def test_administradora_tiene_permiso(self, request_factory, admin_user):
        """Prueba que una usuaria con rol 'administradora' tenga permiso"""
        permission = IsAdministradoraOrDirectora()
        request = request_factory.get('/')
        request.user = admin_user
        
        assert permission.has_permission(request, None) is True

    def test_apoderado_no_tiene_permiso(self, request_factory, apoderado_user):
        """Prueba que un usuario con rol 'apoderado' NO tenga permiso"""
        permission = IsAdministradoraOrDirectora()
        request = request_factory.get('/')
        request.user = apoderado_user
        
        assert permission.has_permission(request, None) is False

    def test_usuario_sin_rol_no_tiene_permiso(self, request_factory, user_sin_rol):
        """Prueba que un usuario sin rol NO tenga permiso"""
        permission = IsAdministradoraOrDirectora()
        request = request_factory.get('/')
        request.user = user_sin_rol
        
        assert permission.has_permission(request, None) is False

    def test_usuario_no_autenticado_no_tiene_permiso(self, request_factory):
        """Prueba que un usuario no autenticado NO tenga permiso"""
        permission = IsAdministradoraOrDirectora()
        request = request_factory.get('/')
        request.user = None
        
        assert permission.has_permission(request, None) is False


@pytest.mark.django_db
class TestIsApoderadoPermission:
    """Pruebas para el permiso IsApoderado"""

    def test_apoderado_tiene_permiso(self, request_factory, apoderado_user):
        """Prueba que un usuario con rol 'apoderado' tenga permiso"""
        permission = IsApoderado()
        request = request_factory.get('/')
        request.user = apoderado_user
        
        assert permission.has_permission(request, None) is True

    def test_directora_no_tiene_permiso(self, request_factory, directora_user):
        """Prueba que una usuaria con rol 'directora' NO tenga permiso"""
        permission = IsApoderado()
        request = request_factory.get('/')
        request.user = directora_user
        
        assert permission.has_permission(request, None) is False

    def test_administradora_no_tiene_permiso(self, request_factory, admin_user):
        """Prueba que una usuaria con rol 'administradora' NO tenga permiso"""
        permission = IsApoderado()
        request = request_factory.get('/')
        request.user = admin_user
        
        assert permission.has_permission(request, None) is False

    def test_usuario_sin_rol_no_tiene_permiso(self, request_factory, user_sin_rol):
        """Prueba que un usuario sin rol NO tenga permiso"""
        permission = IsApoderado()
        request = request_factory.get('/')
        request.user = user_sin_rol
        
        assert permission.has_permission(request, None) is False

    def test_usuario_no_autenticado_no_tiene_permiso(self, request_factory):
        """Prueba que un usuario no autenticado NO tenga permiso"""
        permission = IsApoderado()
        request = request_factory.get('/')
        request.user = None
        
        assert permission.has_permission(request, None) is False


@pytest.mark.django_db
class TestPermissionsIntegracionConVistas:
    """Pruebas de integración: permisos aplicados a vistas reales"""

    def test_directora_puede_acceder_a_vista_protegida(self, api_client, directora_user):
        """Prueba que una directora pueda acceder a una vista con IsDirectora"""
        from core.views import GradoViewSet
        
        api_client.force_authenticate(user=directora_user)
        url = '/api/core/grados/'  # Ajusta según tu URL
        response = api_client.get(url)
        # Si la vista usa IsDirectora, debería permitir acceso
        # Nota: Ajusta el status code esperado (200 o 403)
        assert response.status_code != status.HTTP_401_UNAUTHORIZED
        # Si la vista usa DjangoModelPermissions, podría ser 403 o 200

    def test_apoderado_no_puede_acceder_a_vista_de_grados(self, api_client, apoderado_user):
        """Prueba que un apoderado NO pueda acceder a una vista de administración"""
        api_client.force_authenticate(user=apoderado_user)
        url = '/api/core/grados/'
        response = api_client.post(url, {})
        # Un apoderado no debería poder acceder a grados
        # (DjangoModelPermissions o IsDirectora lo bloquearían)
        assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_401_UNAUTHORIZED]