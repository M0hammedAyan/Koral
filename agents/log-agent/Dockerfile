FROM python:3.11-slim
WORKDIR /app
COPY log-agent/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY base_agent.py .
COPY log-agent/main.py .
EXPOSE 8004
CMD ["python", "main.py"]
