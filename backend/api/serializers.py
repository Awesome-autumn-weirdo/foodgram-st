import base64
import uuid

from django.core.files.base import ContentFile
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from djoser.serializers import UserSerializer as DjoserUserSerializer

from users.models import (User, Subscription)

from recipes.models import (
    Ingredient,
    Recipe,
    IngredientRecipe,
    ShoppingCart,
    Favorite
)


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            try:
                format, img_str = data.split(';base64,')
                ext = format.split('/')[-1]
                if ext == 'jpeg':
                    ext = 'jpg'
                name = f'{uuid.uuid4().hex[:10]}.{ext}'
                data = ContentFile(base64.b64decode(img_str), name=name)
            except Exception:
                raise serializers.ValidationError('Неправильный формат картинки')
        return super().to_internal_value(data)


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('avatar',)


class UserSerializer(DjoserUserSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(required=False)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'username',
            'first_name', 'last_name',
            'is_subscribed', 'avatar'
        ]

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            return Subscription.objects.filter(user=user, author=obj).exists()
        return False


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')
        read_only_fields = fields


class IngredientInRecipeReadSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(source='ingredient.measurement_unit')

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class IngredientInRecipeWriteSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'amount')


class RecipeGetSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    image = Base64ImageField(required=False, allow_null=True)
    ingredients = IngredientInRecipeReadSerializer(
        many=True,
        source='ingredient_recipes'
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = [
            'id', 'author', 'ingredients',
            'is_favorited', 'is_in_shopping_cart',
            'name', 'image', 'text', 'cooking_time',
        ]

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            return user.favorites.filter(recipe=obj).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            return user.shopping_cart.filter(recipe=obj).exists()
        return False


class RecipeSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    ingredients = IngredientInRecipeWriteSerializer(many=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = [
            'id', 'author',
            'ingredients', 'name', 'image',
            'text', 'cooking_time'
        ]

    def validate(self, data):
        ingredients = self.initial_data.get('ingredients')
        if not ingredients:
            raise serializers.ValidationError({'ingredients': 'Нужен хотя бы один ингредиент'})

        seen_ids = set()
        for item in ingredients:
            if item['id'] in seen_ids:
                raise serializers.ValidationError('Ингредиенты не должны повторяться')
            seen_ids.add(item['id'])
            if int(item['amount']) <= 0:
                raise serializers.ValidationError('Количество должно быть больше нуля')

        return data

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        self.create_ingredients(recipe, ingredients)
        return recipe

    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients')
        IngredientRecipe.objects.filter(recipe=instance).delete()
        self.create_ingredients(instance, ingredients)
        return super().update(instance, validated_data)

    def create_ingredients(self, recipe, ingredients):
        IngredientRecipe.objects.bulk_create([
            IngredientRecipe(
                recipe=recipe,
                ingredient_id=item['id'],
                amount=item['amount']
            ) for item in ingredients
        ])

    def to_representation(self, instance):
        context = {'request': self.context.get('request')}
        return RecipeGetSerializer(instance, context=context).data


class RecipeFavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class FavoriteAndShoppingCartSerializerBase(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = ('user', 'recipe')

    def validate(self, data):
        if self.Meta.model.objects.filter(**data).exists():
            raise serializers.ValidationError('Этот рецепт уже добавлен')
        return data


class FavoriteSerializer(FavoriteAndShoppingCartSerializerBase):
    class Meta(FavoriteAndShoppingCartSerializerBase.Meta):
        model = Favorite


class ShoppingCartSerializer(FavoriteAndShoppingCartSerializerBase):
    class Meta(FavoriteAndShoppingCartSerializerBase.Meta):
        model = ShoppingCart


class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ('user', 'author')
        validators = [
            UniqueTogetherValidator(
                queryset=Subscription.objects.all(),
                fields=('user', 'author'),
                message='Уже подписаны на этого пользователя'
            )
        ]


class SubscriptionReadSerializer(UserSerializer):
    recipes = RecipeFavoriteSerializer(many=True, read_only=True)
    recipes_count = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ['recipes', 'recipes_count']

    def get_recipes_count(self, obj):
        return obj.recipes.count()