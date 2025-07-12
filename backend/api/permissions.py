from rest_framework import permissions


class OwnerOrReadOnly(permissions.BasePermission):
    # Разрешение: можно читать всем, а менять только если пользователь автор

    def has_permission(self, request, view):
        # Разрешаем если метод безопасный (GET и т.д.) или если пользователь вошёл
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.user.is_authenticated:
            return True
        return False

    def has_object_permission(self, request, view, obj):
        # Тут тоже — если просто смотрим, то можно всем
        if request.method in permissions.SAFE_METHODS:
            return True
        # Если пользователь тот же, кто автор, то можно редактировать
        if obj.author == request.user:
            return True
        return False
