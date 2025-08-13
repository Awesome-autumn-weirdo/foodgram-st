import base64
import uuid
from django.core.files.base import ContentFile
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from djoser.serializers import UserSerializer as DjoserUserSerializer

from users.models import CustomUser, Follow
from recipes.models import (
    Ingredient, Recipe, RecipeIngredient,
    ShoppingCart, Favorite
)


class Base64ImageField(serializers.ImageField):
    """Поле для загрузки изображения, поддерживающее base64-строки с проверкой формата."""
    ALLOWED_EXTENSIONS = ('jpg', 'jpeg', 'png')

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            try:
                header, b64data = data.split(';base64,')
                ext = header.split('/')[-1].lower()
                ext = 'jpg' if ext == 'jpeg' else ext
                if ext not in self.ALLOWED_EXTENSIONS:
                    raise serializers.ValidationError(
                        f"Формат '{ext}' не поддерживается. Допустимые: {', '.join(self.ALLOWED_EXTENSIONS)}"
                    )
                file_name = f"{uuid.uuid4().hex[:12]}.{ext}"
                decoded_file = base64.b64decode(b64data)
                data = ContentFile(decoded_file, name=file_name)
            except Exception:
                raise serializers.ValidationError('Некорректный формат изображения')
        return super().to_internal_value(data)


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField()

    class Meta:
        model = CustomUser
        fields = ('avatar',)


class UserSerializer(DjoserUserSerializer):
    avatar = Base64ImageField(required=False)
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = (
            'id', 'email', 'username',
            'first_name', 'last_name',
            'is_subscribed', 'avatar',
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        current_user = getattr(request, 'user', None)
        # Проверяем, подписан ли текущий пользователь на obj
        return (
            current_user.is_authenticated and
            Follow.objects.filter(subscriber=current_user, author=obj).exists()
        )

    def to_representation(self, instance):
        """Переопределяем вывод, чтобы при отсутствии аватара отдавать дефолт."""
        representation = super().to_representation(instance)
        if not representation.get('avatar'):
            # URL до дефолтного аватара
            request = self.context.get('request')
            default_path = 'recipes/images/default.jpg'
            if request:
                representation['avatar'] = request.build_absolute_uri(
                    f'/media/{default_path}'
                )
            else:
                representation['avatar'] = f'/media/{default_path}'
        return representation


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')
        read_only_fields = fields


class IngredientInRecipeReadSerializer(serializers.ModelSerializer):
    # Переадресуем поля для удобного чтения ингредиентов с рецептом
    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(source='ingredient.measurement_unit')

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class IngredientInRecipeWriteSerializer(serializers.ModelSerializer):
    # При записи достаточно id и количества
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
            'name', 'image', 'description', 'text', 'cooking_time',
        )
        read_only_fields = fields

    def get_is_favorited(self, obj):
        user = getattr(self.context.get('request'), 'user', None)
        if not user or not user.is_authenticated:
            return False
        # Проверяем наличие рецепта в избранном пользователя
        return Favorite.objects.filter(user=user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        user = getattr(self.context.get('request'), 'user', None)
        if not user or not user.is_authenticated:
            return False
        # Проверяем наличие рецепта в корзине пользователя
        return ShoppingCart.objects.filter(user=user, recipe=obj).exists()


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
        description = data.get('description') or None
        text = data.get('text') or None

        if not description and not text:
            raise serializers.ValidationError({
                'description': 'Требуется описание (description или text).'
            })

        if not ingredients:
            raise serializers.ValidationError({
                'ingredients': 'Необходимо указать хотя бы один ингредиент.'
            })

        ingredient_ids = [item['id'] for item in ingredients]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError({
                'ingredients': 'Ингредиенты не должны повторяться.'
            })

        for item in ingredients:
            amount = item.get('amount')
            if amount is None or int(amount) <= 0:
                raise serializers.ValidationError({
                    'amount': 'Количество ингредиента должно быть положительным числом.'
                })

        cooking_time = data.get('cooking_time', 0)
        if cooking_time <= 0:
            raise serializers.ValidationError({
                'cooking_time': 'Время приготовления должно быть больше нуля.'
            })

        return data

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        self._add_ingredients(recipe, ingredients)
        return recipe

    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients', None)
        updated_instance = super().update(instance, validated_data)
        if ingredients is not None:
            # Удаляем старые связи ингредиентов
            RecipeIngredient.objects.filter(recipe=updated_instance).delete()
            self._add_ingredients(updated_instance, ingredients)
        return updated_instance

    def _add_ingredients(self, recipe, ingredients):
        # Связываем рецепт с ингредиентами и их количеством
        relations = [
            RecipeIngredient(
                recipe=recipe,
                ingredient_id=item['id'],
                amount=item['amount']
            )
            for item in ingredients
        ]
        RecipeIngredient.objects.bulk_create(relations)

    def to_representation(self, instance):
        # При выводе используем более детальный сериализатор
        serializer = RecipeGetSerializer(instance, context=self.context)
        return serializer.data


class RecipeFavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class BaseFavoriteShoppingSerializer(serializers.ModelSerializer):
    """Базовый сериализатор для Favorite и ShoppingCart с проверкой уникальности."""
    class Meta:
        fields = ('user', 'recipe')

    def validate(self, attrs):
        model = self.Meta.model
        if model.objects.filter(**attrs).exists():
            raise serializers.ValidationError('Этот рецепт уже добавлен')
        return attrs


class FavoriteSerializer(BaseFavoriteShoppingSerializer):
    class Meta(BaseFavoriteShoppingSerializer.Meta):
        model = Favorite


class ShoppingCartSerializer(BaseFavoriteShoppingSerializer):
    class Meta(BaseFavoriteShoppingSerializer.Meta):
        model = ShoppingCart


class FollowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Follow
        fields = ('subscriber', 'author')
        validators = [
            UniqueTogetherValidator(
                queryset=Follow.objects.all(),
                fields=('subscriber', 'author'),
                message='Подписка на данного пользователя уже существует.'
            )
        ]


class FollowReadSerializer(UserSerializer):
    recipes = RecipeFavoriteSerializer(many=True, read_only=True)
    recipes_count = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ('recipes', 'recipes_count')

    def get_recipes_count(self, obj):
        # Считаем количество рецептов автора
        return obj.recipes.count()
