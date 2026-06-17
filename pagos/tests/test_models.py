# pagos/tests/test_models.py
import pytest
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date

from pagos.models import ConceptoPago, Deuda, Caja, Banco, Pago, PagoAsignacion
from estudiantes.models import Estudiante, Apoderado
from usuarios.models import Usuario


@pytest.mark.django_db
class TestConceptoPagoModel:
    def test_concepto_pago_creation(self):
        concepto = ConceptoPago.objects.create(
            nombre="Pensión Mensual Test",
            tipo="PENSION",
            monto_base=Decimal("450.00")
        )
        assert concepto.nombre == "Pensión Mensual Test"
        assert concepto.tipo == "PENSION"
        assert concepto.monto_base == Decimal("450.00")
        assert concepto.activo is True
        assert str(concepto) == "Pensión Mensual Test - S/ 450.00"

    def test_concepto_pago_nombre_unico(self):
        """Prueba que no se puedan crear conceptos con el mismo nombre"""
        ConceptoPago.objects.create(
            nombre="Matrícula 2024",
            tipo="MATRICULA",
            monto_base=Decimal("300.00")
        )
        with pytest.raises(Exception):  # IntegrityError
            ConceptoPago.objects.create(
                nombre="Matrícula 2024",
                tipo="MATRICULA",
                monto_base=Decimal("300.00")
            )


