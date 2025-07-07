from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import AvatarUpdateView
from api.views import CustomUserViewSet, TagViewSet, IngredientViewSet, RecipeViewSet

app_name = 'api'

router = DefaultRouter()
router.register('users', CustomUserViewSet, basename='users')
router.register('tags', TagViewSet, basename='tag')
router.register('ingredients', IngredientViewSet, basename='ingredient')
router.register('recipes', RecipeViewSet, basename='recipe')

urlpatterns = [
    path('', include(router.urls)),
    path('', include('djoser.urls')),
    path('users/me/avatar/', AvatarUpdateView.as_view(), name='user-avatar'),
    path('auth/', include('djoser.urls.authtoken')),
]
