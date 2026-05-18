from django.db import models

class Aula(models.Model):
    nombre = models.CharField(max_length=50)  # 2 años, 3 años...
    capacidad = models.IntegerField()

    def __str__(self):
        return self.nombre


class Apoderado(models.Model):
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100,default="Sin Apellidos")
    dni= models.CharField(max_length=8, default="00000000")
    telefono = models.CharField(max_length=20)
    email= models.EmailField(default="sin_email@gmail.com")
    direccion = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nombres + " " + self.apellidos


class Estudiante(models.Model):
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    fecha_nacimiento = models.DateField()

    aula = models.ForeignKey(Aula, on_delete=models.CASCADE)
    apoderado = models.ForeignKey(Apoderado, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.nombres} {self.apellidos}"