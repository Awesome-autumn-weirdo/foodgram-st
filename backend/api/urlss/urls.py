from django.urls import path, include
from .urls_users import urlpatterns as user_urls, router_users
from .urls_recipes import router_recipes
from .urls_auth import urlpatterns as auth_urls

app_name = "api"

urlpatterns = [
    # Роутеры
    path('', include(router_users.urls)),
    path('', include(router_recipes.urls)),

    # Пути, специфичные для пользователей
    *user_urls,

    # Подключение авторизации
    *auth_urls,
]
