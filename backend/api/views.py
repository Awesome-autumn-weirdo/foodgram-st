from django.db.models import Sum
from django.http import HttpResponse
from rest_framework import viewsets, permissions, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet

from recipes.models import Ingredient, Recipe, ShoppingCart, Favorite, RecipeIngredient
from users.models import CustomUser, Follow
from users.serializers import (
    UserSerializer,
    AvatarSerializer,
    FollowSerializer,
    FollowReadSerializer,
)
from recipes.serializers import (
    IngredientSerializer,
    RecipeSerializer,
    RecipeGetSerializer,
    RecipeFavoriteSerializer,
    FavoriteSerializer,
    ShoppingCartSerializer,
)

from api.permissions import OwnerOrReadOnly
from api.filters import RecipeFilter


class AvatarUpdateView(generics.UpdateAPIView):
    """Обновление аватара текущего пользователя."""
    serializer_class = AvatarSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Отдаёт список ингредиентов с опциональным поиском по началу названия."""
    serializer_class = IngredientSerializer
    permission_classes = (permissions.AllowAny,)
    pagination_class = None  # Отключаем пагинацию

    def get_queryset(self):
        query = self.request.query_params.get("name", "").strip()
        qs = Ingredient.objects.all()
        if query:
            qs = qs.filter(name__istartswith=query)
        return qs


class RecipeViewSet(viewsets.ModelViewSet):
    """CRUD для рецептов с фильтрацией и дополнительными действиями."""
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

    def _modify_relation(self, request, pk, model, response_serializer, return_serializer):
        """Универсальный метод добавления/удаления рецепта из связанной модели."""
        recipe = Recipe.objects.filter(pk=pk).first()
        if not recipe:
            return Response({"detail": "Рецепт не найден"}, status=status.HTTP_404_NOT_FOUND)

        if request.method == "POST":
            if model.objects.filter(user=request.user, recipe=recipe).exists():
                return Response({"detail": "Рецепт уже добавлен"}, status=status.HTTP_400_BAD_REQUEST)
            model.objects.create(user=request.user, recipe=recipe)
            data = return_serializer(recipe, context={"request": request}).data
            return Response(data, status=status.HTTP_201_CREATED)

        deleted, _ = model.objects.filter(user=request.user, recipe=recipe).delete()
        if not deleted:
            return Response({"detail": "Рецепт отсутствует"}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post", "delete"])
    def favorite(self, request, pk=None):
        return self._modify_relation(request, pk, Favorite, FavoriteSerializer, RecipeFavoriteSerializer)

    @action(detail=True, methods=["post", "delete"])
    def shopping_cart(self, request, pk=None):
        return self._modify_relation(request, pk, ShoppingCart, ShoppingCartSerializer, RecipeFavoriteSerializer)

    @action(detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated])
    def download_shopping_cart(self, request):
        """Генерирует и отдаёт список ингредиентов из корзины с суммарными количествами."""
        recipe_ids = request.user.cart_items.values_list('recipe_id', flat=True)
        ingredients = (
            RecipeIngredient.objects.filter(recipe_id__in=recipe_ids)
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(total_amount=Sum('amount'))
            .order_by('ingredient__name')
        )

        lines = [
            f"{item['ingredient__name']} ({item['ingredient__measurement_unit']}) - {item['total_amount']}"
            for item in ingredients
        ]
        content = "Список покупок:\n\n" + "\n".join(lines)
        response = HttpResponse(content, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename="shopping_list.txt"'
        return response


class CustomUserViewSet(UserViewSet):
    """Пользовательский ViewSet с поддержкой подписок."""
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer

    def _handle_subscription(self, request, author_id):
        author = CustomUser.objects.filter(pk=author_id).first()
        if not author:
            return Response({"detail": "Пользователь не найден"}, status=status.HTTP_404_NOT_FOUND)

        if request.method == "POST":
            if request.user == author:
                return Response({"detail": "Нельзя подписаться на себя"}, status=status.HTTP_400_BAD_REQUEST)
            if Follow.objects.filter(subscriber=request.user, author=author).exists():
                return Response({"detail": "Уже подписаны"}, status=status.HTTP_400_BAD_REQUEST)
            Follow.objects.create(subscriber=request.user, author=author)
            data = FollowReadSerializer(author, context={"request": request}).data
            return Response(data, status=status.HTTP_201_CREATED)

        deleted, _ = Follow.objects.filter(subscriber=request.user, author=author).delete()
        if not deleted:
            return Response({"detail": "Подписка отсутствует"}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post", "delete"])
    def subscribe(self, request, id=None):
        return self._handle_subscription(request, id)

    @action(detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated])
    def subscriptions(self, request):
        authors = CustomUser.objects.filter(subscribers__subscriber=request.user)
        page = self.paginate_queryset(authors)

        recipes_limit = request.query_params.get('recipes_limit')
        serializer = FollowReadSerializer(
            page,
            many=True,
            context={"request": request, "recipes_limit": recipes_limit}
        )
        return self.get_paginated_response(serializer.data)
