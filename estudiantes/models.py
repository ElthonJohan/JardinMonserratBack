from django.db import models
from django.db import transaction

class Aula(models.Model):
    nombre = models.CharField(max_length=50)  # 2 años, 3 años...
    capacidad = models.IntegerField()

    def __str__(self):
        return self.nombre


class Apoderado(models.Model):
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100,default="Sin Apellidos")
    dni= models.CharField(max_length=8, unique=True, null=True, blank=True)
    telefono = models.CharField(max_length=20)
    email= models.EmailField(default="sin_email@gmail.com")
    direccion = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nombres + " " + self.apellidos



class Estudiante(models.Model):
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    fecha_nacimiento = models.DateField()
    codigo_estudiante = models.CharField(max_length=20, unique=True, null=True, blank=True)
    dni = models.CharField(max_length=8, unique=True, null=True, blank=True)

    

    def save(self, *args, **kwargs):
        # Si el código no ha sido asignado (es una creación nueva)
        if not self.codigo_estudiante:
            # Obtenemos el último ID para asegurar un correlativo real
            ultimo_estudiante = Estudiante.objects.all().order_by('id').last()
            nuevo_id = (ultimo_estudiante.id + 1) if ultimo_estudiante else 1
            
            # Iniciales (usamos 'E' y 'S' como respaldo si fallan los campos)
            inicial_nom = self.nombres[0].upper() if self.nombres else 'E'
            inicial_ape = self.apellidos[0].upper() if self.apellidos else 'S'
            
            self.codigo_estudiante = f"{inicial_nom}{inicial_ape}{nuevo_id:04d}"
            
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nombres} {self.apellidos}"
    

class ApoderadoEstudiante(models.Model):

    TIPO_RELACION = [
        ('PADRE', 'Padre'),
        ('MADRE', 'Madre'),
        ('TUTOR', 'Tutor'),
        ('ABUELO', 'Abuelo'),
        ('OTRO', 'Otro'),
    ]

    apoderado = models.ForeignKey(
        Apoderado,
        on_delete=models.CASCADE,
        related_name='hijos'
    )

    estudiante = models.ForeignKey(
        Estudiante,
        on_delete=models.CASCADE,
        related_name='apoderados'
    )

    tipo_relacion = models.CharField(
        max_length=20,
        choices=TIPO_RELACION
    )

    es_principal = models.BooleanField(default=False)

    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (
            'apoderado',
            'estudiante'
        )
    
    def save(self, *args, **kwargs):

        with transaction.atomic():

            if self.es_principal:

                ApoderadoEstudiante.objects.filter(
                    estudiante=self.estudiante
                ).exclude(
                    pk=self.pk
                ).update(
                    es_principal=False
                )

            super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"{self.apoderado} - "
            f"{self.estudiante} "
            f"({self.tipo_relacion})"
        )