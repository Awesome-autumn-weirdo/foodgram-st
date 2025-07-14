from django_filters import rest_framework as filters
from recipes.models import Recipe
from users.models import User

class RecipeFilter(filters.FilterSet):
    author = filters.ModelMultipleChoiceFilter(
        field_name='author__id',
        to_field_name='id',
        queryset=User.objects.all()
    )

    is_favorited = filters.BooleanFilter(method='get_favorited')
    is_in_shopping_cart = filters.BooleanFilter(method='get_in_cart')

    class Meta:
        model = Recipe
        fields = ['author', 'is_favorited', 'is_in_shopping_cart']

    def get_favorited(self, queryset, name, value):
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(favorited_by__user=user)
        return queryset

    def get_in_cart(self, queryset, name, value):
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(in_carts__user=user)
        return queryset
