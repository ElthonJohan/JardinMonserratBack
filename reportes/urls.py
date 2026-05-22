from django.urls import path
from django.http import HttpResponse
from .views import DashboardStatsAPIView

def index(request):
    return HttpResponse("API Reportes - Servicio disponible")

urlpatterns = [
    path('', index, name='reportes-index'),
    path('dashboard/stats/', DashboardStatsAPIView.as_view(), name='dashboard_stats'),
]
