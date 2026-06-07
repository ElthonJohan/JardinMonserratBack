"""
URL configuration for jardin_monserrat project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenRefreshView
from usuarios.views import CustomTokenObtainPairView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    #usuarios / Authentication
    path('api/auth/', include('usuarios.urls')),
    
    #estudiantes
    path('api/', include('estudiantes.urls')),
    
    path('api/core/', include('core.urls')),
    path('api/matriculas/', include('matriculas.urls')),
    path('api/pagos/', include('pagos.urls')),
    path('api/reportes/', include('reportes.urls')),
    path('api/notificaciones/', include('notificaciones.urls')),
]

# Servir archivos de media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
