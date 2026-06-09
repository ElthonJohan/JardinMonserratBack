from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Notificacion
from .serializers import NotificacionSerializer



class NotificacionViewSet(viewsets.ReadOnlyModelViewSet):

    serializer_class = NotificacionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            Notificacion.objects
            .filter(usuario=self.request.user)
            .order_by('-fecha_creacion')
        )

    @action(detail=True, methods=['patch'])
    def marcar_leido(self, request, pk=None):

        notificacion = self.get_object()

        notificacion.leido = True
        notificacion.save()

        return Response({
            'status': 'Notificación marcada como leída'
        })
    @action(detail=False, methods=['patch'])
    def marcar_todas(self, request):

        self.get_queryset().filter(
            leido=False
        ).update(
            leido=True
        )

        return Response({
            "message":
            "Todas las notificaciones fueron marcadas como leídas"
        })

    @action(detail=False, methods=['get'])
    def count(self, request):

        total = (
            self.get_queryset()
            .filter(leido=False)
            .count()
        )

        return Response({
            "count": total
        })