@pytest.mark.django_db
class TestDeudaModel:
    @pytest.fixture
    def setup_data(self):
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
            nombre="Matrícula Test",
            tipo="MATRICULA",
            monto_base=Decimal("300.00")
        )
        return estudiante, concepto

    def test_deuda_creation(self, setup_data):
        """Prueba creación básica de deuda"""
        estudiante, concepto = setup_data
        deuda = Deuda.objects.create(
            alumno=estudiante,
            concepto=concepto,
            monto_total=Decimal("300.00"),
            mes=3,
            anio=2026,
            fecha_vencimiento=date(2026, 3, 1)
        )
        assert deuda.monto_total == Decimal("300.00")
        assert deuda.monto_pagado == Decimal("0.00")
        assert deuda.estado == "Pendiente"
        assert deuda.saldo_pendiente == Decimal("300.00")

    def test_deuda_saldo_pendiente(self, setup_data):
        estudiante, concepto = setup_data
        deuda = Deuda.objects.create(
            alumno=estudiante,
            concepto=concepto,
            monto_total=Decimal("300.00"),
            monto_pagado=Decimal("100.00"),
            anio=2026,
            fecha_vencimiento=date(2026, 3, 1)
        )
        assert deuda.saldo_pendiente == Decimal("200.00")
        assert str(deuda) == f"{estudiante} - Matrícula Test - None/2026"

    def test_deuda_clean_unique_validation(self, setup_data):
        estudiante, concepto = setup_data

        # Crear la primera deuda
        Deuda.objects.create(
            alumno=estudiante,
            concepto=concepto,
            monto_total=Decimal("300.00"),
            mes=3,
            anio=2026,
            fecha_vencimiento=date(2026, 3, 1)
        )

        # Crear una segunda deuda con los mismos campos únicos y validar clean()
        segunda_deuda = Deuda(
            alumno=estudiante,
            concepto=concepto,
            monto_total=Decimal("300.00"),
            mes=3,
            anio=2026,
            fecha_vencimiento=date(2026, 3, 1)
        )

        with pytest.raises(ValidationError) as excinfo:
            segunda_deuda.clean()
        assert "Ya existe una deuda registrada para este alumno" in str(excinfo.value)

    def test_deuda_clean_permite_actualizacion(self, setup_data):
        """Prueba que una deuda pueda actualizarse sin generar duplicado"""
        estudiante, concepto = setup_data
        deuda = Deuda.objects.create(
            alumno=estudiante,
            concepto=concepto,
            monto_total=Decimal("300.00"),
            mes=3,
            anio=2026,
            fecha_vencimiento=date(2026, 3, 1)
        )

        # Actualizar la misma deuda (no debería lanzar error)
        deuda.monto_total = Decimal("350.00")
        deuda.full_clean()  # No debería lanzar ValidationError
        deuda.save()

        deuda.refresh_from_db()
        assert deuda.monto_total == Decimal("350.00")

    def test_actualizar_estado_pendiente(self, setup_data):
        """Prueba que el estado sea 'Pendiente' cuando no hay pagos"""
        estudiante, concepto = setup_data
        deuda = Deuda.objects.create(
            alumno=estudiante,
            concepto=concepto,
            monto_total=Decimal("500.00"),
            mes=6,
            anio=2026,
            fecha_vencimiento=date(2026, 6, 30)
        )
        deuda.actualizar_estado()
        deuda.refresh_from_db()
        assert deuda.estado == "Pendiente"
        assert deuda.monto_pagado == Decimal("0.00")

    def test_actualizar_estado_parcial_manual(self, setup_data):
        """Prueba que el estado sea 'Parcial' cuando se asigna manualmente monto_pagado"""
        estudiante, concepto = setup_data
        deuda = Deuda.objects.create(
            alumno=estudiante,
            concepto=concepto,
            monto_total=Decimal("500.00"),
            mes=6,
            anio=2026,
            fecha_vencimiento=date(2026, 6, 30)
        )
        # Asignación manual
        deuda.monto_pagado = Decimal("200.00")
        deuda.actualizar_estado()
        deuda.refresh_from_db()
        assert deuda.estado == "Parcial"
        assert deuda.monto_pagado == Decimal("200.00")
        assert deuda.saldo_pendiente == Decimal("300.00")

    def test_actualizar_estado_pagado_manual(self, setup_data):
        """Prueba que el estado sea 'Pagado' cuando se asigna manualmente el total"""
        estudiante, concepto = setup_data
        deuda = Deuda.objects.create(
            alumno=estudiante,
            concepto=concepto,
            monto_total=Decimal("500.00"),
            mes=6,
            anio=2026,
            fecha_vencimiento=date(2026, 6, 30)
        )
        # Asignación manual completa
        deuda.monto_pagado = Decimal("500.00")
        deuda.actualizar_estado()
        deuda.refresh_from_db()
        assert deuda.estado == "Pagado"
        assert deuda.monto_pagado == Decimal("500.00")
        assert deuda.saldo_pendiente == Decimal("0.00")

    def test_actualizar_estado_con_actualizacion_manual_progresiva(self, setup_data):
        """Prueba que el estado se actualice correctamente con asignaciones manuales progresivas"""
        estudiante, concepto = setup_data
        deuda = Deuda.objects.create(
            alumno=estudiante,
            concepto=concepto,
            monto_total=Decimal("500.00"),
            mes=6,
            anio=2026,
            fecha_vencimiento=date(2026, 6, 30)
        )

        # Primer pago parcial
        deuda.monto_pagado = Decimal("200.00")
        deuda.actualizar_estado()
        deuda.refresh_from_db()
        assert deuda.estado == "Parcial"
        assert deuda.saldo_pendiente == Decimal("300.00")

        # Segundo pago parcial
        deuda.monto_pagado = Decimal("400.00")
        deuda.actualizar_estado()
        deuda.refresh_from_db()
        assert deuda.estado == "Parcial"
        assert deuda.saldo_pendiente == Decimal("100.00")

        # Pago completo
        deuda.monto_pagado = Decimal("500.00")
        deuda.actualizar_estado()
        deuda.refresh_from_db()
        assert deuda.estado == "Pagado"
        assert deuda.saldo_pendiente == Decimal("0.00")

    def test_actualizar_estado_con_asignacion_automatica(self, setup_data):
        """Prueba que el estado se actualice correctamente con asignaciones automáticas"""
        estudiante, concepto = setup_data

        # Crear deuda
        deuda = Deuda.objects.create(
            alumno=estudiante,
            concepto=concepto,
            monto_total=Decimal("500.00"),
            mes=6,
            anio=2026,
            fecha_vencimiento=date(2026, 6, 30)
        )

        # Crear usuario y caja para el pago
        usuario = Usuario.objects.create_user(
            username="cajero_test",
            password="pass123",
            is_staff=True
        )
        caja = Caja.objects.create(
            usuario=usuario,
            monto_inicial=Decimal("1000.00")
        )

        # Crear pago aprobado
        pago = Pago.objects.create(
            alumno=estudiante,
            caja=caja,
            monto_total_entregado=Decimal("200.00"),
            metodo_pago="Efectivo",
            estado="APROBADO",
            usuario_creador=usuario
        )

        # Crear asignación con recalcular_desde_asignaciones=True
        PagoAsignacion.objects.create(
            pago=pago,
            deuda=deuda,
            monto_aplicado=Decimal("200.00")
        )

        # Llamar al método con recalcular_desde_asignaciones=True
        deuda.actualizar_estado(recalcular_desde_asignaciones=True)
        deuda.refresh_from_db()
        assert deuda.estado == "Parcial"
        assert deuda.monto_pagado == Decimal("200.00")
        assert deuda.saldo_pendiente == Decimal("300.00")

    def test_actualizar_estado_con_multiples_asignaciones_automaticas(self, setup_data):
        """Prueba múltiples asignaciones automáticas a la misma deuda"""
        estudiante, concepto = setup_data

        # Crear deuda
        deuda = Deuda.objects.create(
            alumno=estudiante,
            concepto=concepto,
            monto_total=Decimal("500.00"),
            mes=6,
            anio=2026,
            fecha_vencimiento=date(2026, 6, 30)
        )

        # Crear usuario y caja
        usuario = Usuario.objects.create_user(
            username="cajero_test3",
            password="pass789",
            is_staff=True
        )
        caja = Caja.objects.create(
            usuario=usuario,
            monto_inicial=Decimal("1000.00")
        )

        # Primer pago
        pago1 = Pago.objects.create(
            alumno=estudiante,
            caja=caja,
            monto_total_entregado=Decimal("200.00"),
            metodo_pago="Efectivo",
            estado="APROBADO",
            usuario_creador=usuario
        )
        PagoAsignacion.objects.create(
            pago=pago1,
            deuda=deuda,
            monto_aplicado=Decimal("200.00")
        )

        # Actualizar con asignaciones automáticas
        deuda.actualizar_estado(recalcular_desde_asignaciones=True)
        deuda.refresh_from_db()
        assert deuda.estado == "Parcial"
        assert deuda.monto_pagado == Decimal("200.00")

        # Segundo pago
        pago2 = Pago.objects.create(
            alumno=estudiante,
            caja=caja,
            monto_total_entregado=Decimal("300.00"),
            metodo_pago="Efectivo",
            estado="APROBADO",
            usuario_creador=usuario
        )
        PagoAsignacion.objects.create(
            pago=pago2,
            deuda=deuda,
            monto_aplicado=Decimal("300.00")
        )

        # Actualizar con asignaciones automáticas
        deuda.actualizar_estado(recalcular_desde_asignaciones=True)
        deuda.refresh_from_db()
        assert deuda.estado == "Pagado"
        assert deuda.monto_pagado == Decimal("500.00")
        assert deuda.saldo_pendiente == Decimal("0.00")

    def test_actualizar_estado_solo_cuenta_pagos_aprobados(self, setup_data):
        """Prueba que solo los pagos APROBADOS cuenten para actualizar el estado"""
        estudiante, concepto = setup_data

        # Crear deuda
        deuda = Deuda.objects.create(
            alumno=estudiante,
            concepto=concepto,
            monto_total=Decimal("500.00"),
            mes=6,
            anio=2026,
            fecha_vencimiento=date(2026, 6, 30)
        )

        # Crear usuario y caja
        usuario = Usuario.objects.create_user(
            username="cajero_test4",
            password="pass101",
            is_staff=True
        )
        caja = Caja.objects.create(
            usuario=usuario,
            monto_inicial=Decimal("1000.00")
        )

        # Crear pago REGISTRADO (no debe contar)
        pago_registrado = Pago.objects.create(
            alumno=estudiante,
            caja=caja,
            monto_total_entregado=Decimal("500.00"),
            metodo_pago="Efectivo",
            estado="REGISTRADO",
            usuario_creador=usuario
        )
        PagoAsignacion.objects.create(
            pago=pago_registrado,
            deuda=deuda,
            monto_aplicado=Decimal("500.00")
        )

        # Verificar que el estado siga Pendiente
        deuda.actualizar_estado(recalcular_desde_asignaciones=True)
        deuda.refresh_from_db()
        assert deuda.estado == "Pendiente"
        assert deuda.monto_pagado == Decimal("0.00")

        # Ahora aprobar el pago
        pago_registrado.estado = "APROBADO"
        pago_registrado.save()
        pago_registrado.fecha_aprobacion = timezone.now()
        pago_registrado.save()

        # Actualizar nuevamente
        deuda.actualizar_estado(recalcular_desde_asignaciones=True)
        deuda.refresh_from_db()
        assert deuda.estado == "Pagado"
        assert deuda.monto_pagado == Decimal("500.00")

    def test_anulacion_manual_de_deuda(self, setup_data):
        """Prueba que se pueda anular manualmente una deuda"""
        estudiante, concepto = setup_data
        deuda = Deuda.objects.create(
            alumno=estudiante,
            concepto=concepto,
            monto_total=Decimal("500.00"),
            mes=6,
            anio=2026,
            fecha_vencimiento=date(2026, 6, 30)
        )

        # Anular manualmente
        deuda.estado = "Anulado"
        deuda.save()
        deuda.refresh_from_db()
        assert deuda.estado == "Anulado"

    def test_actualizar_estado_no_sobrescribe_anulacion(self, setup_data):
        """Prueba que actualizar_estado no cambie una deuda anulada"""
        estudiante, concepto = setup_data
        deuda = Deuda.objects.create(
            alumno=estudiante,
            concepto=concepto,
            monto_total=Decimal("500.00"),
            monto_pagado=Decimal("200.00"),
            estado="Anulado",
            mes=6,
            anio=2026,
            fecha_vencimiento=date(2026, 6, 30)
        )

        # Intentar actualizar estado (no debería cambiar)
        deuda.actualizar_estado()
        deuda.refresh_from_db()
        assert deuda.estado == "Anulado"
        assert deuda.monto_pagado == Decimal("200.00")

    def test_actualizar_estado_con_ambos_metodos(self, setup_data):
        """Prueba la combinación de asignación manual y automática"""
        estudiante, concepto = setup_data

        # Crear deuda
        deuda = Deuda.objects.create(
            alumno=estudiante,
            concepto=concepto,
            monto_total=Decimal("500.00"),
            mes=6,
            anio=2026,
            fecha_vencimiento=date(2026, 6, 30)
        )

        # Primero, asignación manual
        deuda.monto_pagado = Decimal("100.00")
        deuda.actualizar_estado()
        deuda.refresh_from_db()
        assert deuda.estado == "Parcial"
        assert deuda.monto_pagado == Decimal("100.00")

        # Crear usuario y caja para asignación automática
        usuario = Usuario.objects.create_user(
            username="cajero_test5",
            password="pass202",
            is_staff=True
        )
        caja = Caja.objects.create(
            usuario=usuario,
            monto_inicial=Decimal("1000.00")
        )

        # Luego, asignación automática
        pago = Pago.objects.create(
            alumno=estudiante,
            caja=caja,
            monto_total_entregado=Decimal("300.00"),
            metodo_pago="Efectivo",
            estado="APROBADO",
            usuario_creador=usuario
        )
        PagoAsignacion.objects.create(
            pago=pago,
            deuda=deuda,
            monto_aplicado=Decimal("300.00")
        )

        # Actualizar con asignaciones automáticas (debería recalcular)
        deuda.actualizar_estado(recalcular_desde_asignaciones=True)
        deuda.refresh_from_db()
        # El total pagado debería ser 300 (de la asignación), no 100 (manual)
        assert deuda.monto_pagado == Decimal("300.00")
        assert deuda.estado == "Parcial"
        assert deuda.saldo_pendiente == Decimal("200.00")


