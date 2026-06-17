# notificaciones/tests/test_views.py
import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from notificaciones.models import Notificacion
from usuarios.models import Usuario


@pytest.fixture
def api_client():
    """Fixture para cliente API"""
    return APIClient()


@pytest.fixture
def user(db):
    """Fixture para usuario normal"""
    user = Usuario.objects.create_user(
        username="testuser",
        password="test123",
        email="test@example.com"
    )
    return user


@pytest.fixture
def authenticated_client(api_client, user):
    """Fixture para cliente autenticado"""
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def setup_notificaciones(db, user):
    """Configuración base con notificaciones"""
    notificaciones = []
    for i in range(5):
        notificacion = Notificacion.objects.create(
            usuario=user,
            titulo=f"Notificación {i+1}",
            mensaje=f"Mensaje {i+1}",
            tipo="SISTEMA" if i % 2 == 0 else "PAGO_REGISTRADO",
            leido=i % 2 != 0  # Alternar leído/no leído
        )
        notificaciones.append(notificacion)
    return notificaciones


@pytest.mark.django_db
class TestNotificacionViewSet:
    """Pruebas para el ViewSet de Notificaciones"""

    def test_list_notificaciones(self, authenticated_client, setup_notificaciones):
        """Prueba listar notificaciones del usuario autenticado"""
        url = reverse('notificacion-list')
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        
        # Verificar paginación
        if 'results' in response.data:
            assert len(response.data['results']) == 5
            # Verificar orden descendente por fecha
            assert response.data['results'][0]['titulo'] == 'Notificación 5'
        else:
            assert len(response.data) == 5

    def test_list_notificaciones_unauthorized(self, api_client):
        """Prueba que usuarios no autenticados no puedan listar notificaciones"""
        url = reverse('notificacion-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_notificacion_solo_muestra_del_usuario(self, api_client, user):
        """Prueba que un usuario solo vea sus propias notificaciones"""
        # Crear otro usuario
        user2 = Usuario.objects.create_user(
            username="testuser2",
            password="test456"
        )
        
        # Crear notificaciones para ambos usuarios
        Notificacion.objects.create(
            usuario=user,
            titulo="Notificación usuario 1",
            mensaje="Mensaje",
            tipo="SISTEMA"
        )
        Notificacion.objects.create(
            usuario=user2,
            titulo="Notificación usuario 2",
            mensaje="Mensaje",
            tipo="SISTEMA"
        )
        
        # Autenticar como user
        api_client.force_authenticate(user=user)
        url = reverse('notificacion-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        
        if 'results' in response.data:
            assert len(response.data['results']) == 1
            assert response.data['results'][0]['titulo'] == 'Notificación usuario 1'
        else:
            assert len(response.data) == 1
            assert response.data[0]['titulo'] == 'Notificación usuario 1'

    def test_marcar_notificacion_como_leida(self, authenticated_client, setup_notificaciones):
        """Prueba marcar una notificación como leída"""
        notificacion = setup_notificaciones[0]  # La primera está no leída
        assert notificacion.leido is False
        
        url = reverse('notificacion-marcar-leido', args=[notificacion.id])
        response = authenticated_client.patch(url)
        assert response.status_code == status.HTTP_200_OK
        assert 'marcada como leída' in response.data['status']
        
        # Verificar en BD
        notificacion.refresh_from_db()
        assert notificacion.leido is True

    def test_marcar_notificacion_ya_leida(self, authenticated_client, setup_notificaciones):
        """Prueba marcar una notificación ya leída como leída (no debería cambiar)"""
        notificacion = setup_notificaciones[1]  # La segunda está leída
        assert notificacion.leido is True
        
        url = reverse('notificacion-marcar-leido', args=[notificacion.id])
        response = authenticated_client.patch(url)
        assert response.status_code == status.HTTP_200_OK
        
        notificacion.refresh_from_db()
        assert notificacion.leido is True

    def test_marcar_notificacion_inexistente(self, authenticated_client):
        """Prueba marcar notificación inexistente"""
        url = reverse('notificacion-marcar-leido', args=[9999])
        response = authenticated_client.patch(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_marcar_notificacion_de_otro_usuario(self, api_client, user):
        """Prueba que un usuario no pueda marcar notificaciones de otro usuario"""
        # Crear otro usuario y su notificación
        user2 = Usuario.objects.create_user(
            username="testuser2",
            password="test456"
        )
        notificacion = Notificacion.objects.create(
            usuario=user2,
            titulo="Notificación de otro usuario",
            mensaje="Mensaje",
            tipo="SISTEMA"
        )
        
        # Autenticar como user (no el dueño)
        api_client.force_authenticate(user=user)
        url = reverse('notificacion-marcar-leido', args=[notificacion.id])
        response = api_client.patch(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_marcar_todas_notificaciones(self, authenticated_client, setup_notificaciones, user):
        """Prueba marcar todas las notificaciones como leídas"""
        # Verificar que hay no leídas
        no_leidas = Notificacion.objects.filter(leido=False, usuario=user)
        assert no_leidas.count() >= 1
        
        url = reverse('notificacion-marcar-todas')
        response = authenticated_client.patch(url)
        assert response.status_code == status.HTTP_200_OK
        assert 'marcadas como leídas' in response.data['message']
        
        # Verificar que todas están leídas
        todas = Notificacion.objects.filter(usuario=user)
        for notif in todas:
            assert notif.leido is True

    def test_marcar_todas_sin_notificaciones(self, authenticated_client):
        """Prueba marcar todas cuando no hay notificaciones"""
        url = reverse('notificacion-marcar-todas')
        response = authenticated_client.patch(url)
        assert response.status_code == status.HTTP_200_OK
        assert 'marcadas como leídas' in response.data['message']

    def test_count_notificaciones_no_leidas(self, authenticated_client, setup_notificaciones, user):
        """Prueba contar notificaciones no leídas"""
        url = reverse('notificacion-count')
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert 'count' in response.data
        
        # Contar manualmente las no leídas
        no_leidas = Notificacion.objects.filter(
            usuario=user,
            leido=False
        ).count()
        assert response.data['count'] == no_leidas

    def test_count_notificaciones_despues_de_marcar(self, authenticated_client, setup_notificaciones):
        """Prueba contar notificaciones después de marcar algunas como leídas"""
        # Obtener count inicial
        url = reverse('notificacion-count')
        response = authenticated_client.get(url)
        count_inicial = response.data['count']
        
        # Marcar una notificación como leída
        notificacion = Notificacion.objects.filter(leido=False).first()
        url_marcar = reverse('notificacion-marcar-leido', args=[notificacion.id])
        authenticated_client.patch(url_marcar)
        
        # Verificar count disminuyó
        response = authenticated_client.get(reverse('notificacion-count'))
        assert response.data['count'] == count_inicial - 1

    def test_count_notificaciones_unauthorized(self, api_client):
        """Prueba que usuarios no autenticados no puedan contar notificaciones"""
        url = reverse('notificacion-count')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_count_solo_del_usuario(self, api_client, user):
        """Prueba que el count solo cuente notificaciones del usuario autenticado"""
        # Crear otro usuario
        user2 = Usuario.objects.create_user(
            username="testuser2",
            password="test456"
        )
        
        # Crear notificaciones no leídas para ambos
        Notificacion.objects.create(
            usuario=user,
            titulo="Notif user1",
            mensaje="Mensaje",
            tipo="SISTEMA",
            leido=False
        )
        Notificacion.objects.create(
            usuario=user,
            titulo="Notif user1 2",
            mensaje="Mensaje",
            tipo="SISTEMA",
            leido=False
        )
        Notificacion.objects.create(
            usuario=user2,
            titulo="Notif user2",
            mensaje="Mensaje",
            tipo="SISTEMA",
            leido=False
        )
        
        # Autenticar como user
        api_client.force_authenticate(user=user)
        url = reverse('notificacion-count')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 2

    def test_ordenamiento_notificaciones(self, authenticated_client, setup_notificaciones):
        """Prueba que las notificaciones se ordenen por fecha descendente"""
        url = reverse('notificacion-list')
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        
        if 'results' in response.data:
            resultados = response.data['results']
            # La primera debe ser la más reciente
            for i in range(len(resultados) - 1):
                assert resultados[i]['fecha_creacion'] >= resultados[i+1]['fecha_creacion']