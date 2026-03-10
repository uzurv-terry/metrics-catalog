# App-to-Redshift Connection (Technical)

## Purpose
Define the production connection pattern for the KPI app to Amazon Redshift for metadata and semantic-layer operations.

## Connection Topology
```text
KPI App (container/VM)
  -> VPC private subnet routing
    -> Redshift endpoint: <cluster-or-workgroup>.<region>.redshift.amazonaws.com:5439
      -> databases/schemas: kpi_catalog, semantic, report_ts, control
```

## Runtime Requirements
- Network path from app runtime to Redshift port `5439`.
- Redshift security group allows inbound from app security group.
- TLS enabled (`sslmode=verify-full` recommended).
- Credentials sourced from AWS Secrets Manager or IAM database auth (preferred over static passwords).

## Environment Configuration
```bash
REDSHIFT_HOST=example-cluster.abc123xyz.us-east-1.redshift.amazonaws.com
REDSHIFT_PORT=5439
REDSHIFT_DB=analytics
REDSHIFT_USER=kpi_app_user
REDSHIFT_PASSWORD=<secret-or-empty-if-iam-auth>
REDSHIFT_SCHEMA=kpi_catalog
REDSHIFT_SSLMODE=verify-full
REDSHIFT_CONNECT_TIMEOUT_SEC=10
REDSHIFT_STATEMENT_TIMEOUT_MS=900000
```

If using IAM auth, inject temporary password/token at runtime and rotate automatically.

## Python Driver Standard
Use `redshift_connector` for native Redshift support.

```python
import os
import redshift_connector

conn = redshift_connector.connect(
    host=os.environ["REDSHIFT_HOST"],
    port=int(os.environ.get("REDSHIFT_PORT", "5439")),
    database=os.environ["REDSHIFT_DB"],
    user=os.environ["REDSHIFT_USER"],
    password=os.environ["REDSHIFT_PASSWORD"],
    ssl=True,
    timeout=int(os.environ.get("REDSHIFT_CONNECT_TIMEOUT_SEC", "10")),
)

with conn.cursor() as cur:
    cur.execute("set search_path to kpi_catalog, semantic, report_ts, control, public;")
    cur.execute("set statement_timeout to %s;", (int(os.environ.get("REDSHIFT_STATEMENT_TIMEOUT_MS", "900000")),))
    cur.execute("select current_user, current_database(), current_schema;")
    print(cur.fetchone())

conn.close()
```

## Connection Management
- Use a small app-side pool (for example 5-15 open connections per app instance).
- Keep transactions short; explicit `commit`/`rollback` on writes.
- Use separate logical paths for:
  - metadata writes (`kpi_catalog.*`),
  - semantic object DDL (`semantic.*`),
  - reporting reads (`report_ts.*`).

## Security and Least Privilege
Recommended Redshift roles/users:
- `kpi_app_rw`: CRUD on `kpi_catalog`, DDL/DML on `semantic`, read on `report_ts`.
- `kpi_bi_ro`: read-only on `semantic` (no direct ad-hoc write paths).

Grant model (example):
```sql
GRANT USAGE ON SCHEMA kpi_catalog, semantic, report_ts TO ROLE kpi_app_rw;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA kpi_catalog TO ROLE kpi_app_rw;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA semantic TO ROLE kpi_app_rw;
GRANT SELECT ON ALL TABLES IN SCHEMA report_ts TO ROLE kpi_app_rw;

GRANT USAGE ON SCHEMA semantic TO ROLE kpi_bi_ro;
GRANT SELECT ON ALL TABLES IN SCHEMA semantic TO ROLE kpi_bi_ro;
```

## Operational Checks
Run at app startup and on health endpoint:
1. TCP + TLS connectivity to Redshift endpoint.
2. Authentication success for app principal.
3. `SELECT 1` latency threshold (for example < 2s).
4. Schema access checks (`kpi_catalog`, `semantic`, `report_ts`).

## Failure Modes
- `timeout` / `could not connect`: routing, SG, NACL, endpoint, or cluster paused.
- `password authentication failed`: stale secret/token, IAM auth mismatch.
- `permission denied for schema/table`: missing role grants.
- `SSL error`: cert/hostname validation mismatch; enforce correct endpoint + `sslmode`.
