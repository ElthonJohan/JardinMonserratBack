from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PagoViewSet, ConceptoPagoViewSet, DeudaViewSet, CajaViewSet
)

router = DefaultRouter()
router.register(r'conceptos', ConceptoPagoViewSet, basename='concepto-pago')
router.register(r'deudas', DeudaViewSet, basename='deuda')
router.register(r'pagos', PagoViewSet, basename='pago')
router.register(r'cajas', CajaViewSet, basename='caja')

urlpatterns = [
    path('', include(router.urls)),
]
