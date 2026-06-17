# estudiantes/tests/test_models.py
import pytest
from datetime import date
from django.db import IntegrityError
from django.db import transaction

from estudiantes.models import Aula, Apoderado, Estudiante, ApoderadoEstudiante


@pytest.mark.django_db
class TestAulaModel:
    """Pruebas para el modelo Aula"""

    def test_crear_aula(self):
        """Prueba creación básica de aula"""
        aula = Aula.objects.create(
            nombre="3 años",
            capacidad=20
        )
        assert aula.nombre == "3 años"
        assert aula.capacidad == 20
        assert str(aula) == "3 años"

    def test_aula_con_capacidad_cero(self):
        """Prueba que una aula pueda tener capacidad 0"""
        aula = Aula.objects.create(
            nombre="Sin capacidad",
            capacidad=0
        )
        assert aula.capacidad == 0

    def test_aula_nombre_no_obligatoriamente_unico(self):
        """Prueba que se puedan crear aulas con el mismo nombre (no es único a nivel de BD)"""
        Aula.objects.create(nombre="4 años", capacidad=25)
        aula2 = Aula.objects.create(nombre="4 años", capacidad=30)
        assert aula2.id is not None


@pytest.mark.django_db
class TestApoderadoModel:
    """Pruebas para el modelo Apoderado"""

    def test_crear_apoderado_completo(self):
        """Prueba creación de apoderado con todos los campos"""
        apoderado = Apoderado.objects.create(
            nombres="Carlos",
            apellidos="Gómez",
            dni="12345678",
            telefono="999888777",
            email="carlos@example.com",
            direccion="Calle 123, Lima"
        )
        assert apoderado.nombres == "Carlos"
        assert apoderado.apellidos == "Gómez"
        assert apoderado.dni == "12345678"
        assert apoderado.telefono == "999888777"
        assert apoderado.email == "carlos@example.com"
        assert apoderado.direccion == "Calle 123, Lima"
        assert str(apoderado) == "Carlos Gómez"

    def test_crear_apoderado_campos_opcionales(self):
        """Prueba creación de apoderado con campos opcionales vacíos"""
        apoderado = Apoderado.objects.create(
            nombres="Maria",
            telefono="999888777"
        )
        assert apoderado.nombres == "Maria"
        assert apoderado.apellidos == "Sin Apellidos"  # Valor por defecto
        assert apoderado.dni is None
        assert apoderado.email == "sin_email@gmail.com"  # Valor por defecto
        assert apoderado.direccion is None

    def test_apoderado_dni_unico(self):
        """Prueba que el DNI sea único cuando se proporciona"""
        Apoderado.objects.create(
            nombres="Carlos",
            apellidos="Gómez",
            dni="12345678",
            telefono="999888777"
        )
        
        with pytest.raises(Exception):  # IntegrityError
            Apoderado.objects.create(
                nombres="Pedro",
                apellidos="Pérez",
                dni="12345678",  # Mismo DNI
                telefono="999888777"
            )

    def test_apoderado_dni_nulo_repetido(self):
        """Prueba que múltiples apoderados puedan tener DNI nulo"""
        Apoderado.objects.create(
            nombres="Carlos",
            telefono="999888777",
            dni=None
        )
        Apoderado.objects.create(
            nombres="Pedro",
            telefono="999888777",
            dni=None
        )
        assert Apoderado.objects.count() == 2

    def test_apoderado_str_con_apellidos(self):
        """Prueba el string del apoderado con apellidos"""
        apoderado = Apoderado.objects.create(
            nombres="María",
            apellidos="López",
            telefono="999888777"
        )
        assert str(apoderado) == "María López"

    def test_apoderado_str_sin_apellidos(self):
        """Prueba el string del apoderado sin apellidos"""
        apoderado = Apoderado.objects.create(
            nombres="María",
            telefono="999888777"
        )
        assert str(apoderado) == "María Sin Apellidos"


