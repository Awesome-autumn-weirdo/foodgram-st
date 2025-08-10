from django.urls import path
from rest_framework.routers import DefaultRouter

from api.views import CustomUserViewSet, AvatarUpdateView

router_users = DefaultRouter()
router_users.register(r"users", CustomUserViewSet, basename="users")

urlpatterns = [
    path("users/me/avatar/", AvatarUpdateView.as_view(), name="user-avatar"),
]

# Экспортируем для подключения в главный urls.py
user_router_urls = router_users.urls