@pytest.mark.django_db
class TestCajaModel:
    def test_caja_creation(self):
        usuario = Usuario.objects.create_user(
            username="cajero",
            password="password123",
            is_staff=True
        )
        caja = Caja.objects.create(
            usuario=usuario,
            monto_inicial=Decimal("50.00")
        )
        assert caja.estado == "Abierta"
        assert caja.monto_inicial == Decimal("50.00")
        assert str(caja).startswith(f"Caja {caja.id}")

    def test_caja_cierre(self):
        usuario = Usuario.objects.create_user(
            username="cajero2",
            password="password456",
            is_staff=True
        )
        caja = Caja.objects.create(
            usuario=usuario,
            monto_inicial=Decimal("100.00")
        )
        assert caja.estado == "Abierta"
        assert caja.fecha_cierre is None

        # Cerrar caja
        caja.estado = "Cerrada"
        caja.fecha_cierre = timezone.now()
        caja.save()
        caja.refresh_from_db()
        assert caja.estado == "Cerrada"
        assert caja.fecha_cierre is not None


@pytest.mark.django_db
class TestPagoModel:
    @pytest.fixture
    def setup_data(self):
        usuario = Usuario.objects.create_user(
            username="admin_pago",
            password="password123",
            is_superuser=True
        )
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
        caja = Caja.objects.create(
            usuario=usuario,
            monto_inicial=Decimal("0.00")
        )
        banco = Banco.objects.create(nombre="BCP")
        return usuario, estudiante, caja, banco

    def test_pago_efectivo_valido(self, setup_data):
        usuario, estudiante, caja, _ = setup_data
        pago = Pago(
            alumno=estudiante,
            caja=caja,
            monto_total_entregado=Decimal("100.00"),
            metodo_pago="Efectivo",
            usuario_creador=usuario
        )
        # Efectivo no requiere banco ni número de operación
        pago.clean()
        pago.save()
        assert pago.pk is not None
        assert pago.banco is None
        assert pago.numero_operacion is None

    def test_pago_yape_requiere_numero_operacion(self, setup_data):
        usuario, estudiante, caja, _ = setup_data
        pago = Pago(
            alumno=estudiante,
            caja=caja,
            monto_total_entregado=Decimal("100.00"),
            metodo_pago="Yape",
            usuario_creador=usuario
        )
        with pytest.raises(ValidationError) as excinfo:
            pago.clean()
        assert "El número de operación es obligatorio para pagos digitales." in str(excinfo.value)

    def test_pago_transferencia_requiere_banco(self, setup_data):
        usuario, estudiante, caja, _ = setup_data
        pago = Pago(
            alumno=estudiante,
            caja=caja,
            monto_total_entregado=Decimal("100.00"),
            metodo_pago="Transferencia",
            numero_operacion="123456",
            usuario_creador=usuario
        )
        with pytest.raises(ValidationError) as excinfo:
            pago.clean()
        assert "El banco es obligatorio para transferencias o depósitos." in str(excinfo.value)

    def test_pago_transferencia_requiere_numero_operacion(self, setup_data):
        usuario, estudiante, caja, banco = setup_data
        pago = Pago(
            alumno=estudiante,
            caja=caja,
            monto_total_entregado=Decimal("100.00"),
            metodo_pago="Transferencia",
            banco=banco,
            usuario_creador=usuario
        )
        with pytest.raises(ValidationError) as excinfo:
            pago.clean()
        assert "El número de operación es obligatorio." in str(excinfo.value)

    def test_pago_aprobado_requiere_caja(self, setup_data):
        """Prueba que un pago aprobado requiera caja asignada"""
        usuario, estudiante, _, _ = setup_data
        pago = Pago(
            alumno=estudiante,
            monto_total_entregado=Decimal("100.00"),
            metodo_pago="Efectivo",
            estado="APROBADO",  # APROBADO sin caja
            usuario_creador=usuario
        )
        with pytest.raises(ValidationError) as excinfo:
            pago.clean()
        assert "Debe asignarse a una caja receptora" in str(excinfo.value)

    def test_pago_rechazado_requiere_motivo(self, setup_data):
        """Prueba que un pago rechazado requiera motivo"""
        usuario, estudiante, caja, _ = setup_data
        pago = Pago(
            alumno=estudiante,
            caja=caja,
            monto_total_entregado=Decimal("100.00"),
            metodo_pago="Efectivo",
            estado="RECHAZADO",  # RECHAZADO sin motivo
            usuario_creador=usuario
        )
        with pytest.raises(ValidationError) as excinfo:
            pago.clean()
        assert "Debe especificarse un motivo de rechazo" in str(excinfo.value)

    def test_pago_con_banco_y_numero_unico(self, setup_data):
        """Prueba que la combinación banco + número_operacion sea única"""
        usuario, estudiante, caja, banco = setup_data

        # Crear primer pago
        Pago.objects.create(
            alumno=estudiante,
            caja=caja,
            monto_total_entregado=Decimal("100.00"),
            metodo_pago="Transferencia",
            banco=banco,
            numero_operacion="OP-12345",
            estado="REGISTRADO",
            usuario_creador=usuario
        )

        # Intentar crear segundo pago con misma combinación
        with pytest.raises(Exception):  # IntegrityError
            Pago.objects.create(
                alumno=estudiante,
                caja=caja,
                monto_total_entregado=Decimal("200.00"),
                metodo_pago="Transferencia",
                banco=banco,
                numero_operacion="OP-12345",  # Mismo número
                estado="REGISTRADO",
                usuario_creador=usuario
            )

    def test_pago_plim_requiere_numero_operacion(self, setup_data):
        """Prueba que Plin requiera número de operación"""
        usuario, estudiante, caja, _ = setup_data
        pago = Pago(
            alumno=estudiante,
            caja=caja,
            monto_total_entregado=Decimal("100.00"),
            metodo_pago="Plin",
            usuario_creador=usuario
        )
        with pytest.raises(ValidationError) as excinfo:
            pago.clean()
        assert "El número de operación es obligatorio para pagos digitales." in str(excinfo.value)

    def test_pago_str(self, setup_data):
        """Prueba el string del pago"""
        usuario, estudiante, caja, _ = setup_data
        pago = Pago.objects.create(
            alumno=estudiante,
            caja=caja,
            monto_total_entregado=Decimal("100.00"),
            metodo_pago="Efectivo",
            estado="REGISTRADO",
            usuario_creador=usuario
        )
        expected = f"Pago {pago.id} - {estudiante} - S/ 100.00"
        assert str(pago) == expected

    def test_pago_deposito_requiere_banco_y_numero(self, setup_data):
        """Prueba que Depósito requiera banco y número de operación"""
        usuario, estudiante, caja, _ = setup_data
        
        # Probar que falta banco
        pago_sin_banco = Pago(
            alumno=estudiante,
            caja=caja,
            monto_total_entregado=Decimal("100.00"),
            metodo_pago="Depósito",
            numero_operacion="12345",
            usuario_creador=usuario
        )
        with pytest.raises(ValidationError) as excinfo:
            pago_sin_banco.clean()
        assert "El banco es obligatorio para transferencias o depósitos." in str(excinfo.value)
        
        # Probar que falta número de operación
        pago_sin_numero = Pago(
            alumno=estudiante,
            caja=caja,
            monto_total_entregado=Decimal("100.00"),
            metodo_pago="Depósito",
            banco=setup_data[3],  # banco
            usuario_creador=usuario
        )
        with pytest.raises(ValidationError) as excinfo:
            pago_sin_numero.clean()
        assert "El número de operación es obligatorio." in str(excinfo.value)


