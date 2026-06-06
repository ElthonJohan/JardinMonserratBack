from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.hashers import make_password
import random
import string

from .models import Estudiante
from usuarios.models import Usuario


@receiver(post_save, sender=Estudiante)
def create_parent_user(sender, instance, created, **kwargs):
    """Crea automáticamente un usuario para el apoderado al registrar un estudiante"""
    if not created or not instance.apoderado:
        return

    apoderado = instance.apoderado

    # Evitar crear múltiples usuarios para el mismo apoderado
    if apoderado.usuarios.exists():
        return

    # Generar username único
    base_username = f"apoderado_{apoderado.id}"
    username = base_username
    counter = 1
    while Usuario.objects.filter(username=username).exists():
        username = f"{base_username}_{counter}"
        counter += 1

        # Generar contraseña temporal de 8 caracteres
        temp_password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))

    # Crear el usuario
    usuario = Usuario.objects.create(
        username=username,
        first_name=apoderado.nombres,
        last_name=apoderado.apellidos,
        email=apoderado.email,
        is_parent=True,
        first_login=True,
        apoderado_rel=apoderado,
        is_active=True,
    )

    # Establecer la contraseña
    usuario.set_password(temp_password)
    usuario.save()

    # Mostrar en consola (muy útil durante desarrollo)
    print("\n" + "="*60)
    print("✅ USUARIO DE APODERADO CREADO AUTOMÁTICAMENTE")
    print("="*60)
    print(f"Apoderado     : {apoderado.nombres} {apoderado.apellidos}")
    print(f"Estudiante    : {instance}")
    print(f"Usuario       : {username}")
    print(f"Contraseña    : {temp_password}")
    print(f"ID Usuario    : {usuario.id}")
    print("="*60 + "\n")

    # Guardar credenciales en la instancia para que el serializador pueda acceder a ellas
    instance._generated_credentials = {
        "username": username,
        "password": temp_password,
    }

    # Aquí puedes agregar lógica para enviar por email o WhatsApp más adelante