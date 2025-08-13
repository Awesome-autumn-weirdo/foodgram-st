import json
from pathlib import Path
from django.core.management.base import BaseCommand
from django.core.files import File
from django.contrib.auth.hashers import make_password
from users.models import CustomUser, Follow
from recipes.models import Ingredient, Recipe, RecipeIngredient, Favorite, ShoppingCart


class Command(BaseCommand):
    help = 'Загружает тестовые данные из data/test_data.json, используя существующие ингредиенты.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('⚠️  Удаление старых данных...'))

        # Очистка таблиц в правильном порядке (чтобы избежать ошибок с FK)
        models_to_clear = [
            Follow, Favorite, ShoppingCart,
            RecipeIngredient, Recipe,
            CustomUser
        ]
        for model in models_to_clear:
            count_deleted, _ = model.objects.all().delete()
            self.stdout.write(self.style.SUCCESS(f'🗑️ {model.__name__}: удалено {count_deleted} записей'))

        media_root = Path('media')  # Путь к папке media

        try:
            with open('data/test_data.json', encoding='utf-8') as file:
                data = json.load(file)

            users_map = {}
            recipes_map = {}
            ingredients_map = {ing.id: ing for ing in Ingredient.objects.all()}

            # === 1. Пользователи ===
            for item in data:
                if item['model'] == 'users.customuser':
                    fields = item['fields']
                    raw_password = fields.get('password', '12345')
                    user = CustomUser.objects.create(
                        pk=item['pk'],
                        email=fields['email'],
                        username=fields['username'],
                        first_name=fields.get('first_name', ''),
                        last_name=fields.get('last_name', ''),
                        avatar=fields.get('avatar', 'recipes/images/default.jpg'),
                        is_staff=fields.get('is_staff', False),
                        is_superuser=fields.get('is_superuser', False),
                        is_active=fields.get('is_active', True),
                        password=make_password(raw_password)
                    )
                    users_map[item['pk']] = user
            self.stdout.write(self.style.SUCCESS(f'✅ Загружено {len(users_map)} пользователей'))

            # === 2. Подписки ===
            for item in data:
                if item['model'] == 'users.follow':
                    fields = item['fields']
                    Follow.objects.create(
                        pk=item['pk'],
                        subscriber=users_map[fields['subscriber']],
                        author=users_map[fields['author']],
                        created_at=fields['created_at']
                    )
            self.stdout.write(self.style.SUCCESS('✅ Подписки загружены'))

            # === 3. Рецепты ===
            for item in data:
                if item['model'] == 'recipes.recipe':
                    fields = item['fields']
                    recipe = Recipe(
                        name=fields['name'],
                        description=fields['description'],
                        author=users_map[fields['author']],
                        cooking_time=fields['cooking_time'],
                        pub_date=fields['pub_date']
                    )

                    # Загрузка изображения
                    image_file_path = media_root / fields.get('image', 'recipes/images/default.jpg')
                    if image_file_path.exists():
                        with open(image_file_path, 'rb') as f:
                            recipe.image.save(image_file_path.name, File(f), save=False)
                    else:
                        recipe.image = 'recipes/images/default.jpg'

                    recipe.save()
                    recipes_map[item['pk']] = recipe
            self.stdout.write(self.style.SUCCESS(f'✅ Загружено {len(recipes_map)} рецептов'))

            # === 4. Состав рецептов ===
            for item in data:
                if item['model'] == 'recipes.recipeingredient':
                    fields = item['fields']
                    recipe = recipes_map[fields['recipe']]
                    ingredient_name = next(
                        ing['fields']['name'] for ing in data
                        if ing['model'] == 'recipes.ingredient' and ing['pk'] == fields['ingredient']
                    )
                    try:
                        ingredient = Ingredient.objects.get(name=ingredient_name)
                    except Ingredient.DoesNotExist:
                        self.stderr.write(self.style.ERROR(f'❌ Ингредиент "{ingredient_name}" не найден'))
                        continue

                    RecipeIngredient.objects.create(
                        recipe=recipe,
                        ingredient=ingredient,
                        amount=fields['amount']
                    )
            self.stdout.write(self.style.SUCCESS('✅ Состав рецептов загружен'))

            # === 5. Избранное ===
            for item in data:
                if item['model'] == 'recipes.favorite':
                    fields = item['fields']
                    Favorite.objects.create(
                        user=users_map[fields['user']],
                        recipe=recipes_map[fields['recipe']],
                        added_at=fields.get('added_at')
                    )
            self.stdout.write(self.style.SUCCESS('✅ Избранное загружено'))

            # === 6. Корзина ===
            for item in data:
                if item['model'] == 'recipes.shoppingcart':
                    fields = item['fields']
                    ShoppingCart.objects.create(
                        user=users_map[fields['user']],
                        recipe=recipes_map[fields['recipe']]
                    )
            self.stdout.write(self.style.SUCCESS('✅ Корзина загружена'))

        except Exception as error:
            self.stderr.write(self.style.ERROR(f'❌ Ошибка: {error}'))
