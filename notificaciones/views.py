from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Notificacion
from .serializers import NotificacionSerializer

class NotificacionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para notificaciones. Devuelve solo las del usuario autenticado.
    Permite marcar como leída mediante PATCH o acción custom.
    """
    serializer_class = NotificacionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Filtramos para devolver solo las notificaciones del request.user
        return Notificacion.objects.filter(usuario=self.request.user).order_by('-fecha_creacion')

    @action(detail=True, methods=['patch'])
    def marcar_leido(self, request, pk=None):
        notificacion = self.get_object()
        notificacion.leido = True
        notificacion.save()
        return Response({'status': 'Notificación marcada como leída'})
