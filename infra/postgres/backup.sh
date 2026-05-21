#!/usr/bin/env bash
set -euo pipefail

# Environment variables expected:
# PGHOST, PGPORT, PGUSER, PGPASSWORD, PGDATABASE
# BACKUP_DIR (default: ./backups)
# RETENTION_DAYS (default: 14)

BACKUP_DIR=${BACKUP_DIR:-./backups}
RETENTION_DAYS=${RETENTION_DAYS:-14}
TIMESTAMP=$(date -u +"%Y%m%dT%H%M%SZ")
FILENAME="${PGDATABASE:-database}_${TIMESTAMP}.sql.gz"

mkdir -p "${BACKUP_DIR}"

echo "Starting backup for database: ${PGDATABASE:-<unknown>}"
export PGPASSWORD=${PGPASSWORD:-}

pg_dump -h "${PGHOST:-localhost}" -p "${PGPORT:-5432}" -U "${PGUSER:-postgres}" -F c -b -v -f "${BACKUP_DIR}/${FILENAME%.gz}.dump"
gzip -9 "${BACKUP_DIR}/${FILENAME%.gz}.dump"

echo "Backup written to ${BACKUP_DIR}/${FILENAME}"

# cleanup old backups
find "${BACKUP_DIR}" -type f -mtime +${RETENTION_DAYS} -name "*.gz" -print -delete || true

echo "Old backups older than ${RETENTION_DAYS} days removed"
