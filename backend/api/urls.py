from django.urls import path, include
from rest_framework.routers import DefaultRouter

from api.views import (
    CustomUserViewSet,
    IngredientViewSet,
    RecipeViewSet,
    AvatarUpdateView
)

router = DefaultRouter()
router.register(r'users', CustomUserViewSet, basename='users')
router.register(r'ingredients', IngredientViewSet, basename='ingredients')
router.register(r'recipes', RecipeViewSet, basename='recipes')

urlpatterns = [
    path('', include(router.urls)),
    path('users/me/avatar/', AvatarUpdateView.as_view()),
    path('auth/', include('djoser.urls.authtoken')),
    path('', include('djoser.urls')),
]
