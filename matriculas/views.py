from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from .models import Matricula
from .serializers import MatriculaSerializer


class MatriculaViewSet(viewsets.ModelViewSet):
    queryset = Matricula.objects.all()
    serializer_class = MatriculaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = [
        'alumno__nombres', 'alumno__apellidos',
        'aula__nombre', 'anio'
    ]
    ordering_fields = ['anio', 'fecha_matricula', 'estado']
    ordering = ['-anio', '-fecha_matricula']
