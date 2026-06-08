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
from usuarios.models import Usuario
import random
import string
class EstudianteViewSet(viewsets.ModelViewSet):
    queryset = Estudiante.objects.all()
    serializer_class = EstudianteSerializer
    permission_classes = [IsAuthenticated, DjangoModelPermissions]
    
    # Configuramos los backends de filtrado
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    # Filtros exactos (Ej: ?fecha_nacimiento=2020-01-01)
    filterset_fields = ['fecha_nacimiento']
    
    # Campos para búsqueda general (Ej: ?search=Juan o ?search=77665544)
    # Usamos '__' para buscar en campos del modelo relacionado (Apoderado)
    search_fields = ['nombres', 'apellidos', 'apoderado__dni', 'apoderado__nombres']
    
    # Campos permitidos para ordenar (Ej: ?ordering=-fecha_nacimiento)
    ordering_fields = ['nombres', 'apellidos', 'fecha_nacimiento']



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

        # =====================================================
        # BUSCAR O CREAR APODERADO
        # =====================================================

        apoderado = Apoderado.objects.filter(
    dni=apoderado_data['dni']
).first()
        
        if not apoderado:

            datos_nuevo = apoderado_data.copy()
            datos_nuevo.pop('id', None)

            apoderado = Apoderado.objects.create(
                **datos_nuevo
            )
        # Si existe, actualizar sus datos
        if apoderado:

            apoderado.nombres = apoderado_data.get(
                'nombres',
                apoderado.nombres
            )

            apoderado.apellidos = apoderado_data.get(
                'apellidos',
                apoderado.apellidos
            )

            apoderado.telefono = apoderado_data.get(
                'telefono',
                apoderado.telefono
            )

            apoderado.email = apoderado_data.get(
                'email',
                apoderado.email
            )

            apoderado.direccion = apoderado_data.get(
                'direccion',
                apoderado.direccion
            )

            apoderado.save()

        else:

            datos_nuevo = apoderado_data.copy()

            # Evitar error si viene id del frontend
            datos_nuevo.pop('id', None)

            apoderado = Apoderado.objects.create(
                **datos_nuevo
            )

        # =====================================================
        # VALIDAR ESTUDIANTE
        # =====================================================

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

        # =====================================================
        # CREAR ESTUDIANTE
        # =====================================================

        estudiante = Estudiante.objects.create(
            **estudiante_data
        )

        # =====================================================
        # CREAR RELACIÓN APODERADO - ESTUDIANTE
        # =====================================================

        relacion_existente = ApoderadoEstudiante.objects.filter(
            apoderado=apoderado,
            estudiante=estudiante
        ).exists()

        if not relacion_existente:

            ApoderadoEstudiante.objects.create(
                apoderado=apoderado,
                estudiante=estudiante,
                tipo_relacion=data['tipo_relacion'],
                es_principal=data.get(
                    'es_principal',
                    True
                )
            )

        generated_credentials = None

        if not apoderado.usuarios.exists():

            temp_password = ''.join(
                random.choices(
                    string.ascii_letters +
                    string.digits,
                    k=8
                )
            )

            usuario = Usuario.objects.create(
                username=apoderado.dni,
                first_name=apoderado.nombres,
                last_name=apoderado.apellidos,
                email=apoderado.email,
                is_parent=True,
                first_login=True,
                apoderado_rel=apoderado,
                is_active=True
            )

            usuario.set_password(temp_password)
            usuario.save()

            generated_credentials = {
                "username": usuario.username,
                "password": temp_password
            }

        # =====================================================
        # RESPUESTA
        # =====================================================

        return Response(
            {
                "message": "Alumno registrado correctamente",
                "estudiante_id": estudiante.id,
                "apoderado_id": apoderado.id,
                "generated_credentials": generated_credentials
            },
            status=status.HTTP_201_CREATED
        )