from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, DjangoModelPermissions
from .models import Grado, Seccion, Alumno
from .serializers import GradoSerializer, SeccionSerializer, AlumnoSerializer


class GradoViewSet(viewsets.ModelViewSet):
    queryset = Grado.objects.filter(activo=True)
    serializer_class = GradoSerializer
    permission_classes = [IsAuthenticated, DjangoModelPermissions]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nombre', 'nivel']
    ordering_fields = ['orden', 'nombre']
    ordering = ['orden']


class SeccionViewSet(viewsets.ModelViewSet):
    queryset = Seccion.objects.filter(activo=True)
    serializer_class = SeccionSerializer
    permission_classes = [IsAuthenticated, DjangoModelPermissions]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nombre']
    ordering_fields = ['nombre']
    ordering = ['nombre']


class AlumnoViewSet(viewsets.ModelViewSet):
    queryset = Alumno.objects.all()
    serializer_class = AlumnoSerializer
    permission_classes = [IsAuthenticated, DjangoModelPermissions]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nombres', 'apellidos', 'dni', 'nro_matricula', 'email_apoderado']
    ordering_fields = ['apellidos', 'nombres', 'fecha_creacion', 'estado']
    ordering = ['apellidos', 'nombres']
    
    @action(detail=False, methods=['get'])
    def activos(self, request):
        """Obtener solo alumnos activos"""
        alumnos = Alumno.objects.filter(estado='Activo')
        serializer = self.get_serializer(alumnos, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def por_estado(self, request):
        """Filtrar alumnos por estado"""
        estado = request.query_params.get('estado', None)
        if estado:
            alumnos = Alumno.objects.filter(estado=estado)
        else:
            alumnos = Alumno.objects.all()
        serializer = self.get_serializer(alumnos, many=True)
        return Response(serializer.data)
