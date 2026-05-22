from rest_framework import permissions

class IsDirectora(permissions.BasePermission):
    """
    Permite acceso solo a usuarias con el rol de 'directora'.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'directora')


class IsAdministradoraOrDirectora(permissions.BasePermission):
    """
    Permite acceso a usuarias con rol 'administradora' o 'directora'.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            request.user.role in ['administradora', 'directora']
        )


class IsApoderado(permissions.BasePermission):
    """
    Permite acceso solo a usuarios con rol 'apoderado'.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'apoderado')
