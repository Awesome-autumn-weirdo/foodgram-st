import json

# Загрузим исходный файл с данными
with open('ingredients.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

fixture = []
pk = 1
for item in data:
    fixture.append({
        "model": "recipes.ingredient",
        "pk": pk,
        "fields": item
    })
    pk += 1

# Сохраним фикстуру в файл
with open('ingredients_fixture.json', 'w', encoding='utf-8') as f:
    json.dump(fixture, f, ensure_ascii=False, indent=2)
