from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from users.models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    list_display = (
        'id', 'email', 'username',
        'first_name', 'last_name', 'is_active'
    )
    search_fields = ('username', 'email')  # поиск по имени и email
    ordering = ('id',)