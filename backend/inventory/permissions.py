from rest_framework import permissions


class IsManagerOrReadOnly(permissions.BasePermission):
    message = "Only managers or admins can modify catalog data."

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        return (
            request.user.is_superuser
            or request.user.groups.filter(name="Manager").exists()
        )