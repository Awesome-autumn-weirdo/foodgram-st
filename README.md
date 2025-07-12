# 🍲 Foodgram — Продуктовый помощник

**Foodgram** — это онлайн-сервис, который позволяет пользователям:

* публиковать рецепты,
* добавлять их в избранное,
* формировать список покупок,
* подписываться на других авторов рецептов.


## 🚀 Технологии

* Python 3.9+
* Django 3.2
* Django REST Framework
* PostgreSQL
* Docker, Docker Compose
* Gunicorn + Nginx
* JWT (djoser)
* drf-spectacular (OpenAPI-документация)


## ⚙️ Быстрый старт для локальной разработки

### 1. Клонирование репозитория

```bash
git clone https://github.com/Awesome-autumn-weirdo/foodgram-st.git
cd foodgram-st
```

---

### 2. Пример `.env` файла

Создай файл `.env` в папке `infra/` со следующим содержимым:

```env
DB_NAME=db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=db_password
DB_HOST=db
DB_PORT=5432
```


### 3. Запуск проекта в Docker

```bash
docker-compose up --build
```


### 4. Выполнение миграций

```bash
docker-compose exec backend python manage.py migrate
```


### 5. Создание суперпользователя

```bash
docker-compose exec backend python manage.py createsuperuser
```


### 6. Сбор статики

```bash
docker-compose exec backend python manage.py collectstatic --noinput
```


### 7. Доступ к приложению

* 🌐 Приложение: [http://localhost/](http://localhost/)
* 📄 Документация OpenAPI: [http://localhost/api/docs/](http://localhost/api/docs/)
* 🔐 Админка: [http://localhost/admin/](http://localhost/admin/)
