from rest_framework.routers import DefaultRouter
from api.views import IngredientViewSet, RecipeViewSet

router_recipes = DefaultRouter()
router_recipes.register(r"ingredients", IngredientViewSet, basename="ingredients")
router_recipes.register(r"recipes", RecipeViewSet, basename="recipes")

# Просто отдаём список маршрутов
recipe_router_urls = router_recipes.urls
