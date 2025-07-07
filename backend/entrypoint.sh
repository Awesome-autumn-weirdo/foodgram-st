#!/bin/sh

if [ "$DATABASE" = "postgres" ]; then
    echo "📌 Ждём PostgreSQL..."
    while ! nc -z $DB_HOST $DB_PORT; do
        sleep 0.1
    done
    echo "✅ PostgreSQL запущена"
fi

echo "🧹 Очистка статики..."
rm -rf /app/static/*

echo "🔄 Применение миграций..."
python manage.py migrate --noinput

echo "📁 Сбор статики..."
python manage.py collectstatic --noinput --verbosity 2

exec "$@"
