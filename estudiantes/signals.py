from django.db.models.signals import post_save
from django.dispatch import receiver
import random
import string

from .models import ApoderadoEstudiante
from usuarios.models import Usuario


