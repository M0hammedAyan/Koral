FROM python:3.11-slim
WORKDIR /app
COPY simulation/ ./simulation/
ENV SCENARIO=cpu_spike
CMD ["sh", "-c", "python simulation/${SCENARIO}.py"]
