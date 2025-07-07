FROM python:3.9-bullseye

WORKDIR /app

# Устанавливаем зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && pip install --upgrade pip

# Копируем зависимости проекта
COPY requirements.txt .

RUN pip install -r requirements.txt

# Копируем весь проект
COPY . .

# Копируем и даём права на запуск entrypoint.sh
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Убедись, что wait_for_postgres.py уже есть в проекте (в .)
# Или скопируй явно, как ты делал:
COPY wait_for_postgres.py /app/wait_for_postgres.py

ENTRYPOINT ["/entrypoint.sh"]
CMD []
