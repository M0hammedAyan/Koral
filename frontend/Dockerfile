# Dockerfile — Frontend (stub)
# Member 4 replaces this with the real implementation
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install 2>/dev/null || true
COPY . .
RUN npm run build 2>/dev/null || true
EXPOSE 3000
CMD ["npm", "start"]
