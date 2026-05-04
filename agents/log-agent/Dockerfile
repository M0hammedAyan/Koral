# Dockerfile — Log Agent (stub)
# Member 3 replaces this with the real implementation
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt* ./
RUN pip install --no-cache-dir -r requirements.txt 2>/dev/null || true
COPY . .
EXPOSE 8004
CMD ["python", "main.py"]
