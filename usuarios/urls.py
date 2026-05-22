from rest_framework.routers import DefaultRouter
from .views import UsuarioViewSet, RegisterView, RoleViewSet, PermisoViewSet
from django.urls import path, include

router = DefaultRouter()
router.register(r'usuarios', UsuarioViewSet, basename='usuarios')
router.register(r'roles', RoleViewSet, basename='roles')
router.register(r'permisos', PermisoViewSet, basename='permisos')

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('', include(router.urls)),
]