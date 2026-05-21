# Multi-stage Dockerfile for KORAL Frontend
# Production-grade with security hardening

# Stage 1: Build
FROM node:18-alpine AS build

WORKDIR /app

# Copy package files
COPY package.json package-lock.json ./

# Install dependencies needed for the build stage
RUN npm install --include=dev && \
    npm cache clean --force

# Copy source code
COPY . .

# Build application
RUN npm run build

# Stage 2: Runtime
FROM nginx:alpine

# Security: Install packages required for health checks
RUN apk add --no-cache curl

# Create non-root user for nginx
RUN addgroup -g 101 nginx && adduser -D -u 101 -G nginx nginx || true

# Copy built application from builder
COPY --from=build --chown=nginx:nginx /app/build /usr/share/nginx/html

# Copy nginx main configuration (before switching user to avoid pid permission issues)
COPY nginx-main.conf /etc/nginx/nginx.conf

# Copy nginx site configuration
COPY --chown=nginx:nginx nginx.conf /etc/nginx/conf.d/default.conf

# Security: Remove default nginx files
RUN rm -f /etc/nginx/conf.d/default.conf.bak

# Create necessary directories with proper permissions
RUN mkdir -p /var/cache/nginx /var/log/nginx /run/nginx && \
    chown -R nginx:nginx /var/cache/nginx /var/log/nginx /etc/nginx /run/nginx

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000/index.html || exit 1

# Switch to non-root user
USER nginx

# Expose port
EXPOSE 3000

# Run nginx
CMD ["nginx", "-g", "daemon off;"]
