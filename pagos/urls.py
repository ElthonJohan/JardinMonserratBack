from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PagoViewSet, 
    # AprobarPagoView,
    # RechazarPagoView,
    ConceptoPagoViewSet,PagosPendientesView, DeudaViewSet, CajaViewSet, BancoViewSet, parent_payment_dashboard, RegistrarPagoParentView
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
    # pagos/urls.py

path(
    'parent/registrar-pago/',
    RegistrarPagoParentView.as_view(),
    name='registrar-pago-parent'
),
path(
    'pendientes/',
    PagosPendientesView.as_view(),
    name='pagos-pendientes'
),
#aprobar pagos
# path(
#     '<int:pago_id>/aprobar/',
#     AprobarPagoView.as_view(),
#     name='aprobar-pago'
# ),
# #rechazar pagos
# path(
#     '<int:pago_id>/rechazar/',
#     RechazarPagoView.as_view(),
#     name='rechazar-pago')
]
