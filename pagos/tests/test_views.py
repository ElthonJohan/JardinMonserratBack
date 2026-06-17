import pytest
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal
from datetime import date
from django.contrib.auth import get_user_model
from pagos.models import ConceptoPago, Deuda, Caja
from estudiantes.models import Estudiante, Apoderado

User = get_user_model()

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def superuser(db):
    user = User.objects.create_superuser(
        username="admin_test",
        password="adminpassword",
        email="admin@test.com"
    )
    return user

@pytest.fixture
def auth_client(api_client, superuser):
    api_client.force_authenticate(user=superuser)
    return api_client


@pytest.mark.django_db
class TestConceptoPagoViews:
    def test_get_conceptos(self, auth_client):
        ConceptoPago.objects.create(
            nombre="Concepto Test A",
            tipo="OTROS",
            monto_base=Decimal("100.00")
        )
        url = "/api/pagos/conceptos/"
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        # Check that we receive paginated results or list
        if "results" in response.data:
            assert len(response.data["results"]) >= 1
            assert response.data["results"][0]["nombre"] == "Concepto Test A"
        else:
            assert len(response.data) >= 1
            assert response.data[0]["nombre"] == "Concepto Test A"

    def test_create_concepto(self, auth_client):
        url = "/api/pagos/conceptos/"
        data = {
            "nombre": "Concepto Test Nuevo",
            "tipo": "OTROS",
            "monto_base": "150.00",
            "activo": True
        }
        response = auth_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["nombre"] == "Concepto Test Nuevo"


@pytest.mark.django_db
class TestCajaViews:
    def test_mi_estado_caja_cerrada(self, auth_client):
        url = "/api/pagos/cajas/mi_estado/"
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["abierta"] is False
        assert response.data["caja"] is None

    def test_abrir_y_cerrar_caja(self, auth_client):
        # Abrir caja
        url_abrir = "/api/pagos/cajas/abrir_caja/"
        data = {"monto_inicial": "120.00"}
        response_abrir = auth_client.post(url_abrir, data, format="json")
        assert response_abrir.status_code == status.HTTP_201_CREATED
        assert response_abrir.data["caja"]["estado"] == "Abierta"
        
        caja_id = response_abrir.data["caja"]["id"]

        # Verificar mi_estado
        url_estado = "/api/pagos/cajas/mi_estado/"
        response_estado = auth_client.get(url_estado)
        assert response_estado.status_code == status.HTTP_200_OK
        assert response_estado.data["abierta"] is True
        assert response_estado.data["caja"]["id"] == caja_id

        # Cerrar caja
        url_cerrar = f"/api/pagos/cajas/{caja_id}/cerrar_caja/"
        response_cerrar = auth_client.post(url_cerrar)
        assert response_cerrar.status_code == status.HTTP_200_OK
        assert response_cerrar.data["caja"]["estado"] == "Cerrada"


@pytest.mark.django_db
class TestDeudaViews:
    @pytest.fixture
    def setup_deuda(self):
        apoderado = Apoderado.objects.create(
            nombres="Pedro",
            apellidos="García",
            dni="87654321",
            telefono="999888777"
        )
        estudiante = Estudiante.objects.create(
            nombres="Luis",
            apellidos="García",
            fecha_nacimiento=date(2022, 1, 1),
            dni="12121212"
        )
        concepto = ConceptoPago.objects.create(
            nombre="Pensión Mayo",
            tipo="PENSION",
            monto_base=Decimal("500.00")
        )
        deuda = Deuda.objects.create(
            alumno=estudiante,
            concepto=concepto,
            monto_total=Decimal("500.00"),
            anio=2026,
            mes=5,
            fecha_vencimiento=date(2026, 5, 31)
        )
        return estudiante, deuda

    def test_list_deudas(self, auth_client, setup_deuda):
        estudiante, deuda = setup_deuda
        url = "/api/pagos/deudas/"
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        
        # Verificar paginación y contenido
        results = response.data.get("results", response.data)
        assert len(results) >= 1
        assert results[0]["alumno"] == estudiante.id

    def test_filter_deudas_by_alumno(self, auth_client, setup_deuda):
        estudiante, deuda = setup_deuda
        url = f"/api/pagos/deudas/?alumno={estudiante.id}"
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        
        results = response.data.get("results", response.data)
        assert len(results) == 1
        assert results[0]["alumno"] == estudiante.id
