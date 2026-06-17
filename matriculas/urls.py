from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MatriculaViewSet, PeriodoAcademicoViewSet

router = DefaultRouter()
router.register(r'matriculas', MatriculaViewSet, basename='matricula')
router.register(r'periodos-academicos', PeriodoAcademicoViewSet, basename='periodo-academico')

urlpatterns = [
    path('', include(router.urls)),
]
