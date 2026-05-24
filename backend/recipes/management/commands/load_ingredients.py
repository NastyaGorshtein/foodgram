import json
from django.core.management.base import BaseCommand
from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Загрузка ингредиентов'

    def handle(self, *args, **kwargs):
        with open('../data/ingredients.json', encoding='utf-8') as file:
            data = json.load(file)

        for item in data:
            Ingredient.objects.get_or_create(
                name=item['name'],
                measurement_unit=item['measurement_unit']
            )

        print('Готово!')