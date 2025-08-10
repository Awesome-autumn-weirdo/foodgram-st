from django.db.models import Sum, F
from django.http import HttpResponse
from rest_framework import viewsets, permissions, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet

from recipes.models import Ingredient, Recipe, ShoppingCart, Favorite, RecipeIngredient
from users.models import CustomUser, Follow
from api.serializers import (
    UserSerializer, IngredientSerializer, RecipeSerializer,
    RecipeGetSerializer, RecipeFavoriteSerializer,
    FavoriteSerializer, ShoppingCartSerializer,
    FollowSerializer, FollowReadSerializer,
    AvatarSerializer
)
from api.permissions import OwnerOrReadOnly
from api.filters import RecipeFilter


class AvatarUpdateView(generics.UpdateAPIView):
    """Обновление аватара пользователя."""
    serializer_class = AvatarSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Список ингредиентов с фильтрацией по началу названия."""
    serializer_class = IngredientSerializer
    permission_classes = (permissions.AllowAny,)
    pagination_class = None

    def get_queryset(self):
        name_query = (self.request.query_params.get("name") or "").strip()
        qs = Ingredient.objects.all()
        if name_query:
            qs = qs.filter(name__istartswith=name_query)
        return qs


class RecipeViewSet(viewsets.ModelViewSet):
    """CRUD для рецептов с фильтрацией и доп. действиями."""
    queryset = Recipe.objects.all()
    permission_classes = (OwnerOrReadOnly, permissions.IsAuthenticatedOrReadOnly)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    pagination_class = PageNumberPagination

    def get_serializer_class(self):
        if self.request.method in permissions.SAFE_METHODS:
            return RecipeGetSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def _handle_add_remove(self, request, pk, rel_model, rel_serializer, return_serializer):
        """Универсальный метод для POST/DELETE связок."""
        recipe = Recipe.objects.filter(pk=pk).first()
        if not recipe:
            return Response({"detail": "Рецепт не найден"}, status=status.HTTP_404_NOT_FOUND)

        if request.method.lower() == "post":
            if rel_model.objects.filter(user=request.user, recipe=recipe).exists():
                return Response({"detail": "Рецепт уже добавлен"}, status=status.HTTP_400_BAD_REQUEST)
            rel_model.objects.create(user=request.user, recipe=recipe)
            return Response(return_serializer(recipe, context={"request": request}).data, status=status.HTTP_201_CREATED)

        deleted, _ = rel_model.objects.filter(user=request.user, recipe=recipe).delete()
        if not deleted:
            return Response({"detail": "Рецепт отсутствует"}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=("post", "delete"))
    def favorite(self, request, pk=None):
        return self._handle_add_remove(request, pk, Favorite, FavoriteSerializer, RecipeFavoriteSerializer)

    @action(detail=True, methods=("post", "delete"))
    def shopping_cart(self, request, pk=None):
        return self._handle_add_remove(request, pk, ShoppingCart, ShoppingCartSerializer, RecipeFavoriteSerializer)

    @action(detail=False, methods=("get",), permission_classes=(permissions.IsAuthenticated,))
    def download_shopping_cart(self, request):
        """Формирует и скачивает список покупок для пользователя."""
        # Получаем все рецепты в корзине пользователя
        cart_recipes = request.user.cart_items.values_list('recipe_id', flat=True)

        # Получаем ингредиенты из этих рецептов с суммированием количества
        ingredients = (
            RecipeIngredient.objects
            .filter(recipe_id__in=cart_recipes)
            .values(
                'ingredient__name',
                'ingredient__measurement_unit'
            )
            .annotate(total_amount=Sum('amount'))
            .order_by('ingredient__name')
        )

        # Формируем текстовый файл
        text = "Список покупок:\n\n"
        for item in ingredients:
            text += (
                f"{item['ingredient__name']} "
                f"({item['ingredient__measurement_unit']}) - "
                f"{item['total_amount']}\n"
            )

        response = HttpResponse(text, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename="shopping_list.txt"'
        return response


class CustomUserViewSet(UserViewSet):
    """Расширенный UserViewSet с подписками."""
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer

    def _handle_subscribe(self, request, author_id):
        author = CustomUser.objects.filter(pk=author_id).first()
        if not author:
            return Response({"detail": "Пользователь не найден"}, status=status.HTTP_404_NOT_FOUND)

        if request.method.lower() == "post":
            if Follow.objects.filter(subscriber=request.user, author=author).exists():
                return Response({"detail": "Уже подписаны"}, status=status.HTTP_400_BAD_REQUEST)
            if request.user == author:
                return Response({"detail": "Нельзя подписаться на себя"}, status=status.HTTP_400_BAD_REQUEST)
            Follow.objects.create(subscriber=request.user, author=author)
            return Response(FollowReadSerializer(author, context={"request": request}).data, status=status.HTTP_201_CREATED)

        deleted, _ = Follow.objects.filter(subscriber=request.user, author=author).delete()
        if not deleted:
            return Response({"detail": "Подписка отсутствует"}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=("post", "delete"))
    def subscribe(self, request, id=None):
        return self._handle_subscribe(request, id)

    @action(detail=False, methods=("get",), permission_classes=(permissions.IsAuthenticated,))
    def subscriptions(self, request):
        authors = CustomUser.objects.filter(subscribers__subscriber=request.user)
        page = self.paginate_queryset(authors)

        # Получаем параметр recipes_limit из запроса
        recipes_limit = request.query_params.get('recipes_limit')

        serializer = FollowReadSerializer(
            page,
            many=True,
            context={
                "request": request,
                "recipes_limit": recipes_limit
            }
        )
        return self.get_paginated_response(serializer.data)
