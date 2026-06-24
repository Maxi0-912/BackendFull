from rest_framework.permissions import BasePermission

class EsCliente(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            hasattr(request.user, 'rol') and
            request.user.rol is not None and
            request.user.rol.nombre.lower() == 'cliente'
        )

class EsEmpresa(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            hasattr(request.user, 'rol') and
            request.user.rol is not None and
            request.user.rol.nombre.lower() == 'empresa'
        )

class EsAdmin(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            hasattr(request.user, 'rol') and
            request.user.rol is not None and
            request.user.rol.nombre.lower() == 'admin'
        )