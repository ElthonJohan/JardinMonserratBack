# usuarios/tests/test_models.py
import pytest
from datetime import date

from usuarios.models import Usuario
from estudiantes.models import Apoderado, Estudiante, ApoderadoEstudiante


@pytest.mark.django_db
class TestUsuarioModel:
    """Pruebas para el modelo Usuario"""

    def test_crear_usuario_basico(self):
        """Prueba creación de usuario básico"""
        usuario = Usuario.objects.create_user(
            username="testuser",
            password="test123",
            email="test@example.com"
        )
        
        assert usuario.username == "testuser"
        assert usuario.email == "test@example.com"
        assert usuario.is_parent is False
        assert usuario.first_login is True
        assert usuario.apoderado_rel is None
        assert usuario.check_password("test123") is True
        assert str(usuario) == "testuser"

    def test_crear_usuario_con_apoderado(self):
        """Prueba creación de usuario con apoderado asociado"""
        # Crear apoderado
        apoderado = Apoderado.objects.create(
            nombres="Carlos",
            apellidos="Gómez",
            dni="12345678",
            telefono="999888777"
        )
        
        usuario = Usuario.objects.create_user(
            username="carlos.gomez",
            password="test123",
            email="carlos@example.com",
            apoderado_rel=apoderado,
            is_parent=True,
            first_login=True
        )
        
        assert usuario.apoderado_rel == apoderado
        assert usuario.is_parent is True
        assert usuario.first_login is True

    def test_usuario_is_parent_por_defecto(self):
        """Prueba que is_parent sea False por defecto"""
        usuario = Usuario.objects.create_user(
            username="testuser",
            password="test123"
        )
        assert usuario.is_parent is False

    def test_usuario_first_login_por_defecto(self):
        """Prueba que first_login sea True por defecto"""
        usuario = Usuario.objects.create_user(
            username="testuser",
            password="test123"
        )
        assert usuario.first_login is True

    def test_usuario_sin_apoderado(self):
        """Prueba usuario sin apoderado asociado"""
        usuario = Usuario.objects.create_user(
            username="admin",
            password="admin123",
            is_staff=True
        )
        assert usuario.apoderado_rel is None
        assert usuario.is_parent is False

    def test_usuario_con_apoderado_y_estudiantes(self):
        """Prueba que un apoderado pueda tener múltiples estudiantes"""
        # Crear apoderado
        apoderado = Apoderado.objects.create(
            nombres="Carlos",
            apellidos="Gómez",
            dni="12345678",
            telefono="999888777"
        )
        
        # Crear usuario apoderado
        usuario = Usuario.objects.create_user(
            username="carlos.gomez",
            password="test123",
            apoderado_rel=apoderado,
            is_parent=True
        )
        
        # Crear estudiantes
        estudiante1 = Estudiante.objects.create(
            nombres="Luis",
            apellidos="Gómez",
            fecha_nacimiento=date(2020, 5, 15),
            dni="87654321"
        )
        estudiante2 = Estudiante.objects.create(
            nombres="Ana",
            apellidos="Gómez",
            fecha_nacimiento=date(2021, 3, 10),
            dni="11111111"
        )
        
        # Crear relaciones
        ApoderadoEstudiante.objects.create(
            apoderado=apoderado,
            estudiante=estudiante1,
            tipo_relacion="PADRE",
            es_principal=True
        )
        ApoderadoEstudiante.objects.create(
            apoderado=apoderado,
            estudiante=estudiante2,
            tipo_relacion="PADRE",
            es_principal=False
        )
        
        # Verificar que el apoderado tiene 2 estudiantes
        estudiantes = ApoderadoEstudiante.objects.filter(apoderado=apoderado)
        assert estudiantes.count() == 2
        assert usuario.is_parent is True