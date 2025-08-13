from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from users.models import Follow
from recipes.models import Recipe
from .user import UserSerializer

class FollowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Follow
        fields = ('subscriber', 'author')
        validators = [
            UniqueTogetherValidator(
                queryset=Follow.objects.all(),
                fields=('subscriber', 'author'),
                message='Подписка уже существует.'
            )
        ]

class FollowReadSerializer(UserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ('recipes', 'recipes_count')

    def get_recipes(self, obj):
        from recipes.serializers.favorite import RecipeFavoriteSerializer
        return RecipeFavoriteSerializer(obj.recipes.all(), many=True).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()
