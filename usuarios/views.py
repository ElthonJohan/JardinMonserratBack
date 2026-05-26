from rest_framework import viewsets, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, DjangoModelPermissions, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from estudiantes.models import Estudiante
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from rest_framework.response import Response
from .models import Usuario
from .serializers import (
    UsuarioSerializer, RegisterSerializer, CustomTokenObtainPairSerializer,
    GroupSerializer
)

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class PermisoViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        excluded_apps = ['admin', 'auth', 'contenttypes', 'sessions']
        content_types = ContentType.objects.exclude(app_label__in=excluded_apps)
        
        result = []
        for ct in content_types:
            perms = Permission.objects.filter(content_type=ct)
            if not perms.exists():
                continue
                
            modulo_name = ct.model.capitalize()
            
            permisos_dict = {}
            for p in perms:
                action = p.codename.split('_')[0]
                permisos_dict[action] = {
                    "id": p.id,
                    "codename": p.codename
                }
                
            result.append({
                "modulo": modulo_name,
                "permisos": permisos_dict
            })
            
        return Response(result)

class RoleViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [IsAuthenticated, DjangoModelPermissions]

class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [IsAuthenticated, DjangoModelPermissions]

class RegisterView(generics.CreateAPIView):
    queryset = Usuario.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [IsAuthenticated, DjangoModelPermissions]
    
@api_view(['POST'])
@permission_classes([AllowAny])
def login_parent(request):
    codigo_estudiante = request.data.get('codigo_estudiante')
    password = request.data.get('password')

    if not codigo_estudiante or not password:
        return Response({"detail": "Código y contraseña son requeridos."}, status=400)

    try:
        estudiante = Estudiante.objects.get(codigo_estudiante=codigo_estudiante)
        apoderado = estudiante.apoderado
        usuario = apoderado.usuarios.first()
        
        if not usuario:
            return Response({"detail": "Usuario no encontrado."}, status=404)

        user = authenticate(username=usuario.username, password=password)
        
        if user is None:
            return Response({"detail": "Contraseña incorrecta."}, status=401)

        if not user.is_active:
            return Response({"detail": "Cuenta desactivada."}, status=403)

        refresh = RefreshToken.for_user(user)

        response_data = {
            "success": True,
            "token": str(refresh.access_token),
            "refresh": str(refresh),
            "user": {
                "id": user.id,
                "username": user.username,
                "full_name": f"{apoderado.nombres} {apoderado.apellidos}",
                "apoderado_id": apoderado.id,
                "user_type": "parent",
                "first_login": user.first_login
            },
            "estudiante": {
                "id": estudiante.id,
                "nombre": str(estudiante),
                "codigo": estudiante.codigo_estudiante
            }
        }

        # Si es primer login, avisar que debe cambiar contraseña
        if user.first_login:
            response_data["requires_password_change"] = True
            response_data["message"] = "Debes cambiar tu contraseña en el primer ingreso."

        return Response(response_data)

    except Estudiante.DoesNotExist:
        return Response({"detail": "Código de estudiante no encontrado."}, status=404)
    

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password_first_login(request):
    """
    Cambiar contraseña en el primer inicio de sesión (para apoderados)
    """
    user = request.user
    old_password = request.data.get('old_password')
    new_password = request.data.get('new_password')
    confirm_password = request.data.get('confirm_password')

    if not old_password or not new_password or not confirm_password:
        return Response({"detail": "Todos los campos son requeridos."}, status=400)

    # Verificar que la contraseña actual sea correcta
    if not user.check_password(old_password):
        return Response({"detail": "La contraseña actual es incorrecta."}, status=400)

    # Verificar que las nuevas contraseñas coincidan
    if new_password != confirm_password:
        return Response({"detail": "Las nuevas contraseñas no coinciden."}, status=400)

    # Validar longitud mínima
    if len(new_password) < 6:
        return Response({"detail": "La nueva contraseña debe tener al menos 6 caracteres."}, status=400)

    # Cambiar la contraseña
    user.set_password(new_password)
    user.first_login = False  # Marcar como ya cambiado
    user.save()

    return Response({
        "success": True,
        "message": "Contraseña cambiada exitosamente. Ahora puedes iniciar sesión con tu nueva contraseña."
    })