# notificaciones/tests/test_models.py
import pytest
from datetime import date

from notificaciones.models import Notificacion
from usuarios.models import Usuario
from estudiantes.models import Estudiante, Apoderado, ApoderadoEstudiante


@pytest.mark.django_db
class TestNotificacionModel:
    """Pruebas para el modelo Notificacion"""

    @pytest.fixture
    def setup_notificacion_data(self):
        """Configuración base para pruebas de notificación"""
        # Crear usuario
        usuario = Usuario.objects.create_user(
            username="testuser",
            password="test123",
            email="test@example.com"
        )
        
        # Crear estudiante (opcional)
        apoderado = Apoderado.objects.create(
            nombres="Carlos",
            apellidos="Gómez",
            dni="12345678",
            telefono="999888777"
        )
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
            'usuario': usuario,
            'estudiante': estudiante
        }

    def test_crear_notificacion(self, setup_notificacion_data):
        """Prueba creación básica de notificación"""
        data = setup_notificacion_data
        notificacion = Notificacion.objects.create(
            usuario=data['usuario'],
            titulo="Pago Registrado",
            mensaje="Se ha registrado un nuevo pago",
            tipo="PAGO_REGISTRADO",
            leido=False
        )
        
        assert notificacion.usuario == data['usuario']
        assert notificacion.titulo == "Pago Registrado"
        assert notificacion.mensaje == "Se ha registrado un nuevo pago"
        assert notificacion.tipo == "PAGO_REGISTRADO"
        assert notificacion.leido is False
        assert notificacion.alumno is None
        assert notificacion.ruta is None
        assert notificacion.fecha_creacion is not None

    def test_crear_notificacion_con_alumno(self, setup_notificacion_data):
        """Prueba creación de notificación con alumno asociado"""
        data = setup_notificacion_data
        notificacion = Notificacion.objects.create(
            usuario=data['usuario'],
            alumno=data['estudiante'],
            titulo="Pago Aprobado",
            mensaje="El pago ha sido aprobado",
            tipo="PAGO_APROBADO"
        )
        
        assert notificacion.alumno == data['estudiante']
        assert notificacion.tipo == "PAGO_APROBADO"

    def test_crear_notificacion_con_ruta(self, setup_notificacion_data):
        """Prueba creación de notificación con ruta"""
        data = setup_notificacion_data
        notificacion = Notificacion.objects.create(
            usuario=data['usuario'],
            titulo="Ver pago",
            mensaje="Haga clic para ver el pago",
            tipo="SISTEMA",
            ruta="/pagos/1"
        )
        
        assert notificacion.ruta == "/pagos/1"

    def test_notificacion_tipos_validos(self, setup_notificacion_data):
        """Prueba que los tipos de notificación válidos funcionen"""
        data = setup_notificacion_data
        tipos = ['PAGO_REGISTRADO', 'PAGO_APROBADO', 'PAGO_RECHAZADO', 'SISTEMA']
        
        for tipo in tipos:
            notificacion = Notificacion.objects.create(
                usuario=data['usuario'],
                titulo=f"Notificación {tipo}",
                mensaje=f"Mensaje para {tipo}",
                tipo=tipo
            )
            assert notificacion.tipo == tipo

    def test_notificacion_leido_por_defecto(self, setup_notificacion_data):
        """Prueba que leido sea False por defecto"""
        data = setup_notificacion_data
        notificacion = Notificacion.objects.create(
            usuario=data['usuario'],
            titulo="Notificación de prueba",
            mensaje="Mensaje de prueba"
        )
        assert notificacion.leido is False

    def test_notificacion_str_no_leida(self, setup_notificacion_data):
        """Prueba el string de notificación no leída"""
        data = setup_notificacion_data
        notificacion = Notificacion.objects.create(
            usuario=data['usuario'],
            titulo="Pago Registrado",
            mensaje="Se ha registrado un nuevo pago",
            tipo="PAGO_REGISTRADO",
            leido=False
        )
        expected = f"[PAGO_REGISTRADO] Pago Registrado - {data['usuario']} (No Leída)"
        assert str(notificacion) == expected

    def test_notificacion_str_leida(self, setup_notificacion_data):
        """Prueba el string de notificación leída"""
        data = setup_notificacion_data
        notificacion = Notificacion.objects.create(
            usuario=data['usuario'],
            titulo="Pago Aprobado",
            mensaje="El pago ha sido aprobado",
            tipo="PAGO_APROBADO",
            leido=True
        )
        expected = f"[PAGO_APROBADO] Pago Aprobado - {data['usuario']} (Leída)"
        assert str(notificacion) == expected

    def test_notificacion_ordenamiento(self, setup_notificacion_data):
        """Prueba que las notificaciones se ordenen por fecha descendente"""
        data = setup_notificacion_data
        
        notificacion1 = Notificacion.objects.create(
            usuario=data['usuario'],
            titulo="Notificación 1",
            mensaje="Mensaje 1"
        )
        
        notificacion2 = Notificacion.objects.create(
            usuario=data['usuario'],
            titulo="Notificación 2",
            mensaje="Mensaje 2"
        )
        
        notificaciones = Notificacion.objects.all()
        # La más reciente debe ser la primera
        assert notificaciones[0].fecha_creacion >= notificaciones[1].fecha_creacion

    def test_notificacion_por_usuario(self, setup_notificacion_data):
        """Prueba filtrar notificaciones por usuario"""
        data = setup_notificacion_data
        
        # Crear otro usuario
        usuario2 = Usuario.objects.create_user(
            username="testuser2",
            password="test456"
        )
        
        # Notificación para usuario 1
        Notificacion.objects.create(
            usuario=data['usuario'],
            titulo="Notificación para usuario 1",
            mensaje="Mensaje"
        )
        
        # Notificación para usuario 2
        Notificacion.objects.create(
            usuario=usuario2,
            titulo="Notificación para usuario 2",
            mensaje="Mensaje"
        )
        
        # Verificar que cada usuario ve sus notificaciones
        notificaciones_user1 = Notificacion.objects.filter(usuario=data['usuario'])
        notificaciones_user2 = Notificacion.objects.filter(usuario=usuario2)
        
        assert notificaciones_user1.count() == 1
        assert notificaciones_user2.count() == 1
        assert notificaciones_user1[0].titulo == "Notificación para usuario 1"
        assert notificaciones_user2[0].titulo == "Notificación para usuario 2"