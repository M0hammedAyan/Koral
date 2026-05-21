# DATABASE_AUDIT

Summary
- DB_TYPE: postgres
- DB_HOST: localhost
- DB_PORT: 5432
- DB_NAME: Koral
- DB_USER: postgres
- DB_PASS: 

Connection
- Live connectivity: SUCCESS (connected to Postgres at localhost:5432)

What I verified
1. Verified live connection using provided credentials.
2. Queried `information_schema` — no production tables were present initially.
3. No migration framework detected (no `alembic` tables or migrations directory).
4. Created missing tables non-destructively using `CREATE TABLE IF NOT EXISTS` statements matching `backend/database.py` schema:
   - `anomalies`
   - `incidents`
   - `fix_history`
   - `graph_nodes`
   - `graph_edges`
5. Confirmed tables exist after creation and observed primary key and unique indexes created by DDL (primary keys and `incidents_incident_id_key`).
6. Verified row counts: `incidents` = 0, `anomalies` = 0.

Issues Found
- Missing schema / missing tables: the Postgres DB lacked the KORAL schema/tables prior to initialization.
- No migration tooling: repository contains no Alembic/migration artifacts; schema is created by `init_db()` at runtime.
- Local dependency gap: importing `init_db()` failed in this environment due to missing `sqlalchemy` (CI/container may differ).
- Index coverage: only primary keys and the unique constraint on `incidents.incident_id` exist. No indexes on `timestamp`, `metric`, `namespace`, or `pod` fields which will impact query performance on large datasets.
- No migration history: because schema is created ad-hoc, there's no versioned migration record for schema evolution.

Actions Taken (non-destructive)
- Created missing tables via direct `psycopg2` statements using the same DDL used by `backend/database.py` (all statements used `IF NOT EXISTS`).
- Did NOT alter or delete any existing schema, data, or repository files.

Files changed
- Added: `DATABASE_AUDIT.md` (this file)

Fixes Applied
- Missing tables created: `anomalies`, `incidents`, `fix_history`, `graph_nodes`, `graph_edges`.

Recommendations / Next Tasks
1. Ensure backend runs with `DB_TYPE=postgres` in its environment and restart the backend so `init_db()` runs at startup (preferred), or run a controlled init script on startup.
   - Example environment variable (export in your systemd/Helm/Deployment): `DB_TYPE=postgres`.
2. Add migration tooling (Alembic) to the repository and generate initial baseline migration reflecting current schema. This provides safe, versioned schema evolution.
3. Improve index coverage (non-breaking): consider adding indexes on
   - `anomalies(timestamp)`, `anomalies(metric)`, `anomalies(namespace)`, `anomalies(pod)`
   - `incidents(timestamp)`, `incidents(namespace)`
   - Additional compound indexes depending on query patterns (e.g., `(namespace, timestamp)`)
4. Ensure `sqlalchemy` and other DB dependencies are declared in `requirements.txt` and available in the runtime environment so `install_psycopg2_pool()` and `init_db()` can run without import errors.
5. Implement migration checks in CI to detect schema drift (compare DB schema vs migrations) prior to releases.
6. Consider adding a `schema_migrations` table (Alembic does this) and a nightly schema verification job.
7. Verify connection pooling on the deployed service: `database/pool.py` configures `QueuePool(pool_size=20, max_overflow=10, pool_pre_ping=True)` — ensure this is acceptable for your deployment size and tune if needed.

Notes & Non-goals
- No destructive actions were performed. No schema deletions or destructive migrations were run.
- I created tables directly because `init_db()` could not be executed here (missing `sqlalchemy`), but the DDL used matches the current `backend/database.py` logic.

NEXT TASK
- Set `DB_TYPE=postgres` in the backend service environment and restart the backend (or run `init_db()` in init container). Then confirm `init_db()` runs without import errors (ensure `sqlalchemy` installed). After that, run application-level smoke tests and an insertion test via the backend endpoints to confirm persistence and WebSocket broadcast behavior.
