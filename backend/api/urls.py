from .urls_users import urlpatterns as user_urls, user_router_urls
from .urls_recipes import recipe_router_urls
from .urls_auth import urlpatterns as auth_urls

app_name = "api"

urlpatterns = [
    # Роутеры от пользователей и рецептов
    *user_router_urls,
    *recipe_router_urls,

    # Пути, специфичные для пользователей
    *user_urls,

    # Подключение авторизации
    *auth_urls,
]
