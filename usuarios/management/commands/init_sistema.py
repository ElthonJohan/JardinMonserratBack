from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from usuarios.models import Usuario

class Command(BaseCommand):
    help = 'Inicializa los roles (Grupos) y permisos por defecto del sistema'

    def handle(self, *args, **kwargs):
        self.stdout.write('Iniciando carga de roles y permisos...')

        # Crear o obtener grupos
        directora_group, _ = Group.objects.get_or_create(name='Directora')
        admin_group, _ = Group.objects.get_or_create(name='Administradora')
        apoderado_group, _ = Group.objects.get_or_create(name='Apoderado')

        # 1. Directora: Todos los permisos (excluyendo internos de django)
        excluded_apps = ['admin', 'auth', 'contenttypes', 'sessions']
        all_permissions = Permission.objects.exclude(content_type__app_label__in=excluded_apps)
        directora_group.permissions.set(all_permissions)
        
        # 2. Administradora: CRUD Pagos
        pagos_permissions = Permission.objects.filter(content_type__app_label='pagos')
        admin_group.permissions.set(pagos_permissions)
        
        # 3. Apoderado: view_pago, view_deuda
        apoderado_perms = Permission.objects.filter(
            content_type__app_label='pagos',
            codename__in=['view_pago', 'view_deuda']
        )
        apoderado_group.permissions.set(apoderado_perms)

        # Crear usuario master
        if not Usuario.objects.filter(username='master').exists():
            master_user = Usuario.objects.create_user(
                username='master',
                password='password123',
                is_staff=True,
                is_superuser=True
            )
            master_user.groups.add(directora_group)
            self.stdout.write(self.style.SUCCESS('Usuario master creado (admin@monserrat.com / password123)'))
        else:
            self.stdout.write(self.style.WARNING('Usuario master ya existía'))

        self.stdout.write(self.style.SUCCESS('Roles y permisos inicializados correctamente.'))