@pytest.mark.django_db
class TestEstudianteModel:
    """Pruebas para el modelo Estudiante"""

    def test_crear_estudiante(self):
        """Prueba creación básica de estudiante"""
        estudiante = Estudiante.objects.create(
            nombres="Luis",
            apellidos="Gómez",
            fecha_nacimiento=date(2020, 5, 15),
            dni="87654321"
        )
        assert estudiante.nombres == "Luis"
        assert estudiante.apellidos == "Gómez"
        assert estudiante.fecha_nacimiento == date(2020, 5, 15)
        assert estudiante.dni == "87654321"
        assert str(estudiante) == "Luis Gómez"

    def test_estudiante_genera_codigo_automaticamente(self):
        """Prueba que el código de estudiante se genere automáticamente al crear"""
        estudiante = Estudiante.objects.create(
            nombres="Ana",
            apellidos="Martínez",
            fecha_nacimiento=date(2021, 3, 10),
            dni="12345678"
        )
        # El código debe tener formato: InicialNombre + InicialApellido + ID(4 dígitos)
        # Ejemplo: AM0001
        assert estudiante.codigo_estudiante is not None
        assert len(estudiante.codigo_estudiante) == 6  # 2 letras + 4 números
        assert estudiante.codigo_estudiante.startswith("AM")  # Ana Martínez

    def test_estudiante_codigo_consecutivo(self):
        """Prueba que los códigos sean consecutivos"""
        estudiante1 = Estudiante.objects.create(
            nombres="Luis",
            apellidos="Gómez",
            fecha_nacimiento=date(2020, 5, 15),
            dni="87654321"
        )
        estudiante2 = Estudiante.objects.create(
            nombres="María",
            apellidos="Pérez",
            fecha_nacimiento=date(2021, 6, 20),
            dni="12345678"
        )
        estudiante3 = Estudiante.objects.create(
            nombres="Pedro",
            apellidos="Alva",
            fecha_nacimiento=date(2021, 7, 25),
            dni="11112222"
        )
        
        # El código debe ser secuencial para los creados subsecuentemente
        codigo2 = estudiante2.codigo_estudiante
        codigo3 = estudiante3.codigo_estudiante
        
        # Los últimos 4 dígitos deben ser consecutivos
        id2 = int(codigo2[-4:])
        id3 = int(codigo3[-4:])
        assert id3 == id2 + 1

    def test_estudiante_codigo_con_iniciales_correctas(self):
        """Prueba que el código use las iniciales correctas"""
        estudiante = Estudiante.objects.create(
            nombres="Carlos Alberto",
            apellidos="González Pérez",
            fecha_nacimiento=date(2020, 5, 15),
            dni="87654321"
        )
        # Debe usar la primera letra del primer nombre y primer apellido
        assert estudiante.codigo_estudiante.startswith("CG")

    def test_estudiante_codigo_con_nombres_vacios(self):
        """Prueba que el código use valores por defecto si nombres/apellidos están vacíos"""
        estudiante = Estudiante.objects.create(
            nombres="",
            apellidos="",
            fecha_nacimiento=date(2020, 5, 15),
            dni="87654321"
        )
        # Debe usar 'E' y 'S' como respaldo
        assert estudiante.codigo_estudiante.startswith("ES")

    def test_estudiante_dni_unico(self):
        """Prueba que el DNI sea único"""
        Estudiante.objects.create(
            nombres="Luis",
            apellidos="Gómez",
            fecha_nacimiento=date(2020, 5, 15),
            dni="87654321"
        )
        
        with pytest.raises(Exception):  # IntegrityError
            Estudiante.objects.create(
                nombres="Pedro",
                apellidos="Pérez",
                fecha_nacimiento=date(2021, 6, 20),
                dni="87654321"  # Mismo DNI
            )

    def test_estudiante_dni_nulo_repetido(self):
        """Prueba que múltiples estudiantes puedan tener DNI nulo"""
        Estudiante.objects.create(
            nombres="Luis",
            apellidos="Gómez",
            fecha_nacimiento=date(2020, 5, 15),
            dni=None
        )
        Estudiante.objects.create(
            nombres="Pedro",
            apellidos="Pérez",
            fecha_nacimiento=date(2021, 6, 20),
            dni=None
        )
        assert Estudiante.objects.count() == 2

    def test_estudiante_no_sobrescribe_codigo_existente(self):
        """Prueba que el código no se sobrescriba si ya existe"""
        estudiante = Estudiante.objects.create(
            nombres="Luis",
            apellidos="Gómez",
            fecha_nacimiento=date(2020, 5, 15),
            dni="87654321"
        )
        codigo_original = estudiante.codigo_estudiante
        
        # Modificar y guardar
        estudiante.nombres = "Carlos"
        estudiante.save()
        estudiante.refresh_from_db()
        
        # El código no debe cambiar
        assert estudiante.codigo_estudiante == codigo_original


