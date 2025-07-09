# Etapa de build con Node.js 22.17.0
FROM node:22.17.0-alpine AS build
WORKDIR /app
COPY . .
RUN npm install
RUN npm run build

# Etapa de producción con NGINX
FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
EXPOSE 80
