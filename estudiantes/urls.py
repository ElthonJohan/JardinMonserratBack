from rest_framework.routers import DefaultRouter
from django.urls import path
from .views import (EstudianteViewSet,
  ApoderadoViewSet,
  AulaViewSet,
    AgregarApoderadoView,
    EstudianteApoderadosView,
    CambiarApoderadoPrincipalView,
    EliminarRelacionApoderadoView,
  ParentProfileView, RegistroAlumnoView,
  ParentChangePasswordView)

router = DefaultRouter()
router.register(r'estudiantes', EstudianteViewSet)
router.register(r'apoderados', ApoderadoViewSet)
router.register(r'aulas', AulaViewSet)  # NUEVO ENDPOINT PARA AULAS

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
),
    path(
    'estudiantes/<int:estudiante_id>/agregar-apoderado/',
    AgregarApoderadoView.as_view(),
    name='agregar-apoderado'
),
    path(
    'estudiantes/<int:estudiante_id>/apoderados/',
    EstudianteApoderadosView.as_view(),
    name='estudiante-apoderados'
),
    path(
    'apoderado-relacion/<int:relacion_id>/principal/',
    CambiarApoderadoPrincipalView.as_view(),
    name='cambiar-apoderado-principal'
),
    path(
    'apoderado-relacion/<int:relacion_id>/',
    EliminarRelacionApoderadoView.as_view(),
    name='eliminar-relacion-apoderado'
),
    path(
    "parent/change-password/",
    ParentChangePasswordView.as_view(),
),
#     path(
#     "apoderados/<int:pk>/reset-password/",
#     ApoderadoViewSet.as_view({"post": "reset_password"}),
# ),

]