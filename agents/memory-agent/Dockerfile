FROM python:3.11-slim
WORKDIR /app
COPY memory-agent/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY base_agent.py .
COPY memory-agent/main.py .
EXPOSE 8002
CMD ["python", "main.py"]
