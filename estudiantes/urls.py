from rest_framework.routers import DefaultRouter
from django.urls import path
from .views import (EstudianteViewSet,
 AulaViewSet,
  ApoderadoViewSet,
  ParentProfileView)

router = DefaultRouter()
router.register(r'estudiantes', EstudianteViewSet)
router.register(r'aulas', AulaViewSet)
router.register(r'apoderados', ApoderadoViewSet)

urlpatterns = router.urls + [

    # NUEVO ENDPOINT
    path(
        'parent/profile/',
        ParentProfileView.as_view(),
        name='parent-profile'
    ),
]