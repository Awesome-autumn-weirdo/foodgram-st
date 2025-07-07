import json
from django.core.management.base import BaseCommand
from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Загружает ингредиенты из ingredients.json. Старые — удаляет.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('⚠️  Удаление старых ингредиентов...'))
        count_deleted, _ = Ingredient.objects.all().delete()

        self.stdout.write(self.style.SUCCESS(f'🗑️ Удалено {count_deleted} ингредиентов'))

        try:
            with open('data/ingredients.json', encoding='utf-8') as file:
                data = json.load(file)

            ingredients = [
                Ingredient(name=item['name'], measurement_unit=item['measurement_unit'])
                for item in data if item.get('name') and item.get('measurement_unit')
            ]

            Ingredient.objects.bulk_create(ingredients)
            self.stdout.write(self.style.SUCCESS(f'✅ Загружено {len(ingredients)} ингредиентов'))

        except Exception as error:
            self.stderr.write(self.style.ERROR(f'❌ Ошибка: {error}'))
