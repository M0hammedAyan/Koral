FROM python:3.11-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       postgresql-client \
       pgbackrest \
       ca-certificates \
       curl \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --uid 10001 --create-home backup
USER 10001
WORKDIR /home/backup

ENTRYPOINT ["/bin/sh", "-c"]
CMD ["pgbackrest version"]
