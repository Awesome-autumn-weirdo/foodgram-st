from django.contrib import admin
from users.models import Follow
from .models import (
    Ingredient, Recipe, RecipeIngredient,
    Favorite, ShoppingCart
)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit')
    search_fields = ('name',)  # поиск по названию


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'author', 'favorites_count')
    search_fields = ('name', 'author__username')  # поиск по названию и автору
    readonly_fields = ('favorites_count',)

    def favorites_count(self, obj):
        return obj.favorites.count()
    favorites_count.short_description = 'Добавлений в избранное'


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipe', 'ingredient', 'amount')


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe', 'added_at')
    search_fields = ('user__username', 'recipe__name')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    search_fields = ('user__username', 'recipe__name')


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('subscriber', 'author', 'created_at')
    search_fields = ('subscriber__username', 'author__username')