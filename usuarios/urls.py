from rest_framework.routers import DefaultRouter
from .views import UsuarioViewSet, RegisterView, RoleViewSet, PermisoViewSet, login_parent, change_password_first_login, CustomTokenObtainPairView
from rest_framework_simplejwt.views import TokenRefreshView
from django.urls import path, include

router = DefaultRouter()
router.register(r'usuarios', UsuarioViewSet, basename='usuarios')
router.register(r'roles', RoleViewSet, basename='roles')
router.register(r'permisos', PermisoViewSet, basename='permisos')

urlpatterns = [
    path('login/', CustomTokenObtainPairView.as_view(), name='login_admin'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', RegisterView.as_view(), name='register'),
    path('', include(router.urls)),
    path('login-parent/', login_parent, name='login-parent'),
    path('change-password-first/', change_password_first_login, name='change-password-first'),
]