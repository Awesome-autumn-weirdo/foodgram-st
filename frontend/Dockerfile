# Сборка фронтенда
FROM node:21.7.1-alpine AS build

WORKDIR /app

COPY package*.json ./
RUN npm install --legacy-peer-deps

COPY . ./
RUN npm run build

# Второй этап — простой образ на nginx для отдачи статических файлов
FROM nginx:alpine

# Копируем собранные файлы из build-этапа в папку nginx для отдачи
COPY --from=build /app/build /usr/share/nginx/html

# Копируем твой конфиг nginx (если нужен свой конфиг для фронтенда, иначе можно использовать дефолтный)
# COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
