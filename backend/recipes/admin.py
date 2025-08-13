from django.contrib import admin
from users.models import Follow
from .models import Ingredient, Recipe, RecipeIngredient, Favorite, ShoppingCart


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Админка для ингредиентов: отображение и поиск по названию."""
    list_display = ['id', 'name', 'measurement_unit']
    search_fields = ['name']


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Админка для рецептов с отображением количества добавлений в избранное."""
    list_display = ['id', 'name', 'author', 'favorites_total']
    search_fields = ['name', 'author__username']
    readonly_fields = ['favorites_total']

    def favorites_total(self, obj):
        # Подсчитываем количество добавлений рецепта в избранное
        return obj.favorited_by.count()
    favorites_total.short_description = 'В избранном раз'


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    """Админка для связи рецептов с ингредиентами и количеством."""
    list_display = ['id', 'recipe', 'ingredient', 'amount']
    list_select_related = ['recipe', 'ingredient']


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Админка избранных рецептов с поиском по пользователю и рецепту."""
    list_display = ['user', 'recipe', 'added_at']
    search_fields = ['user__username', 'recipe__name']
    list_select_related = ['user', 'recipe']


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    """Админка корзины пользователя с поиском."""
    list_display = ['user', 'recipe']
    search_fields = ['user__username', 'recipe__name']
    list_select_related = ['user', 'recipe']


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    """Админка для подписок с отображением дат создания."""
    list_display = ['subscriber', 'author', 'created_at']
    search_fields = ['subscriber__username', 'author__username']
    list_select_related = ['subscriber', 'author']
