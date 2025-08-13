from rest_framework import serializers
from recipes.models import Recipe, RecipeIngredient, ShoppingCart, Favorite
from users.serializers.user import UserSerializer
from users.serializers.base import Base64ImageField
from .ingredient import IngredientInRecipeReadSerializer, IngredientInRecipeWriteSerializer

class RecipeGetSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    ingredients = IngredientInRecipeReadSerializer(many=True, source='ingredient_quantities')
    image = Base64ImageField(required=False, allow_null=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    text = serializers.CharField(source='description', read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id', 'author', 'ingredients',
            'is_favorited', 'is_in_shopping_cart',
            'name', 'image', 'description', 'text', 'cooking_time',
        )
        read_only_fields = fields

    def get_is_favorited(self, obj):
        user = getattr(self.context.get('request'), 'user', None)
        return user.is_authenticated and Favorite.objects.filter(user=user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        user = getattr(self.context.get('request'), 'user', None)
        return user.is_authenticated and ShoppingCart.objects.filter(user=user, recipe=obj).exists()

class RecipeSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    ingredients = IngredientInRecipeWriteSerializer(many=True)
    image = Base64ImageField(required=False, allow_null=True)
    text = serializers.CharField(source='description', required=False)
    description = serializers.CharField(required=False)

    class Meta:
        model = Recipe
        fields = (
            'id', 'author', 'ingredients', 'name',
            'image', 'description', 'text', 'cooking_time',
        )

    def validate(self, data):
        ingredients = data.get('ingredients', [])
        description = data.get('description') or data.get('text')

        if not description:
            raise serializers.ValidationError({'description': 'Нужно указать описание.'})
        if not ingredients:
            raise serializers.ValidationError({'ingredients': 'Нужен хотя бы один ингредиент.'})

        ids = [i['id'] for i in ingredients]
        if len(ids) != len(set(ids)):
            raise serializers.ValidationError({'ingredients': 'Ингредиенты не должны повторяться.'})

        for item in ingredients:
            if item.get('amount', 0) <= 0:
                raise serializers.ValidationError({'amount': 'Количество должно быть > 0.'})

        if data.get('cooking_time', 0) <= 0:
            raise serializers.ValidationError({'cooking_time': 'Время приготовления должно быть больше нуля.'})

        return data

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        self._add_ingredients(recipe, ingredients)
        return recipe

    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients', None)
        recipe = super().update(instance, validated_data)
        if ingredients is not None:
            RecipeIngredient.objects.filter(recipe=recipe).delete()
            self._add_ingredients(recipe, ingredients)
        return recipe

    def _add_ingredients(self, recipe, ingredients):
        RecipeIngredient.objects.bulk_create([
            RecipeIngredient(recipe=recipe, ingredient_id=i['id'], amount=i['amount'])
            for i in ingredients
        ])

    def to_representation(self, instance):
        return RecipeGetSerializer(instance, context=self.context).data
