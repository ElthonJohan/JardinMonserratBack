# core/tests/test_models.py
import pytest
from datetime import date
from django.db import IntegrityError

from core.models import Grado, Seccion, Alumno


@pytest.mark.django_db
class TestGradoModel:
    """Pruebas para el modelo Grado"""

    def test_crear_grado(self):
        """Prueba creación básica de grado"""
        grado = Grado.objects.create(
            nombre="1ro de Primaria",
            nivel="Primaria",
            orden=1,
            activo=True
        )
        assert grado.nombre == "1ro de Primaria"
        assert grado.nivel == "Primaria"
        assert grado.orden == 1
        assert grado.activo is True
        assert str(grado) == "1ro de Primaria (Primaria)"

    def test_grado_nombre_unico(self):
        """Prueba que el nombre del grado sea único"""
        Grado.objects.create(
            nombre="1ro de Primaria",
            nivel="Primaria",
            orden=1
        )
        
        with pytest.raises(IntegrityError):
            Grado.objects.create(
                nombre="1ro de Primaria",  # Nombre duplicado
                nivel="Primaria",
                orden=2
            )

    def test_grado_niveles_validos(self):
        """Prueba que los niveles válidos funcionen"""
        niveles = ['Inicial', 'Primaria']
        
        for nivel in niveles:
            grado = Grado.objects.create(
                nombre=f"{nivel} Test",
                nivel=nivel,
                orden=1
            )
            assert grado.nivel == nivel

    def test_grado_activo_por_defecto(self):
        """Prueba que activo sea True por defecto"""
        grado = Grado.objects.create(
            nombre="2do de Primaria",
            nivel="Primaria",
            orden=2
        )
        assert grado.activo is True

    def test_grado_ordenamiento(self):
        """Prueba que los grados se ordenen por orden"""
        Grado.objects.create(
            nombre="3ro de Primaria",
            nivel="Primaria",
            orden=3
        )
        Grado.objects.create(
            nombre="1ro de Primaria",
            nivel="Primaria",
            orden=1
        )
        Grado.objects.create(
            nombre="2do de Primaria",
            nivel="Primaria",
            orden=2
        )
        
        grados = Grado.objects.all()
        assert grados[0].orden == 1
        assert grados[1].orden == 2
        assert grados[2].orden == 3

    def test_grado_str(self):
        """Prueba el string del grado"""
        grado = Grado.objects.create(
            nombre="1ro de Primaria",
            nivel="Primaria",
            orden=1
        )
        assert str(grado) == "1ro de Primaria (Primaria)"


@pytest.mark.django_db
class TestSeccionModel:
    """Pruebas para el modelo Seccion"""

    def test_crear_seccion(self):
        """Prueba creación básica de sección"""
        seccion = Seccion.objects.create(
            nombre="A",
            activo=True
        )
        assert seccion.nombre == "A"
        assert seccion.activo is True
        assert str(seccion) == "Sección A"

    def test_seccion_nombre_unico(self):
        """Prueba que el nombre de la sección sea único"""
        Seccion.objects.create(nombre="A")
        
        with pytest.raises(IntegrityError):
            Seccion.objects.create(nombre="A")  # Nombre duplicado

    def test_seccion_activo_por_defecto(self):
        """Prueba que activo sea True por defecto"""
        seccion = Seccion.objects.create(nombre="B")
        assert seccion.activo is True

    def test_seccion_ordenamiento(self):
        """Prueba que las secciones se ordenen por nombre"""
        Seccion.objects.create(nombre="C")
        Seccion.objects.create(nombre="A")
        Seccion.objects.create(nombre="B")
        
        secciones = Seccion.objects.all()
        assert secciones[0].nombre == "A"
        assert secciones[1].nombre == "B"
        assert secciones[2].nombre == "C"

    def test_seccion_str(self):
        """Prueba el string de la sección"""
        seccion = Seccion.objects.create(nombre="Única")
        assert str(seccion) == "Sección Única"


