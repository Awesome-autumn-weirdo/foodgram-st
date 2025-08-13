from rest_framework import permissions


class OwnerOrReadOnly(permissions.BasePermission):
    """Разрешение: только создатель объекта может его изменять."""

    def has_permission(self, request, view):
        # Разрешаем безопасные методы всем, остальные — только аутентифицированным
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Для чтения разрешаем всем, для изменений — только автору
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author == request.user
