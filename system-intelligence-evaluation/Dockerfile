FROM python:3.11-slim

WORKDIR /app

COPY simulation/*.py ./

ENV SCENARIO=io_storm

CMD ["sh", "-c", "python ${SCENARIO}.py"]
