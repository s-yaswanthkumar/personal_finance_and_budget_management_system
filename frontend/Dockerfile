# ==========================================
# Stage 1: Build React/Vite Frontend
# ==========================================
FROM node:20-alpine AS build

WORKDIR /app

# Copy dependency manifests
COPY package*.json ./

# Install npm dependencies
RUN npm ci --silent || npm install --silent

# Copy source code and build production assets
COPY . .
RUN npm run build

# ==========================================
# Stage 2: Production Nginx Web Server
# ==========================================
FROM nginx:alpine

# Remove default nginx static assets
RUN rm -rf /usr/share/nginx/html/*

# Copy built application from build stage
COPY --from=build /app/dist /usr/share/nginx/html

# Copy custom Nginx configuration with API reverse proxy
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose HTTP port
EXPOSE 80

# Healthcheck to verify Nginx is actively serving
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD wget -q -O /dev/null http://127.0.0.1/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
