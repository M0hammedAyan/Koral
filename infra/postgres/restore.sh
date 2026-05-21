#!/usr/bin/env bash
set -euo pipefail

# Usage: restore.sh <backup-file>
if [ "$#" -ne 1 ]; then
  echo "Usage: $0 <backup-file.gz>" >&2
  exit 2
fi

BACKUP_FILE="$1"
if [[ "${BACKUP_FILE}" != *.gz ]]; then
  echo "Expected a .gz backup file" >&2
  exit 2
fi

TMPDIR=$(mktemp -d)
trap 'rm -rf "${TMPDIR}"' EXIT

echo "Restoring from ${BACKUP_FILE}"
gunzip -c "${BACKUP_FILE}" > "${TMPDIR}/restore.dump"

export PGPASSWORD=${PGPASSWORD:-}
pg_restore -h "${PGHOST:-localhost}" -p "${PGPORT:-5432}" -U "${PGUSER:-postgres}" -d "${PGDATABASE:-postgres}" -v "${TMPDIR}/restore.dump"

echo "Restore completed"
