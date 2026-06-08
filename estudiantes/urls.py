from rest_framework.routers import DefaultRouter
from django.urls import path
from .views import (EstudianteViewSet,
  ApoderadoViewSet,
  ParentProfileView, RegistroAlumnoView)

router = DefaultRouter()
router.register(r'estudiantes', EstudianteViewSet)
router.register(r'apoderados', ApoderadoViewSet)

urlpatterns = router.urls + [

    # NUEVO ENDPOINT
    path(
        'parent/profile/',
        ParentProfileView.as_view(),
        name='parent-profile'
    ),
    path(
    'registro-alumno/',
    RegistroAlumnoView.as_view(),
    name='registro-alumno'
)
]