from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PeriodoEvaluacionViewSet, AreaViewSet, CompetenciaViewSet,
    CalificacionViewSet, ApreciacionViewSet, LibretaVirtualView,
    AsignacionDocenteViewSet
)

router = DefaultRouter()
router.register(r'periodos', PeriodoEvaluacionViewSet)
router.register(r'areas', AreaViewSet)
router.register(r'competencias', CompetenciaViewSet)
router.register(r'calificaciones', CalificacionViewSet)
router.register(r'apreciaciones', ApreciacionViewSet)
router.register(r'asignaciones', AsignacionDocenteViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('libreta-virtual/', LibretaVirtualView.as_view(), name='libreta_virtual'),
]
