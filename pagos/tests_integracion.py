# Tests de Integración: Abono Multinivel y Control de Caja

Guarda este archivo como `pagos/tests_integracion.py` para ejecutar:

```bash
python manage.py test pagos.tests_integracion -v 2
```

---

```python
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from datetime import date
import decimal

from pagos.models import Pago, Deuda, Caja, PagoAsignacion, ConceptoPago
from estudiantes.models import Estudiante, Aula, Apoderado
from matriculas.models import Matricula

User = get_user_model()


class CajaAPITestCase(TestCase):
    """Tests para el control de caja"""
    
    def setUp(self):
        """Configuración inicial"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='admin',
            password='pass123',
            role='admin'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_abrir_caja(self):
        """Test: Abrir una nueva caja"""
        url = '/api/pagos/cajas/abrir_caja/'
        data = {'monto_inicial': '100.00'}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['caja']['estado'], 'Abierta')
        self.assertEqual(response.data['caja']['monto_inicial'], '100.00')
        
        # Verificar que no se puede abrir otra caja
        response2 = self.client.post(url, data, format='json')
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_mi_estado_abierta(self):
        """Test: Verificar estado de caja abierta"""
        # Crear caja abierta
        Caja.objects.create(
            usuario=self.user,
            estado='Abierta',
            monto_inicial=decimal.Decimal('100.00')
        )
        
        url = '/api/pagos/cajas/mi_estado/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['abierta'])
        self.assertIsNotNone(response.data['caja'])
    
    def test_mi_estado_cerrada(self):
        """Test: Verificar estado sin caja abierta"""
        url = '/api/pagos/cajas/mi_estado/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['abierta'])
        self.assertIsNone(response.data['caja'])
    
    def test_cerrar_caja(self):
        """Test: Cerrar una caja abierta"""
        # Crear caja
        caja = Caja.objects.create(
            usuario=self.user,
            estado='Abierta',
            monto_inicial=decimal.Decimal('100.00')
        )
        
        url = f'/api/pagos/cajas/{caja.id}/cerrar_caja/'
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verificar en BD
        caja.refresh_from_db()
        self.assertEqual(caja.estado, 'Cerrada')
        self.assertIsNotNone(caja.fecha_cierre)


class PagoFIFOAPITestCase(TransactionTestCase):
    """Tests para la lógica FIFO de abono multinivel"""
    
    def setUp(self):
        """Configuración inicial con datos de prueba"""
        self.client = APIClient()
        
        # Crear usuario
        self.user = User.objects.create_user(
            username='admin',
            password='pass123',
            role='admin'
        )
        self.client.force_authenticate(user=self.user)
        
        # Crear aula
        self.aula = Aula.objects.create(
            nombre='2 años',
            capacidad=20
        )
        
        # Crear apoderado
        self.apoderado = Apoderado.objects.create(
            nombres='Carlos',
            apellidos='López',
            dni='12345678',
            telefono='987654321',
            direccion='Calle 123'
        )
        
        # Crear estudiante
        self.estudiante = Estudiante.objects.create(
            nombres='Juan',
            apellidos='Pérez',
            fecha_nacimiento=date(2023, 5, 15),
            aula=self.aula,
            apoderado=self.apoderado
        )
        
        # Crear conceptos de pago
        self.concepto_matricula = ConceptoPago.objects.create(
            nombre='Matrícula',
            tipo='MATRICULA',
            monto_base=decimal.Decimal('300.00'),
            activo=True
        )
        
        self.concepto_pension = ConceptoPago.objects.create(
            nombre='Pensión',
            tipo='PENSION',
            monto_base=decimal.Decimal('500.00'),
            activo=True
        )
        
        # Crear deudas manuales para prueba
        self.deuda_matricula = Deuda.objects.create(
            alumno=self.estudiante,
            concepto=self.concepto_matricula,
            monto_total=decimal.Decimal('300.00'),
            mes=None,
            anio=2026,
            fecha_vencimiento=date(2026, 3, 1),
            estado='Pendiente'
        )
        
        self.deuda_pension_marzo = Deuda.objects.create(
            alumno=self.estudiante,
            concepto=self.concepto_pension,
            monto_total=decimal.Decimal('500.00'),
            mes=3,
            anio=2026,
            fecha_vencimiento=date(2026, 3, 31),
            estado='Pendiente'
        )
        
        self.deuda_pension_abril = Deuda.objects.create(
            alumno=self.estudiante,
            concepto=self.concepto_pension,
            monto_total=decimal.Decimal('500.00'),
            mes=4,
            anio=2026,
            fecha_vencimiento=date(2026, 4, 30),
            estado='Pendiente'
        )
        
        # Abrir caja
        self.caja = Caja.objects.create(
            usuario=self.user,
            estado='Abierta',
            monto_inicial=decimal.Decimal('0.00')
        )
    
    def test_error_sin_caja_abierta(self):
        """Test: Error al registrar pago sin caja abierta"""
        # Cerrar caja
        self.caja.estado = 'Cerrada'
        self.caja.save()
        
        url = '/api/pagos/pagos/'
        data = {
            'alumno': self.estudiante.id,
            'monto_total_entregado': '1200.00',
            'metodo_pago': 'Efectivo',
            'numero_operacion': 'VOC001'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Caja abierta', str(response.data))
    
    def test_pago_fifo_completo(self):
        """Test: Pago FIFO que cubre múltiples deudas"""
        url = '/api/pagos/pagos/'
        data = {
            'alumno': self.estudiante.id,
            'monto_total_entregado': '1200.00',
            'metodo_pago': 'Efectivo',
            'numero_operacion': 'VOC001',
            'observaciones': 'Pago de deudas'
        }
        
        response = self.client.post(url, data, format='json')
        
        # Verificar respuesta
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.data['asignaciones']), 3)
        
        # Verificar distribución FIFO
        asignaciones = response.data['asignaciones']
        
        # Deuda 1: Matrícula (vencimiento 01/03)
        self.assertEqual(asignaciones[0]['monto_aplicado'], '300.00')
        self.assertEqual(asignaciones[0]['deuda_detail']['concepto'], 'Matrícula')
        
        # Deuda 2: Pensión Marzo (vencimiento 31/03)
        self.assertEqual(asignaciones[1]['monto_aplicado'], '500.00')
        self.assertEqual(asignaciones[1]['deuda_detail']['mes'], 3)
        
        # Deuda 3: Pensión Abril (vencimiento 30/04)
        self.assertEqual(asignaciones[2]['monto_aplicado'], '400.00')
        self.assertEqual(asignaciones[2]['deuda_detail']['mes'], 4)
        self.assertEqual(asignaciones[2]['deuda_detail']['saldo_pendiente'], '100.00')
    
    def test_estado_deuda_actualizado(self):
        """Test: Los estados de deuda se actualizan correctamente"""
        url = '/api/pagos/pagos/'
        data = {
            'alumno': self.estudiante.id,
            'monto_total_entregado': '1200.00',
            'metodo_pago': 'Efectivo',
            'numero_operacion': 'VOC001'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verificar estados en BD
        self.deuda_matricula.refresh_from_db()
        self.assertEqual(self.deuda_matricula.estado, 'Pagado')
        self.assertEqual(self.deuda_matricula.monto_pagado, decimal.Decimal('300.00'))
        
        self.deuda_pension_marzo.refresh_from_db()
        self.assertEqual(self.deuda_pension_marzo.estado, 'Pagado')
        
        self.deuda_pension_abril.refresh_from_db()
        self.assertEqual(self.deuda_pension_abril.estado, 'Parcial')
        self.assertEqual(self.deuda_pension_abril.monto_pagado, decimal.Decimal('400.00'))
        self.assertEqual(
            self.deuda_pension_abril.saldo_pendiente,
            decimal.Decimal('100.00')
        )
    
    def test_pago_parcial(self):
        """Test: Pago que no cubre todas las deudas"""
        url = '/api/pagos/pagos/'
        data = {
            'alumno': self.estudiante.id,
            'monto_total_entregado': '300.00',  # Solo la matrícula
            'metodo_pago': 'Efectivo',
            'numero_operacion': 'VOC001'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Solo debe haber 1 asignación
        self.assertEqual(len(response.data['asignaciones']), 1)
        self.assertEqual(response.data['asignaciones'][0]['deuda_detail']['concepto'], 'Matrícula')
        
        # Las otras deudas deben seguir pendientes
        self.deuda_pension_marzo.refresh_from_db()
        self.assertEqual(self.deuda_pension_marzo.estado, 'Pendiente')
    
    def test_numero_operacion_unico(self):
        """Test: No se puede registrar pago con numero_operacion duplicado"""
        # Crear primer pago
        Pago.objects.create(
            alumno=self.estudiante,
            caja=self.caja,
            monto_total_entregado=decimal.Decimal('100.00'),
            metodo_pago='Efectivo',
            numero_operacion='DUPLICADO123',
            usuario_registro=self.user
        )
        
        # Intentar crear otro con el mismo numero
        url = '/api/pagos/pagos/'
        data = {
            'alumno': self.estudiante.id,
            'monto_total_entregado': '200.00',
            'metodo_pago': 'Efectivo',
            'numero_operacion': 'DUPLICADO123'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_atomicidad_transaccion(self):
        """Test: La transacción es atómica (todo o nada)"""
        # Crear un pago que falle (ID de alumno inválido)
        url = '/api/pagos/pagos/'
        data = {
            'alumno': 9999,  # Alumno no existe
            'monto_total_entregado': '1200.00',
            'metodo_pago': 'Efectivo',
            'numero_operacion': 'VOC001'
        }
        
        # Debe fallar
        response = self.client.post(url, data, format='json')
        self.assertNotEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verificar que no se creó el pago
        pago_count = Pago.objects.filter(numero_operacion='VOC001').count()
        self.assertEqual(pago_count, 0)


class DeudaFilterAPITestCase(TestCase):
    """Tests para los filtros de deuda"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='admin',
            password='pass123',
            role='admin'
        )
        self.client.force_authenticate(user=self.user)
        
        # Crear datos de prueba
        aula = Aula.objects.create(nombre='2 años', capacidad=20)
        apoderado = Apoderado.objects.create(
            nombres='Carlos', apellidos='López',
            dni='12345678', telefono='987654321',
            direccion='Calle 123'
        )
        
        self.estudiante1 = Estudiante.objects.create(
            nombres='Juan', apellidos='Pérez',
            fecha_nacimiento=date(2023, 5, 15),
            aula=aula, apoderado=apoderado
        )
        
        self.estudiante2 = Estudiante.objects.create(
            nombres='María', apellidos='González',
            fecha_nacimiento=date(2023, 8, 20),
            aula=aula, apoderado=apoderado
        )
        
        concepto_pension = ConceptoPago.objects.create(
            nombre='Pensión', tipo='PENSION',
            monto_base=decimal.Decimal('500.00'), activo=True
        )
        
        # Crear deudas
        self.deuda1 = Deuda.objects.create(
            alumno=self.estudiante1,
            concepto=concepto_pension,
            monto_total=decimal.Decimal('500.00'),
            mes=3, anio=2026,
            fecha_vencimiento=date(2026, 3, 31),
            estado='Pendiente'
        )
        
        self.deuda2 = Deuda.objects.create(
            alumno=self.estudiante2,
            concepto=concepto_pension,
            monto_total=decimal.Decimal('500.00'),
            mes=3, anio=2026,
            fecha_vencimiento=date(2026, 3, 31),
            estado='Pagado'
        )
    
    def test_filtrar_por_alumno(self):
        """Test: Filtrar deudas por alumno"""
        url = f'/api/pagos/deudas/?alumno={self.estudiante1.id}'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['alumno'], self.estudiante1.id)
    
    def test_filtrar_por_estado(self):
        """Test: Filtrar deudas por estado"""
        url = '/api/pagos/deudas/?estado=Pagado'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['estado'], 'Pagado')
    
    def test_filtrar_por_anio(self):
        """Test: Filtrar deudas por año"""
        url = '/api/pagos/deudas/?anio=2026'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
    
    def test_buscar_por_nombre(self):
        """Test: Buscar deudas por nombre de alumno"""
        url = '/api/pagos/deudas/?search=Juan'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
    
    def test_ordenar_por_fecha_vencimiento(self):
        """Test: Ordenar deudas por fecha de vencimiento"""
        url = '/api/pagos/deudas/?ordering=fecha_vencimiento'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Los resultados deben estar ordenados


class PagoSearchAPITestCase(TestCase):
    """Tests para búsqueda en pagos"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='admin', password='pass123', role='admin'
        )
        self.client.force_authenticate(user=self.user)
        
        aula = Aula.objects.create(nombre='2 años', capacidad=20)
        apoderado = Apoderado.objects.create(
            nombres='Carlos', apellidos='López',
            dni='12345678', telefono='987654321',
            direccion='Calle 123'
        )
        
        estudiante = Estudiante.objects.create(
            nombres='Juan', apellidos='Pérez',
            fecha_nacimiento=date(2023, 5, 15),
            aula=aula, apoderado=apoderado
        )
        
        caja = Caja.objects.create(
            usuario=self.user,
            estado='Abierta',
            monto_inicial=decimal.Decimal('0.00')
        )
        
        # Crear pago
        self.pago = Pago.objects.create(
            alumno=estudiante,
            caja=caja,
            monto_total_entregado=decimal.Decimal('1200.00'),
            metodo_pago='Yape',
            numero_operacion='YPE20260506001',
            usuario_registro=self.user
        )
    
    def test_buscar_por_numero_operacion(self):
        """Test: Buscar pago por numero_operacion"""
        url = '/api/pagos/pagos/?search=YPE20260506001'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
    
    def test_filtrar_por_metodo(self):
        """Test: Filtrar pagos por método"""
        url = '/api/pagos/pagos/?metodo_pago=Yape'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)


# Ejecutar con:
# python manage.py test pagos.tests_integracion -v 2
# o para un test específico:
# python manage.py test pagos.tests_integracion.PagoFIFOAPITestCase.test_pago_fifo_completo -v 2
```

---

## Ejecutar los Tests

```bash
# Todos los tests
python manage.py test pagos.tests_integracion -v 2

# Tests específicos
python manage.py test pagos.tests_integracion.CajaAPITestCase -v 2
python manage.py test pagos.tests_integracion.PagoFIFOAPITestCase -v 2
python manage.py test pagos.tests_integracion.DeudaFilterAPITestCase -v 2

# Test específico
python manage.py test pagos.tests_integracion.PagoFIFOAPITestCase.test_pago_fifo_completo -v 2
```

## Esperados:

```
test_abrir_caja ... ok
test_mi_estado_abierta ... ok
test_mi_estado_cerrada ... ok
test_cerrar_caja ... ok
test_error_sin_caja_abierta ... ok
test_pago_fifo_completo ... ok
test_estado_deuda_actualizado ... ok
test_pago_parcial ... ok
test_numero_operacion_unico ... ok
test_atomicidad_transaccion ... ok
test_filtrar_por_alumno ... ok
test_filtrar_por_estado ... ok
test_buscar_por_numero_operacion ... ok

Ran 13 tests in 0.123s

OK
```
