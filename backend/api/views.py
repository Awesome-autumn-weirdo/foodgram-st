from django.db.models import Sum, F
from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse

from rest_framework import viewsets, status, permissions, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from djoser.views import UserViewSet

from recipes.models import (
    Tag, Ingredient, Recipe, ShoppingCart, Favorite, Subscription
)
from users.models import User

from api.serializers import (
    TagSerializer, UserSerializer, IngredientSerializer,
    RecipeSerializer, RecipeGetSerializer,
    RecipeFavoriteSerializer, FavoriteSerializer,
    ShoppingCartSerializer, SubscriptionSerializer,
    SubscriptionReadSerializer, AvatarSerializer
)
from api.permissions import OwnerOrReadOnly
from api.filters import RecipeFilter
from api.utils import create_object, delete_object

from recipes.models import IngredientRecipe


class AvatarUpdateView(generics.UpdateAPIView):
    serializer_class = AvatarSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None
    permission_classes = [permissions.AllowAny]


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = IngredientSerializer
    pagination_class = None
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = Ingredient.objects.all()
        name = self.request.query_params.get('name')
        if name:
            queryset = queryset.filter(name__istartswith=name)
        return queryset


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = [OwnerOrReadOnly, permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter
    pagination_class = PageNumberPagination

    def get_serializer_class(self):
        if self.request.method in permissions.SAFE_METHODS:
            return RecipeGetSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['post', 'delete'])
    def favorite(self, request, pk=None):
        if request.method == 'POST':
            data = create_object(
                request, pk,
                FavoriteSerializer,
                RecipeFavoriteSerializer,
                Recipe
            )
            return Response(data.data, status=status.HTTP_201_CREATED)
        delete_object(request, pk, Recipe, Favorite)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post', 'delete'])
    def shopping_cart(self, request, pk=None):
        if request.method == 'POST':
            data = create_object(
                request, pk,
                ShoppingCartSerializer,
                RecipeFavoriteSerializer,
                Recipe
            )
            return Response(data.data, status=status.HTTP_201_CREATED)
        delete_object(request, pk, Recipe, ShoppingCart)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def download_shopping_cart(self, request):
        ingredients = (
            IngredientRecipe.objects
            .filter(recipe__in_carts__user=request.user)
            .values(name=F('ingredient__name'), unit=F('ingredient__measurement_unit'))
            .annotate(amount=Sum('amount'))
            .order_by('name')
        )

        lines = ['Список покупок:']
        for item in ingredients:
            lines.append(f"{item['name']} ({item['unit']}) — {item['amount']}")

        response = HttpResponse('\n'.join(lines), content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename="shopping_list.txt"'
        return response

    @action(detail=True, methods=['get'])
    def get_link(self, request, pk=None):
        recipe = self.get_object()
        url = request.build_absolute_uri(f'/recipes/{recipe.pk}')
        return Response({'link': url})


class CustomUserViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    @action(detail=True, methods=['post', 'delete'])
    def subscribe(self, request, id=None):
        if request.method == 'POST':
            data = create_object(
                request, id,
                SubscriptionSerializer,
                SubscriptionReadSerializer,
                User
            )
            return Response(data.data, status=status.HTTP_201_CREATED)
        delete_object(request, id, User, Subscription)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def subscriptions(self, request):
        user = request.user
        authors = User.objects.filter(subscribers__user=user)
        page = self.paginate_queryset(authors)
        serializer = SubscriptionReadSerializer(page, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)
