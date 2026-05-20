FROM python:3.11-slim

WORKDIR /app

# Install kubectl
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
RUN curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" && \
    chmod +x kubectl && mv kubectl /usr/local/bin/

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY main.py .
COPY executor.py .
COPY validator.py .
COPY allowed_commands.yaml .
COPY dry_run.py .
COPY verifier.py .
COPY telegram_notify.py .

# Health check
HEALTHCHECK --interval=10s --timeout=5s --retries=5 \
    CMD python -c "import httpx; httpx.get('http://localhost:8009/health', timeout=5)" || exit 1

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8009", "--workers", "2"]
