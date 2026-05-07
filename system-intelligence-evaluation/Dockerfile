FROM python:3.11-slim

WORKDIR /app

COPY simulation/*.py ./

ENV SCENARIO=io_storm

CMD python ${SCENARIO}.py
