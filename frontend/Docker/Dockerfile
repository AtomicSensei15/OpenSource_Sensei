# Multi-stage build for the React (Vite) frontend
# Stages:
# 1. deps  - install dependencies with a clean layer cache
# 2. build - build the production assets
# 3. nginx - serve the built static files with Nginx (final image)

# syntax=docker/dockerfile:1.6

############################
# 1. Dependencies layer
############################
FROM node:20-alpine AS deps
WORKDIR /app
COPY user_fe/package.json user_fe/package-lock.json* ./user_fe/
RUN \
  if [ -f user_fe/package-lock.json ]; then cd user_fe && npm ci; \
  else cd user_fe && npm install; fi

############################
# 2. Build stage
############################
FROM node:20-alpine AS build
WORKDIR /app
ENV NODE_ENV=production
COPY --from=deps /app/user_fe/node_modules ./user_fe/node_modules
COPY user_fe ./user_fe
WORKDIR /app/user_fe
# Build with no inline sourcemaps (can be configured)
RUN npm run build

############################
# 3. Nginx stage
############################
FROM nginx:1.27-alpine AS nginx
# Copy custom nginx configuration
COPY Docker/nginx.conf /etc/nginx/conf.d/default.conf
# Copy built assets
COPY --from=build /app/user_fe/dist /usr/share/nginx/html
# Default port
EXPOSE 80
# Healthcheck (optional, documented in compose)
CMD ["nginx", "-g", "daemon off;"]
