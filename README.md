# metrics-catalog

Flask app for managing metric metadata in Redshift:
- `kpi_catalog.kpi_definition`
- `kpi_catalog.kpi_usage`
- `kpi_catalog.kpi_approver`

## What This App Does
- Create/edit/list metric definitions with governance rules.
- Create/edit/list metric usage mappings tied to metric ID/slug/version.
- Create/list metric approvers tied to metric version.
- Explore read-only metric/report lineage in a visual map.
- Enforce service-layer validation before Redshift writes.
- Connect to Redshift using the Data API (`boto3` + `redshift-data`).

## Requirements
- Python 3.10+
- AWS CLI configured profile with Redshift Data API + Secrets Manager access
- Redshift cluster/database/secret values

## Configuration
The app loads `.env` automatically.

Required env vars:
- `CLUSTER_ID`
- `DATABASE`
- `SECRET_ARN`
- `AWS_PROFILE`
- `AWS_DEFAULT_REGION`
- `FLASK_SECRET_KEY`

Optional:
- `PORT` (defaults to `5000`)
- `FLASK_DEBUG` (`true`/`false`)
- `LINEAGE_MAX_NODES`
- `LINEAGE_MAX_EDGES`
- `LINEAGE_SEARCH_LIMIT`
- `LINEAGE_CACHE_TTL_SEC`

Use profile-based auth (recommended):

```bash
unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN
```

## Run Locally

```bash
python3 -m pip install -r requirements.txt
python3 run.py
```

If port `5000` is already in use:

```bash
PORT=5001 python3 run.py
```

## App Routes
- `/` Home
- `/kpi-definitions/` Metric Definitions workspace
- `/kpi-usage/` Metric Usage workspace
- `/kpi-approvers/` Metric Approvers workspace
- `/lineage/` Visual Metric Map
- `/health` Data API health check (`select 1`)

## Testing
See:
- `docs/testing/testing_guide.md`

## Documentation
See:
- `docs/README.md` (index)
- `docs/architecture/`
- `docs/operations/`
- `docs/testing/`
- `docs/standards/`

Deployment reference:
- `docs/operations/aws_deployment_runbook.md`
- `docs/operations/allowable_operations_guide.md`
