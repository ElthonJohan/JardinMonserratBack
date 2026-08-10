from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from .models import Matricula, PeriodoAcademico
from .serializers import MatriculaSerializer, PeriodoAcademicoSerializer


class MatriculaViewSet(viewsets.ModelViewSet):
    queryset = Matricula.objects.all()
    serializer_class = MatriculaSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = [
        'alumno__nombres', 'alumno__apellidos',
        'aula__nombre','periodo_academico__nombre', 'periodo_academico__anio'
    ]
    ordering_fields = ['periodo_academico__anio', 'fecha_matricula', 'estado']
    ordering = ['-periodo_academico__anio', '-fecha_matricula']

class PeriodoAcademicoViewSet(viewsets.ModelViewSet):
    queryset = PeriodoAcademico.objects.all()
    serializer_class = PeriodoAcademicoSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nombre', 'anio']
    ordering_fields = ['anio', 'fecha_inicio']
    ordering = ['-anio', '-fecha_inicio']