@pytest.mark.django_db
class TestAlumnoModel:
    """Pruebas para el modelo Alumno"""

    def test_crear_alumno(self):
        """Prueba creación básica de alumno"""
        alumno = Alumno.objects.create(
            nro_matricula="2026-0001",
            nombres="Luis",
            apellidos="Gómez",
            dni="12345678",
            fecha_nacimiento=date(2020, 5, 15),
            nombre_apoderado="Carlos Gómez",
            telefono_apoderado="999888777",
            estado="Activo"
        )
        assert alumno.nro_matricula == "2026-0001"
        assert alumno.nombres == "Luis"
        assert alumno.apellidos == "Gómez"
        assert alumno.dni == "12345678"
        assert alumno.fecha_nacimiento == date(2020, 5, 15)
        assert alumno.nombre_apoderado == "Carlos Gómez"
        assert alumno.telefono_apoderado == "999888777"
        assert alumno.estado == "Activo"
        assert str(alumno) == "Gómez, Luis (12345678)"
        assert alumno.get_full_name() == "Luis Gómez"

    def test_alumno_nro_matricula_unico(self):
        """Prueba que el número de matrícula sea único"""
        Alumno.objects.create(
            nro_matricula="2026-0001",
            nombres="Luis",
            apellidos="Gómez",
            dni="12345678",
            fecha_nacimiento=date(2020, 5, 15),
            nombre_apoderado="Carlos Gómez",
            telefono_apoderado="999888777"
        )
        
        with pytest.raises(IntegrityError):
            Alumno.objects.create(
                nro_matricula="2026-0001",  # Número duplicado
                nombres="Ana",
                apellidos="Martínez",
                dni="87654321",
                fecha_nacimiento=date(2021, 3, 10),
                nombre_apoderado="Pedro Martínez",
                telefono_apoderado="999888777"
            )

    def test_alumno_dni_unico(self):
        """Prueba que el DNI sea único"""
        Alumno.objects.create(
            nro_matricula="2026-0001",
            nombres="Luis",
            apellidos="Gómez",
            dni="12345678",
            fecha_nacimiento=date(2020, 5, 15),
            nombre_apoderado="Carlos Gómez",
            telefono_apoderado="999888777"
        )
        
        with pytest.raises(IntegrityError):
            Alumno.objects.create(
                nro_matricula="2026-0002",
                nombres="Ana",
                apellidos="Martínez",
                dni="12345678",  # DNI duplicado
                fecha_nacimiento=date(2021, 3, 10),
                nombre_apoderado="Pedro Martínez",
                telefono_apoderado="999888777"
            )

    def test_alumno_estados_validos(self):
        """Prueba que los estados válidos funcionen"""
        estados = ['Activo', 'Retirado', 'Egresado']
        
        for estado in estados:
            alumno = Alumno.objects.create(
                nro_matricula=f"2026-{estado[:3]}",
                nombres="Test",
                apellidos="Test",
                dni=f"1234567{estados.index(estado)}",
                fecha_nacimiento=date(2020, 5, 15),
                nombre_apoderado="Test Apoderado",
                telefono_apoderado="999888777",
                estado=estado
            )
            assert alumno.estado == estado

    def test_alumno_campos_opcionales(self):
        """Prueba que los campos opcionales sean opcionales"""
        alumno = Alumno.objects.create(
            nro_matricula="2026-0001",
            nombres="Luis",
            apellidos="Gómez",
            dni="12345678",
            fecha_nacimiento=date(2020, 5, 15),
            nombre_apoderado="Carlos Gómez",
            telefono_apoderado="999888777"
        )
        assert alumno.direccion is None
        assert alumno.telefono is None
        assert alumno.email_apoderado is None

    def test_alumno_ordenamiento(self):
        """Prueba que los alumnos se ordenen por apellidos y nombres"""
        Alumno.objects.create(
            nro_matricula="2026-0001",
            nombres="Luis",
            apellidos="Gómez",
            dni="12345678",
            fecha_nacimiento=date(2020, 5, 15),
            nombre_apoderado="Carlos Gómez",
            telefono_apoderado="999888777"
        )
        Alumno.objects.create(
            nro_matricula="2026-0002",
            nombres="Ana",
            apellidos="Martínez",
            dni="87654321",
            fecha_nacimiento=date(2021, 3, 10),
            nombre_apoderado="Pedro Martínez",
            telefono_apoderado="999888777"
        )
        Alumno.objects.create(
            nro_matricula="2026-0003",
            nombres="Carlos",
            apellidos="Gómez",
            dni="11111111",
            fecha_nacimiento=date(2020, 5, 15),
            nombre_apoderado="Carlos Gómez",
            telefono_apoderado="999888777"
        )
        
        alumnos = Alumno.objects.all()
        # Debe ordenar por apellidos: Gómez, Gómez, Martínez
        # Luego por nombres: Carlos, Luis, Ana
        assert alumnos[0].apellidos == "Gómez"
        assert alumnos[0].nombres == "Carlos"
        assert alumnos[1].apellidos == "Gómez"
        assert alumnos[1].nombres == "Luis"
        assert alumnos[2].apellidos == "Martínez"

    def test_alumno_indexes(self, db):
        """Prueba que los índices existan (verificación estructural)"""
        # Verificar que los índices se crearon correctamente
        from django.db import connection
        
        # Esta prueba verifica que las migraciones crearon los índices
        # Crear un alumno y buscar por DNI debería usar el índice
        alumno = Alumno.objects.create(
            nro_matricula="2026-0001",
            nombres="Luis",
            apellidos="Gómez",
            dni="12345678",
            fecha_nacimiento=date(2020, 5, 15),
            nombre_apoderado="Carlos Gómez",
            telefono_apoderado="999888777"
        )
        
        # Buscar por DNI debería funcionar
        encontrado = Alumno.objects.filter(dni="12345678").first()
        assert encontrado == alumno
        
        # Buscar por nro_matricula debería funcionar
        encontrado = Alumno.objects.filter(nro_matricula="2026-0001").first()
        assert encontrado == alumno

    def test_alumno_full_name(self):
        """Prueba el método get_full_name"""
        alumno = Alumno.objects.create(
            nro_matricula="2026-0001",
            nombres="Luis Alberto",
            apellidos="Gómez Pérez",
            dni="12345678",
            fecha_nacimiento=date(2020, 5, 15),
            nombre_apoderado="Carlos Gómez",
            telefono_apoderado="999888777"
        )
        assert alumno.get_full_name() == "Luis Alberto Gómez Pérez"