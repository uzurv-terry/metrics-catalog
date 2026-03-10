# Current App Redshift Connection Process (metrics-catalog)

## Purpose
Document the exact Redshift connection and execution pattern used by this Flask KPI web form app.

## Connection Model Used by This App
This app uses the **Redshift Data API** (not direct TCP database connections):
- AWS SDK (`boto3`)
- Redshift Data API client (`redshift-data`)
- Secret-based DB auth via `SecretArn`

Primary implementation files:
- `app/infrastructure/redshift/connection_factory.py`
- `app/infrastructure/redshift/data_api_executor.py`
- `app/infrastructure/redshift/repositories/kpi_definition_repository.py`
- `app/infrastructure/redshift/repositories/kpi_usage_repository.py`
- `app/config.py`

## Required Environment Variables
- `CLUSTER_ID`
- `DATABASE`
- `SECRET_ARN`
- `AWS_DEFAULT_REGION`
- `AWS_PROFILE` (recommended for local profile-based auth)

Optional app settings:
- `FLASK_SECRET_KEY`
- `FLASK_DEBUG`

## Authentication and Authorization Path
1. App loads environment variables.
2. `boto3.session.Session(profile_name=AWS_PROFILE, region_name=AWS_DEFAULT_REGION)` is created.
3. `session.client("redshift-data")` is created.
4. SQL is submitted via `execute_statement` with:
   - `ClusterIdentifier`
   - `Database`
   - `SecretArn`
   - `Sql`
   - optional named `Parameters`
5. Statement completion is polled via `describe_statement`.
6. SELECT results are read via `get_statement_result`.

## IAM Permissions Needed
For the app runtime identity/profile:
- `redshift-data:ExecuteStatement`
- `redshift-data:DescribeStatement`
- `redshift-data:GetStatementResult`
- `secretsmanager:GetSecretValue` on `SECRET_ARN`

## SQL Execution Pattern in This App
- Repository methods use named parameters in SQL (`:param_name`).
- Executor converts request params into Data API `Parameters`.
- Writes and reads are synchronous from the web request perspective.

## Runtime Behavior
- No app-managed DB connection pool.
- No cursor/transaction object in app code.
- Unit of work commit/rollback are no-op wrappers for Data API mode.
- Health endpoint (`GET /health`) runs `select 1 as ok` through Data API.

## Web App Endpoints (Current)
- `GET /`
- `GET /health`
- `GET/POST /kpi-definitions/new`
- `GET /kpi-definitions/`
- `GET/POST /kpi-definitions/<kpi_slug>/<kpi_version>/edit`
- `GET/POST /kpi-usage/new`
- `GET /kpi-usage/`
- `GET/POST /kpi-usage/<usage_id>/edit`

## Validation Checklist
1. Load env vars (`CLUSTER_ID`, `DATABASE`, `SECRET_ARN`, `AWS_DEFAULT_REGION`, `AWS_PROFILE`).
2. Ensure profile session is valid: `aws sts get-caller-identity --profile <profile>`.
3. Start app: `python run.py`.
4. Verify connection via: `GET /health`.
5. Create test records in:
   - `/kpi-definitions/new`
   - `/kpi-usage/new`
6. Verify rows in:
   - `kpi_catalog.kpi_definition`
   - `kpi_catalog.kpi_usage`

## Failure Modes
- Missing env vars: startup/runtime errors from factory validation.
- IAM denied: `AccessDeniedException` on Data API calls.
- Bad secret ARN: resource not found or secret access error.
- SQL error: statement status `FAILED` with Data API error payload.
- Expired local profile session: auth failure until re-login.
