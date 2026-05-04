FROM python:3.11-slim
WORKDIR /app
COPY storage-agent/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY base_agent.py .
COPY storage-agent/main.py .
EXPOSE 8003
CMD ["python", "main.py"]
