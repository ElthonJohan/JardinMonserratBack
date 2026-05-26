from rest_framework import viewsets, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import ApoderadoProfileSerializer
from .models import Estudiante, Aula, Apoderado
from .serializers import EstudianteSerializer, AulaSerializer, ApoderadoSerializer
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticated, DjangoModelPermissions

class EstudianteViewSet(viewsets.ModelViewSet):
    queryset = Estudiante.objects.all()
    serializer_class = EstudianteSerializer
    permission_classes = [IsAuthenticated, DjangoModelPermissions]
    
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
    permission_classes = [IsAuthenticated, DjangoModelPermissions]

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nombre']
    ordering_fields = ['nombre']
    


class ApoderadoViewSet(viewsets.ModelViewSet):
    queryset = Apoderado.objects.all()
    serializer_class = ApoderadoSerializer
    permission_classes = [IsAuthenticated, DjangoModelPermissions]



class ParentProfileView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        user = request.user

        # VALIDAR QUE SEA APODERADO
        if not user.is_parent:
            return Response(
                {"detail": "No autorizado"},
                status=403
            )

        # OBTENER APODERADO
        apoderado = user.apoderado_rel

        serializer = ApoderadoProfileSerializer(apoderado)

        return Response(serializer.data)