from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PagoViewSet, ConceptoPagoViewSet, DeudaViewSet, CajaViewSet, BancoViewSet, parent_payment_dashboard
)

router = DefaultRouter()
router.register(r'conceptos', ConceptoPagoViewSet, basename='concepto-pago')
router.register(r'deudas', DeudaViewSet, basename='deuda')
router.register(r'pagos', PagoViewSet, basename='pago')
router.register(r'cajas', CajaViewSet, basename='caja')
router.register(r'bancos', BancoViewSet, basename='banco')

urlpatterns = [
    path('', include(router.urls)),
    path('parent/pagos/', parent_payment_dashboard, name='parent-payment-dashboard'),
]
