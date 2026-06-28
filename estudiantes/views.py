from rest_framework import viewsets, filters
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from .serializers import ApoderadoProfileSerializer, RegistroAlumnoSerializer, AgregarApoderadoSerializer, ApoderadoEstudianteDetalleSerializer
from .models import ApoderadoEstudiante, Estudiante, Aula, Apoderado
from .serializers import EstudianteSerializer, ChangePasswordSerializer, AulaSerializer, ApoderadoSerializer,ApoderadoProfileUpdateSerializer
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticated, DjangoModelPermissions
from usuarios.models import Usuario
import random
import string
from django.utils.crypto import get_random_string

class AulaViewSet(viewsets.ModelViewSet):
    queryset = Aula.objects.all().order_by('id')
    serializer_class = AulaSerializer
    permission_classes = [IsAuthenticated, DjangoModelPermissions]

class EstudianteViewSet(viewsets.ModelViewSet):
    queryset = Estudiante.objects.all().order_by('id')
    serializer_class = EstudianteSerializer
    permission_classes = [IsAuthenticated, DjangoModelPermissions]
    
    # Configuramos los backends de filtrado
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]

    def get_queryset(self):
        return Estudiante.objects.all().prefetch_related('apoderados__apoderado')
    
    # Filtros exactos (Ej: ?fecha_nacimiento=2020-01-01)
    filterset_fields = ['fecha_nacimiento']
    
    # Campos para búsqueda general (Ej: ?search=Juan o ?search=77665544)
    # Usamos '__' para buscar en campos del modelo relacionado (Apoderado) a través de la tabla intermedia
    search_fields = ['nombres', 'apellidos', 'apoderados__apoderado__dni', 'apoderados__apoderado__nombres']
    
    # Campos permitidos para ordenar (Ej: ?ordering=-fecha_nacimiento)
    ordering_fields = ['nombres', 'apellidos', 'fecha_nacimiento']
    ordering = '-id'



