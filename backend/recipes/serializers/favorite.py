from rest_framework import serializers
from recipes.models import Favorite, Recipe

class RecipeFavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')

class BaseFavoriteShoppingSerializer(serializers.ModelSerializer):
    """Общий сериализатор для избранного и корзины."""
    class Meta:
        fields = ('user', 'recipe')

    def validate(self, attrs):
        if self.Meta.model.objects.filter(**attrs).exists():
            raise serializers.ValidationError('Этот рецепт уже добавлен.')
        return attrs

class FavoriteSerializer(BaseFavoriteShoppingSerializer):
    class Meta(BaseFavoriteShoppingSerializer.Meta):
        model = Favorite
