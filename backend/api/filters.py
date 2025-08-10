from django_filters import rest_framework as filters
from recipes.models import Recipe
from users.models import CustomUser


class RecipeFilter(filters.FilterSet):
    author = filters.ModelMultipleChoiceFilter(
        field_name='author__id',
        to_field_name='id',
        queryset=CustomUser.objects.all(),
        label='Автор рецепта'
    )

    is_favorited = filters.BooleanFilter(
        method='filter_favorited',
        label='Отфильтровать по избранному'
    )

    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_in_cart',
        label='Отфильтровать по корзине'
    )

    class Meta:
        model = Recipe
        fields = ['author', 'is_favorited', 'is_in_shopping_cart']

    def filter_favorited(self, queryset, name, value):
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(favorited_by__user=user)
        return queryset

    def filter_in_cart(self, queryset, name, value):
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(in_carts__user=user)
        return queryset
