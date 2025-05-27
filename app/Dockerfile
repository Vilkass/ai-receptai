# Stage 1: Build the Angular app
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build -- --configuration production --project app

# Stage 2: Serve the Angular app using Nginx
FROM nginx:stable-alpine

# Copy the Angular build from Stage 1
COPY --from=builder /app/dist/app/browser /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
