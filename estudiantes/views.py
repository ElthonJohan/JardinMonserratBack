from rest_framework import viewsets, filters
from .models import Estudiante, Aula, Apoderado
from .serializers import EstudianteSerializer, AulaSerializer, ApoderadoSerializer
from django_filters.rest_framework import DjangoFilterBackend

class EstudianteViewSet(viewsets.ModelViewSet):
    queryset = Estudiante.objects.all()
    serializer_class = EstudianteSerializer
    
    # Configuramos los backends de filtrado
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    # Filtros exactos (Ej: ?fecha_nacimiento=2020-01-01)
    filterset_fields = ['fecha_nacimiento', 'aula']
    
    # Campos para búsqueda general (Ej: ?search=Juan o ?search=77665544)
    # Usamos '__' para buscar en campos del modelo relacionado (Apoderado)
    search_fields = ['nombres', 'apellidos', 'apoderado__dni', 'apoderado__nombres']
    
    # Campos permitidos para ordenar (Ej: ?ordering=-fecha_nacimiento)
    ordering_fields = ['nombres', 'apellidos', 'fecha_nacimiento']


class AulaViewSet(viewsets.ModelViewSet):
    queryset = Aula.objects.all()
    serializer_class = AulaSerializer


class ApoderadoViewSet(viewsets.ModelViewSet):
    queryset = Apoderado.objects.all()
    serializer_class = ApoderadoSerializer