@pytest.mark.django_db
class TestPagoAsignacionModel:
    @pytest.fixture
    def setup_asignacion(self):
        """Fixture para pruebas de asignación"""
        usuario = Usuario.objects.create_user(
            username="cajero_asignacion",
            password="pass123"
        )
        apoderado = Apoderado.objects.create(
            nombres="Ana",
            apellidos="Martínez",
            dni="12345678",
            telefono="999888777"
        )
        estudiante = Estudiante.objects.create(
            nombres="Carlos",
            apellidos="Martínez",
            fecha_nacimiento=date(2020, 5, 10),
            dni="87654321"
        )
        concepto = ConceptoPago.objects.create(
            nombre="Pensión Junio",
            tipo="PENSION",
            monto_base=Decimal("500.00")
        )
        deuda = Deuda.objects.create(
            alumno=estudiante,
            concepto=concepto,
            monto_total=Decimal("500.00"),
            mes=6,
            anio=2026,
            fecha_vencimiento=date(2026, 6, 30)
        )
        caja = Caja.objects.create(
            usuario=usuario,
            monto_inicial=Decimal("1000.00"),
            estado="Abierta"
        )
        pago = Pago.objects.create(
            alumno=estudiante,
            caja=caja,
            monto_total_entregado=Decimal("500.00"),
            metodo_pago="Efectivo",
            estado="APROBADO",
            usuario_creador=usuario
        )
        return {
            'pago': pago,
            'deuda': deuda,
            'estudiante': estudiante,
            'usuario': usuario,
            'caja': caja
        }

    def test_crear_asignacion(self, setup_asignacion):
        """Prueba creación básica de asignación"""
        asignacion = PagoAsignacion.objects.create(
            pago=setup_asignacion['pago'],
            deuda=setup_asignacion['deuda'],
            monto_aplicado=Decimal("500.00")
        )
        assert asignacion.pk is not None
        assert asignacion.monto_aplicado == Decimal("500.00")
        assert asignacion.pago == setup_asignacion['pago']
        assert asignacion.deuda == setup_asignacion['deuda']

    def test_asignacion_actualiza_estado_deuda(self, setup_asignacion):
        """Prueba que asignar un pago actualice el estado de la deuda automáticamente"""
        PagoAsignacion.objects.create(
            pago=setup_asignacion['pago'],
            deuda=setup_asignacion['deuda'],
            monto_aplicado=Decimal("500.00")
        )

        # Verificar que la deuda se actualizó
        deuda = setup_asignacion['deuda']
        deuda.refresh_from_db()
        assert deuda.monto_pagado == Decimal("500.00")
        assert deuda.estado == "Pagado"
        assert deuda.saldo_pendiente == Decimal("0.00")

    def test_asignacion_parcial(self, setup_asignacion):
        """Prueba asignación parcial de un pago"""
        PagoAsignacion.objects.create(
            pago=setup_asignacion['pago'],
            deuda=setup_asignacion['deuda'],
            monto_aplicado=Decimal("200.00")
        )

        deuda = setup_asignacion['deuda']
        deuda.refresh_from_db()
        assert deuda.monto_pagado == Decimal("200.00")
        assert deuda.estado == "Parcial"
        assert deuda.saldo_pendiente == Decimal("300.00")

    def test_multiples_asignaciones_misma_deuda(self, setup_asignacion):
        """Prueba múltiples asignaciones a la misma deuda"""
        # Primera asignación
        PagoAsignacion.objects.create(
            pago=setup_asignacion['pago'],
            deuda=setup_asignacion['deuda'],
            monto_aplicado=Decimal("200.00")
        )

        # Segunda asignación
        pago2 = Pago.objects.create(
            alumno=setup_asignacion['estudiante'],
            caja=setup_asignacion['caja'],
            monto_total_entregado=Decimal("300.00"),
            metodo_pago="Efectivo",
            estado="APROBADO",
            usuario_creador=setup_asignacion['usuario']
        )
        PagoAsignacion.objects.create(
            pago=pago2,
            deuda=setup_asignacion['deuda'],
            monto_aplicado=Decimal("300.00")
        )

        # Verificar acumulación
        deuda = setup_asignacion['deuda']
        deuda.refresh_from_db()
        assert deuda.monto_pagado == Decimal("500.00")
        assert deuda.estado == "Pagado"
        assert deuda.saldo_pendiente == Decimal("0.00")

    def test_asignacion_str(self, setup_asignacion):
        """Prueba el string de la asignación"""
        asignacion = PagoAsignacion.objects.create(
            pago=setup_asignacion['pago'],
            deuda=setup_asignacion['deuda'],
            monto_aplicado=Decimal("500.00")
        )
        expected = f"Asignación de Pago {asignacion.id}"
        assert str(asignacion) == expected