@pytest.mark.django_db
class TestApoderadoEstudianteModel:
    """Pruebas para el modelo ApoderadoEstudiante (relación Many-to-Many)"""

    @pytest.fixture
    def setup_relacion(self):
        """Configuración base para pruebas de relación"""
        apoderado = Apoderado.objects.create(
            nombres="Carlos",
            apellidos="Gómez",
            dni="12345678",
            telefono="999888777"
        )
        apoderado2 = Apoderado.objects.create(
            nombres="María",
            apellidos="López",
            dni="87654321",
            telefono="999888777"
        )
        estudiante = Estudiante.objects.create(
            nombres="Luis",
            apellidos="Gómez",
            fecha_nacimiento=date(2020, 5, 15),
            dni="11111111"
        )
        return {
            'apoderado': apoderado,
            'apoderado2': apoderado2,
            'estudiante': estudiante
        }

    def test_crear_relacion_apoderado_estudiante(self, setup_relacion):
        """Prueba creación de relación entre apoderado y estudiante"""
        relacion = ApoderadoEstudiante.objects.create(
            apoderado=setup_relacion['apoderado'],
            estudiante=setup_relacion['estudiante'],
            tipo_relacion="PADRE",
            es_principal=True
        )
        assert relacion.apoderado == setup_relacion['apoderado']
        assert relacion.estudiante == setup_relacion['estudiante']
        assert relacion.tipo_relacion == "PADRE"
        assert relacion.es_principal is True
        assert relacion.fecha_registro is not None

    def test_relacion_unica_por_apoderado_estudiante(self, setup_relacion):
        """Prueba que no se pueda duplicar la misma relación"""
        ApoderadoEstudiante.objects.create(
            apoderado=setup_relacion['apoderado'],
            estudiante=setup_relacion['estudiante'],
            tipo_relacion="PADRE",
            es_principal=True
        )
        
        with pytest.raises(Exception):  # IntegrityError por unique_together
            ApoderadoEstudiante.objects.create(
                apoderado=setup_relacion['apoderado'],
                estudiante=setup_relacion['estudiante'],
                tipo_relacion="MADRE",
                es_principal=False
            )

    def test_relacion_principal_unica_por_estudiante(self, setup_relacion):
        """Prueba que solo un apoderado pueda ser principal por estudiante"""
        # Crear primer apoderado principal
        relacion1 = ApoderadoEstudiante.objects.create(
            apoderado=setup_relacion['apoderado'],
            estudiante=setup_relacion['estudiante'],
            tipo_relacion="PADRE",
            es_principal=True
        )
        
        # Crear segundo apoderado también como principal (debería desmarcar el anterior)
        relacion2 = ApoderadoEstudiante.objects.create(
            apoderado=setup_relacion['apoderado2'],
            estudiante=setup_relacion['estudiante'],
            tipo_relacion="MADRE",
            es_principal=True
        )
        
        # Recargar desde BD
        relacion1.refresh_from_db()
        relacion2.refresh_from_db()
        
        # Solo el segundo debe ser principal
        assert relacion1.es_principal is False
        assert relacion2.es_principal is True

    def test_relacion_principal_no_afecta_otros_estudiantes(self, setup_relacion):
        """Prueba que cambiar principal en un estudiante no afecte a otros"""
        # Crear otro estudiante
        estudiante2 = Estudiante.objects.create(
            nombres="Ana",
            apellidos="Martínez",
            fecha_nacimiento=date(2021, 3, 10),
            dni="22222222"
        )
        
        # Crear relación principal para estudiante1
        relacion1 = ApoderadoEstudiante.objects.create(
            apoderado=setup_relacion['apoderado'],
            estudiante=setup_relacion['estudiante'],
            tipo_relacion="PADRE",
            es_principal=True
        )
        
        # Crear relación para estudiante2 con mismo apoderado
        relacion2 = ApoderadoEstudiante.objects.create(
            apoderado=setup_relacion['apoderado'],
            estudiante=estudiante2,
            tipo_relacion="PADRE",
            es_principal=True
        )
        
        # Verificar que ambas son principales (no se afectan entre sí)
        relacion1.refresh_from_db()
        relacion2.refresh_from_db()
        assert relacion1.es_principal is True
        assert relacion2.es_principal is True

    def test_tipos_relacion_validos(self, setup_relacion):
        """Prueba que los tipos de relación válidos funcionen"""
        tipos = ['PADRE', 'MADRE', 'TUTOR', 'ABUELO', 'OTRO']
        
        for tipo in tipos:
            relacion = ApoderadoEstudiante.objects.create(
                apoderado=setup_relacion['apoderado'],
                estudiante=setup_relacion['estudiante'],
                tipo_relacion=tipo,
                es_principal=False
            )
            assert relacion.tipo_relacion == tipo
            relacion.delete()

    def test_relacion_str(self, setup_relacion):
        """Prueba el string de la relación"""
        relacion = ApoderadoEstudiante.objects.create(
            apoderado=setup_relacion['apoderado'],
            estudiante=setup_relacion['estudiante'],
            tipo_relacion="PADRE",
            es_principal=True
        )
        expected = f"{setup_relacion['apoderado']} - {setup_relacion['estudiante']} (PADRE)"
        assert str(relacion) == expected

    def test_relacion_con_apoderado_y_estudiante_multiples(self, setup_relacion):
        """Prueba que un apoderado pueda tener múltiples hijos y viceversa"""
        # Crear otro estudiante
        estudiante2 = Estudiante.objects.create(
            nombres="Ana",
            apellidos="Gómez",
            fecha_nacimiento=date(2021, 3, 10),
            dni="22222222"
        )
        
        # Mismo apoderado con dos estudiantes
        ApoderadoEstudiante.objects.create(
            apoderado=setup_relacion['apoderado'],
            estudiante=setup_relacion['estudiante'],
            tipo_relacion="PADRE",
            es_principal=True
        )
        ApoderadoEstudiante.objects.create(
            apoderado=setup_relacion['apoderado'],
            estudiante=estudiante2,
            tipo_relacion="PADRE",
            es_principal=True
        )
        
        # Verificar que el apoderado tiene 2 hijos
        hijos = setup_relacion['apoderado'].hijos.all()
        assert hijos.count() == 2
        
        # Verificar que el estudiante tiene 1 apoderado
        apoderados = setup_relacion['estudiante'].apoderados.all()
        assert apoderados.count() == 1


