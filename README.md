# Foodgram
## Описание проекта

Foodgram — веб-приложение для публикации рецептов, подписок на авторов, добавления рецептов в избранное и формирования списка покупок.

Пользователи могут:

публиковать рецепты
подписываться на других авторов
добавлять рецепты в избранное
добавлять рецепты в список покупок
скачивать список покупок с суммированными ингредиентами


Проект развёрнут на сервере и доступен по адресу:

https://foodgramm.servehttp.com

---

## Использованные технологии

* Python
* Django
* Django REST Framework
* Djoser
* PostgreSQL
* Docker
* Docker Compose
* Nginx
* React
* Gunicorn

## Архитектура

Проект состоит из нескольких контейнеров:

* backend — Django REST API
* frontend — React
* db — PostgreSQL
* gateway — Nginx

---

# Установка и запуск проекта

## Клонировать репозиторий

```bash
git clone https://github.com/NastyaGorshtein/foodgram.git
cd foodgram/infra
```

---

## Создать файл переменных окружения

Создайте файл `.env` на примере шиблона:

POSTGRES_DB=foodgram
POSTGRES_USER=foodgram_user
POSTGRES_PASSWORD=your_password

DB_HOST=db
DB_PORT=5432

SECRET_KEY=your_secret_key

DEBUG=False

ALLOWED_HOSTS=yourdomain.com,localhost,127.0.0.1,89.169.191.247

## Запуск проекта через Docker

```bash
docker compose -f docker-compose.production.yml up -d
```

После запуска выполните миграции:

```bash
docker compose exec backend python manage.py migrate
```

Соберите статические файлы:

```bash
docker compose exec backend python manage.py collectstatic --noinput
```

---

# Примеры API запросов

## Получить список рецептов

GET

```
/api/recipes/
```

Ответ:

(указан один рецепт из списка)

```json
[
    ...
        {
            "id": 3,
            "author": {
                "email": "anastasia.gorshtein@yandex.ru",
                "id": 3,
                "username": "Пользователь",
                "first_name": "пользователь",
                "last_name": "Фудграм",
                "is_subscribed": false,
                "avatar": null
            },
            "name": "Каша из топора",
            "image": "http://foodgramm.servehttp.com/media/recipes/images/temp_mGwZotG.jpeg",
            "text": "туда сюда",
            "cooking_time": 10,
            "tags": [
                {
                    "id": 5,
                    "name": "завтрак",
                    "slug": "zavtrak"
                }
            ],
            "ingredients": [
                {
                    "id": 1863,
                    "name": "топинамбур",
                    "measurement_unit": "г",
                    "amount": 1000
                },
                {
                    "id": 1136,
                    "name": "овсяные хлопья быстрого приготовления",
                    "measurement_unit": "г",
                    "amount": 300
                },
                {
                    "id": 977,
                    "name": "масло авокадо",
                    "measurement_unit": "мл",
                    "amount": 100
                },
                {
                    "id": 1685,
                    "name": "соль гималайская",
                    "measurement_unit": "г",
                    "amount": 10
                },
                {
                    "id": 1549,
                    "name": "сахар жемчужный",
                    "measurement_unit": "г",
                    "amount": 20
                }
            ],
            "is_favorited": false,
            "is_in_shopping_cart": false
        },
    ...
]
```

---

## Добавить рецепт

POST

```
/api/recipes/
```

Тело запроса:

```json
{
  "name": "Название рецепта",
  "text": "Описание",
  "ingredients": [
    {
      "id": 1,
      "amount": 100
    }
  ],
  "tags": [1],
  "cooking_time": 10,
  "image": "base64_string"
}
```

# Автор

-   **Анастасия Горштейн** — [GitHub](https://github.com/NastyaGorshtein)
