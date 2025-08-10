import base64
import uuid
from django.core.files.base import ContentFile
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from djoser.serializers import UserSerializer as DjoserUserSerializer

from users.models import CustomUser, Follow
from recipes.models import Ingredient, Recipe, RecipeIngredient, ShoppingCart, Favorite


class Base64ImageField(serializers.ImageField):
    SUPPORTED_EXTENSIONS = ('jpg', 'jpeg', 'png')

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            try:
                header, b64 = data.split(';base64,')
                ext = header.split('/')[-1].lower()
                if ext == 'jpeg':
                    ext = 'jpg'
                if ext not in self.SUPPORTED_EXTENSIONS:
                    raise serializers.ValidationError(
                        f"Формат {ext} не поддерживается. Доступны: {', '.join(self.SUPPORTED_EXTENSIONS)}"
                    )
                name = f"{uuid.uuid4().hex[:12]}.{ext}"
                raw = base64.b64decode(b64)
                data = ContentFile(raw, name=name)
            except Exception:
                raise serializers.ValidationError('Неверный формат изображения')
        return super().to_internal_value(data)


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField()

    class Meta:
        model = CustomUser
        fields = ('avatar',)


class UserSerializer(DjoserUserSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(required=False)

    class Meta:
        model = CustomUser
        fields = (
            'id', 'email', 'username',
            'first_name', 'last_name',
            'is_subscribed', 'avatar'
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        return (
            user.is_authenticated
            and Follow.objects.filter(subscriber=user, author=obj).exists()
        )


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
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class IngredientInRecipeWriteSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeGetSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    image = Base64ImageField(required=False, allow_null=True)
    ingredients = IngredientInRecipeReadSerializer(
        many=True, source='ingredient_quantities'
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    text = serializers.CharField(source='description', read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id', 'author', 'ingredients',
            'is_favorited', 'is_in_shopping_cart',
            'name', 'image', 'description', 'text', 'cooking_time'
        )
        read_only_fields = fields

    def get_is_favorited(self, obj):
        user = getattr(self.context.get('request'), 'user', None)
        return user.is_authenticated and user.favorites.filter(recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        user = getattr(self.context.get('request'), 'user', None)
        return user.is_authenticated and user.cart_items.filter(recipe=obj).exists()


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
            'image', 'description', 'text', 'cooking_time'
        )

    def validate(self, attrs):
        ingredients = attrs.get('ingredients', [])
        description = attrs.get('description') or None
        text = attrs.get('text') or None

        if not description and not text:
            raise serializers.ValidationError({
                'description': 'Описание (или text) обязательно'
            })

        if not ingredients:
            raise serializers.ValidationError({
                'ingredients': 'Нужен хотя бы один ингредиент'
            })

        ing_ids = [item['id'] for item in ingredients]
        if len(ing_ids) != len(set(ing_ids)):
            raise serializers.ValidationError({
                'ingredients': 'Ингредиенты не должны повторяться'
            })

        for item in ingredients:
            if int(item.get('amount', 0)) <= 0:
                raise serializers.ValidationError({
                    'amount': 'Количество должно быть больше 0'
                })

        if attrs.get('cooking_time', 0) <= 0:
            raise serializers.ValidationError({
                'cooking_time': 'Время приготовления должно быть больше 0'
            })

        return attrs

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        self._attach_ingredients(recipe, ingredients)
        return recipe

    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients', [])
        instance = super().update(instance, validated_data)
        if ingredients:
            RecipeIngredient.objects.filter(recipe=instance).delete()
            self._attach_ingredients(instance, ingredients)
        return instance

    def _attach_ingredients(self, recipe, ingredients):
        RecipeIngredient.objects.bulk_create([
            RecipeIngredient(
                recipe=recipe,
                ingredient_id=item['id'],
                amount=item['amount']
            ) for item in ingredients
        ])

    def to_representation(self, instance):
        return RecipeGetSerializer(
            instance,
            context={'request': self.context.get('request')}
        ).data


class RecipeFavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class FavoriteAndShoppingCartSerializerBase(serializers.ModelSerializer):
    class Meta:
        fields = ('user', 'recipe')

    def validate(self, data):
        if self.__class__.Meta.model.objects.filter(**data).exists():
            raise serializers.ValidationError('Рецепт уже добавлен')
        return data


class FavoriteSerializer(FavoriteAndShoppingCartSerializerBase):
    class Meta(FavoriteAndShoppingCartSerializerBase.Meta):
        model = Favorite


class ShoppingCartSerializer(FavoriteAndShoppingCartSerializerBase):
    class Meta(FavoriteAndShoppingCartSerializerBase.Meta):
        model = ShoppingCart


class FollowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Follow
        fields = ('subscriber', 'author')
        validators = [
            UniqueTogetherValidator(
                queryset=Follow.objects.all(),
                fields=('subscriber', 'author'),
                message='Вы уже подписаны на этого пользователя'
            )
        ]


class FollowReadSerializer(UserSerializer):
    recipes = RecipeFavoriteSerializer(many=True, read_only=True)
    recipes_count = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ('recipes', 'recipes_count')

    def get_recipes_count(self, obj):
        return obj.recipes.count()
