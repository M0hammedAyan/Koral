FROM python:3.11-slim
WORKDIR /app
COPY cpu-agent/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY base_agent.py .
COPY cpu-agent/main.py .
EXPOSE 8001
CMD ["python", "main.py"]
