from rest_framework import viewsets, filters
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from .serializers import ApoderadoProfileSerializer, RegistroAlumnoSerializer
from .models import ApoderadoEstudiante, Estudiante, Aula, Apoderado
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

    @action(detail=False, methods=['get'])
    def buscar(self, request):

        dni = request.query_params.get('dni')

        if not dni:
            return Response(
                {"error": "Debe proporcionar un DNI"},
                status=status.HTTP_400_BAD_REQUEST
            )

        apoderado = Apoderado.objects.filter(
            dni=dni
        ).first()

        if not apoderado:
            return Response(
                {"exists": False},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = self.get_serializer(apoderado)

        return Response({
            "exists": True,
            "data": serializer.data
        })



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
    

class RegistroAlumnoView(APIView):

    @transaction.atomic
    def post(self, request):

        serializer = RegistroAlumnoSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        data = serializer.validated_data

        estudiante_data = data['estudiante']
        apoderado_data = data['apoderado']

        # 👇 AQUÍ VA ESTE CÓDIGO
        apoderado = Apoderado.objects.filter(dni=apoderado_data["dni"]).first()

        if not apoderado:
            apoderado = Apoderado.objects.create(
                **apoderado_data
            )

        dni_estudiante = estudiante_data.get("dni")

        if dni_estudiante:
            existe = Estudiante.objects.filter(
                dni=dni_estudiante
            ).exists()

            if existe:
                return Response(
                    {
                        "error": "Ya existe un estudiante con ese DNI"
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

        estudiante = Estudiante.objects.create(
            **estudiante_data
        )

        if ApoderadoEstudiante.objects.filter(
            apoderado=apoderado,
            estudiante=estudiante
        ).exists():

            return Response(
                {
                    "error": "La relación ya existe"
                },
                status=status.HTTP_400_BAD_REQUEST
            )    

        ApoderadoEstudiante.objects.create(
            apoderado=apoderado,
            estudiante=estudiante,
            tipo_relacion=data['tipo_relacion'],
            es_principal=data['es_principal']
        )

        return Response(
        {
            "message": "Alumno registrado correctamente",
            "estudiante_id": estudiante.id,
            "apoderado_id": apoderado.id
        },
        status=status.HTTP_201_CREATED
)