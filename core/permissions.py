from rest_framework import permissions

class IsDirectora(permissions.BasePermission):
    """
    Permite acceso solo a usuarias con el rol de 'directora' (Grupo Directora).
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.groups.filter(name='Directora').exists()
        )


class IsAdministradoraOrDirectora(permissions.BasePermission):
    """
    Permite acceso a usuarias con rol 'administradora' o 'directora' (Grupos Administradora o Directora).
    """
    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            request.user.groups.filter(name__in=['Administradora', 'Directora']).exists()
        )


class IsApoderado(permissions.BasePermission):
    """
    Permite acceso solo a usuarios con rol 'apoderado' (Grupo Apoderado).
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.groups.filter(name='Apoderado').exists()
        )
