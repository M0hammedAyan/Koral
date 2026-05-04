# Dockerfile — Frontend (stub)
# Member 4 replaces this with the real implementation
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