@pytest.mark.django_db
class TestRelacionesEntreModelos:
    """Pruebas de integración entre modelos"""

    def test_estudiante_con_apoderados(self):
        """Prueba que un estudiante pueda tener múltiples apoderados"""
        # Crear apoderados
        apoderado1 = Apoderado.objects.create(
            nombres="Carlos",
            apellidos="Gómez",
            dni="12345678",
            telefono="999888777"
        )
        apoderado2 = Apoderado.objects.create(
            nombres="María",
            apellidos="López",
            dni="87654321",
            telefono="999888777"
        )
        
        # Crear estudiante
        estudiante = Estudiante.objects.create(
            nombres="Luis",
            apellidos="Gómez",
            fecha_nacimiento=date(2020, 5, 15),
            dni="11111111"
        )
        
        # Crear relaciones
        ApoderadoEstudiante.objects.create(
            apoderado=apoderado1,
            estudiante=estudiante,
            tipo_relacion="PADRE",
            es_principal=True
        )
        ApoderadoEstudiante.objects.create(
            apoderado=apoderado2,
            estudiante=estudiante,
            tipo_relacion="MADRE",
            es_principal=False
        )
        
        # Verificar que el estudiante tiene 2 apoderados
        apoderados = estudiante.apoderados.all()
        assert apoderados.count() == 2
        
        # Verificar que el apoderado principal es el primero
        principal = estudiante.apoderados.filter(es_principal=True).first()
        assert principal.apoderado == apoderado1

    def test_apoderado_con_multiples_estudiantes(self):
        """Prueba que un apoderado pueda tener múltiples estudiantes"""
        # Crear apoderado
        apoderado = Apoderado.objects.create(
            nombres="Carlos",
            apellidos="Gómez",
            dni="12345678",
            telefono="999888777"
        )
        
        # Crear estudiantes
        estudiante1 = Estudiante.objects.create(
            nombres="Luis",
            apellidos="Gómez",
            fecha_nacimiento=date(2020, 5, 15),
            dni="11111111"
        )
        estudiante2 = Estudiante.objects.create(
            nombres="Ana",
            apellidos="Gómez",
            fecha_nacimiento=date(2021, 3, 10),
            dni="22222222"
        )
        
        # Crear relaciones
        ApoderadoEstudiante.objects.create(
            apoderado=apoderado,
            estudiante=estudiante1,
            tipo_relacion="PADRE",
            es_principal=True
        )
        ApoderadoEstudiante.objects.create(
            apoderado=apoderado,
            estudiante=estudiante2,
            tipo_relacion="PADRE",
            es_principal=True
        )
        
        # Verificar que el apoderado tiene 2 hijos
        hijos = apoderado.hijos.all()
        assert hijos.count() == 2