class ApoderadoViewSet(viewsets.ModelViewSet):
    queryset = Apoderado.objects.all().order_by('id')
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



    @action(detail=True, methods=["post"])
    def reset_password(self, request, pk=None):
        """
        Restablece la contraseña del usuario asociado al apoderado.
        """

        apoderado = self.get_object()

        usuario = apoderado.usuarios.first()

        if not usuario:
            return Response(
                {
                    "detail": "El apoderado no tiene un usuario asociado."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        password_temporal = get_random_string(
            length=8,
            allowed_chars="ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
        )

        usuario.set_password(password_temporal)
        usuario.first_login = True
        usuario.save()

        return Response(
            {
                "message": "Contraseña restablecida correctamente.",
                "apoderado": f"{apoderado.nombres} {apoderado.apellidos}",
                "username": usuario.username,
                "password": password_temporal
            },
            status=status.HTTP_200_OK
        )


class ParentProfileView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        user = request.user

        if not user.is_parent:
            return Response(
                {
                    "detail":
                    "No autorizado"
                },
                status=403
            )

        apoderado = getattr(
            user,
            'apoderado_rel',
            None
        )

        if not apoderado:

            return Response(
                {
                    "detail":
                    "No existe un perfil de apoderado asociado."
                },
                status=404
            )

        serializer = (
            ApoderadoProfileSerializer(
                apoderado
            )
        )

        return Response(
            serializer.data
        )
    
    def put(self, request):

        user = request.user

        if not user.is_parent:

            return Response(
                {
                    "detail":
                    "No autorizado"
                },
                status=403
            )

        apoderado = getattr(
            user,
            "apoderado_rel",
            None
        )

        if not apoderado:

            return Response(
                {
                    "detail":
                    "No existe un perfil de apoderado asociado."
                },
                status=404
            )

        serializer = (
            ApoderadoProfileUpdateSerializer(
                apoderado,
                data=request.data,
                partial=True
            )
        )

        if serializer.is_valid():

            serializer.save()

            return Response(
                {
                    "message":
                    "Perfil actualizado correctamente",
                    "data":
                    serializer.data
                }
            )

        return Response(
            serializer.errors,
            status=400
        )


class ParentChangePasswordView(
    APIView
):

    permission_classes = [
        IsAuthenticated
    ]

    def post(
        self,
        request
    ):

        serializer = (
            ChangePasswordSerializer(
                data=request.data
            )
        )

        serializer.is_valid(
            raise_exception=True
        )

        user = request.user

        current_password = (
            serializer.validated_data[
                "current_password"
            ]
        )

        if not user.check_password(
            current_password
        ):

            return Response(
                {
                    "detail":
                    "La contraseña actual es incorrecta."
                },
                status=400
            )

        user.set_password(
            serializer.validated_data[
                "new_password"
            ]
        )

        user.save()

        return Response(
            {
                "message":
                "Contraseña actualizada correctamente"
            }
        )

class EstudianteApoderadosView(APIView):

    def get(
        self,
        request,
        estudiante_id
    ):

        try:

            estudiante = Estudiante.objects.get(
                pk=estudiante_id
            )

        except Estudiante.DoesNotExist:

            return Response(
                {
                    "error":
                    "Estudiante no encontrado"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        relaciones = (
            ApoderadoEstudiante.objects
            .filter(
                estudiante=estudiante
            )
            .select_related(
                'apoderado'
            )
            .order_by(
                '-es_principal'
            )
        )

        serializer = (
            ApoderadoEstudianteDetalleSerializer(
                relaciones,
                many=True
            )
        )

        return Response(
            serializer.data
        )


class RegistroAlumnoView(APIView):

    @transaction.atomic
    def get(self):

        serializer = RegistroAlumnoSerializer()

        return Response(serializer.data)
    
    
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
   
   

class CambiarApoderadoPrincipalView(APIView):

    @transaction.atomic
    def patch(
        self,
        request,
        relacion_id
    ):

        try:

            relacion = (
                ApoderadoEstudiante.objects
                .select_related('estudiante')
                .get(pk=relacion_id)
            )

        except ApoderadoEstudiante.DoesNotExist:

            return Response(
                {
                    "error":
                    "Relación no encontrada"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        estudiante = relacion.estudiante

        # Quitar principal a todos

        ApoderadoEstudiante.objects.filter(
            estudiante=estudiante
        ).update(
            es_principal=False
        )

        # Asignar nuevo principal

        relacion.es_principal = True
        relacion.save()

        return Response(
            {
                "message":
                "Apoderado principal actualizado correctamente",

                "apoderado": (
                    f"{relacion.apoderado.nombres} "
                    f"{relacion.apoderado.apellidos}"
                ),

                "estudiante": (
                    f"{estudiante.nombres} "
                    f"{estudiante.apellidos}"
                )
            },
            status=status.HTTP_200_OK
        )     

class AgregarApoderadoView(APIView):

    @transaction.atomic
    def post(self, request, estudiante_id):

        serializer = AgregarApoderadoSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        data = serializer.validated_data

        try:

            estudiante = Estudiante.objects.get(
                pk=estudiante_id
            )

        except Estudiante.DoesNotExist:

            return Response(
                {
                    "error": "Estudiante no encontrado"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        # Buscar apoderado existente por DNI

        apoderado = Apoderado.objects.filter(
            dni=data['dni']
        ).first()

        # Crear si no existe

        if not apoderado:

            apoderado = Apoderado.objects.create(
                dni=data['dni'],
                nombres=data.get('nombres', ''),
                apellidos=data.get('apellidos', ''),
                telefono=data.get('telefono', ''),
                email=data.get(
                    'email',
                    'sin_email@gmail.com'
                ),
                direccion=data.get(
                    'direccion',
                    ''
                )
            )

        # Verificar si ya está asociado

        relacion_existente = (
            ApoderadoEstudiante.objects.filter(
                apoderado=apoderado,
                estudiante=estudiante
            ).exists()
        )

        if relacion_existente:

            return Response(
                {
                    "error":
                    "El apoderado ya está asociado a este estudiante"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Si será principal, quitar principal anterior

        if data['es_principal']:

            ApoderadoEstudiante.objects.filter(
                estudiante=estudiante
            ).update(
                es_principal=False
            )

        relacion = (
            ApoderadoEstudiante.objects.create(
                apoderado=apoderado,
                estudiante=estudiante,
                tipo_relacion=data['tipo_relacion'],
                es_principal=data['es_principal']
            )
        )

        return Response(
            {
                "message":
                "Apoderado agregado correctamente",

                "apoderado": {
                    "id": apoderado.id,
                    "nombre":
                    f"{apoderado.nombres} "
                    f"{apoderado.apellidos}"
                },

                "relacion": {
                    "id": relacion.id,
                    "tipo_relacion":
                    relacion.tipo_relacion,
                    "es_principal":
                    relacion.es_principal
                }
            },
            status=status.HTTP_201_CREATED
        )
        
        
class EliminarRelacionApoderadoView(APIView):

    @transaction.atomic
    def delete(
        self,
        request,
        relacion_id
    ):

        try:

            relacion = (
                ApoderadoEstudiante.objects
                .select_related(
                    'estudiante',
                    'apoderado'
                )
                .get(pk=relacion_id)
            )

        except ApoderadoEstudiante.DoesNotExist:

            return Response(
                {
                    "error":
                    "Relación no encontrada"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        estudiante = relacion.estudiante

        total_apoderados = (
            ApoderadoEstudiante.objects
            .filter(
                estudiante=estudiante
            )
            .count()
        )

        if total_apoderados <= 1:

            return Response(
                {
                    "error":
                    "El estudiante debe tener al menos un apoderado."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        nombre_apoderado = (
            f"{relacion.apoderado.nombres} "
            f"{relacion.apoderado.apellidos}"
        )

        era_principal = relacion.es_principal

        relacion.delete()

        # Si eliminamos al principal,
        # asignamos otro automáticamente

        if era_principal:

            nuevo_principal = (
                ApoderadoEstudiante.objects
                .filter(
                    estudiante=estudiante
                )
                .first()
            )

            if nuevo_principal:

                nuevo_principal.es_principal = True
                nuevo_principal.save()

        return Response(
            {
                "message":
                "Relación eliminada correctamente",

                "apoderado":
                nombre_apoderado
            },
            status=status.HTTP_200_OK
        )