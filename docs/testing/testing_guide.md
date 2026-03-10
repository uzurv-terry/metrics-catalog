# KPI Catalog App Testing Guide

## 1. Prerequisites
- Python 3.10+
- AWS CLI configured with profile `uzsts` (or another valid profile)
- Redshift Data API permissions + secret access permissions

Required IAM permissions for the runtime identity:
- `redshift-data:ExecuteStatement`
- `redshift-data:DescribeStatement`
- `redshift-data:GetStatementResult`
- `secretsmanager:GetSecretValue` for `SECRET_ARN`

## 2. Local Setup

```bash
cd /Users/terrymayfield/Repositories/metrics-catalog
python3 -m pip install -r requirements.txt
```

If your Python environment is externally managed, use:

```bash
python3 -m pip install --user -r requirements.txt
```

## 3. Environment Configuration (Data API Pattern)

1. Create your runtime env file:

```bash
cp .env.example .env
```

2. Edit `.env` with real values for:
- `CLUSTER_ID`
- `DATABASE`
- `SECRET_ARN`
- `AWS_DEFAULT_REGION`
- `AWS_PROFILE`
- `FLASK_SECRET_KEY`
- (`REDSHIFT_*` variables are not used in the current Data API implementation.)

3. Ensure static AWS keys are not exported:

```bash
unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN
```

4. Load env vars:

```bash
set -a
source .env
set +a
```

5. Verify AWS identity:

```bash
aws sts get-caller-identity --profile "$AWS_PROFILE"
```

## 4. Static/Syntax Checks

```bash
python3 -m compileall app run.py
```

Expected: no syntax errors.

## 5. App Factory Smoke Test

```bash
python3 - <<'PY'
from app import create_app
app = create_app()
print("app factory ok")
PY
```

Expected output: `app factory ok`

## 6. Start the App

```bash
python run.py
```

Open in browser:
- `http://127.0.0.1:5000/`
- `http://127.0.0.1:5000/health`

Expected for `/health`: JSON like `{"status":"ok"}`.

## 7. Functional Web Form Tests

### 7.1 KPI Definition Flow
1. Go to `/kpi-definitions/new`.
2. Create a KPI definition with:
- `kpi_name` (KPI ID is auto-generated)
- `kpi_version`
- required metadata (`business_definition`, owners, status, certification, formula)
3. Confirm it appears in `/kpi-definitions/`.
4. Click `Edit` and save updates.

### 7.2 KPI Usage Flow
1. Go to `/kpi-usage/new`.
2. In `Find KPI by ID or Slug`, search by either value and confirm `kpi_id + kpi_slug + kpi_version` auto-fill.
3. Select 2+ `Consumer Tools`.
4. Submit once and confirm one usage row is created per selected tool in `/kpi-usage/`.
5. Click `Edit` on a row and save updates.

## 8. Validation and Governance Checks

Run these behavior checks via forms:

1. Duplicate KPI definition:
- Create same `kpi_slug + kpi_version` twice.
- Expected: reject with conflict error.

1. Name uniqueness:
- Create a second KPI with the same `kpi_name`.
- Expected: reject with conflict error.

1. Derived slug:
- Enter a KPI name with spaces and punctuation.
- Expected: slug preview auto-derives and persisted row uses derived slug.

2. Active status requirement:
- Set `status=active` without owner fields.
- Expected: validation error.

1. Two-approval activation gate:
- Set `status=active` without `Approval 1` and `Approval 2`.
- Expected: validation error.

3. Certified requirement:
- Set `certification_level=certified` without `metric_query_reference`.
- Expected: validation error.

4. Usage identity integrity:
- Submit usage with mismatched `kpi_id/slug/version`.
- Expected: validation error.

5. Executive Tableau rule:
- Use `consumer_tool=tableau` and `usage_type=dashboard` for non-`active+certified` KPI.
- Expected: validation error.

6. Multi-select consumer tools:
- Submit usage with multiple selected tools.
- Expected: one new row per selected tool, same KPI identity and usage reference fields.

7. Consumer tool required on create:
- Submit usage without selecting any consumer tool.
- Expected: validation error.

## 9. Redshift Data Verification (Optional)

Run in Redshift query editor:

```sql
select kpi_id, kpi_slug, kpi_version, status, certification_level, created_at
from kpi_catalog.kpi_definition
order by created_at desc
limit 20;

select usage_id, kpi_id, kpi_slug, kpi_version, consumer_tool, usage_type, reference_name, created_at
from kpi_catalog.kpi_usage
order by created_at desc
limit 20;
```

## 10. Troubleshooting

1. `AccessDeniedException` from Data API:
- Verify runtime IAM permissions for `redshift-data:*` actions and secret access.

2. Secret not found / invalid ARN:
- Validate `SECRET_ARN` and `AWS_DEFAULT_REGION`.

3. AWS profile/session errors:
- Run `aws sso login --profile uzsts` (if SSO-backed) and retry.

4. App health endpoint fails:
- Verify `CLUSTER_ID`, `DATABASE`, `SECRET_ARN`, `AWS_PROFILE` are loaded.
- Confirm Redshift cluster supports Data API for your setup.
