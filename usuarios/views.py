from rest_framework import viewsets, generics
from rest_framework.permissions import IsAuthenticated, DjangoModelPermissions
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