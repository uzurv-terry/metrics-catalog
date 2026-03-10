# Login and Environment Setup Steps (metrics-catalog)

This document captures the recommended local login + environment flow for running the KPI web form app with profile-based AWS auth.

## 1. Profile Login Flow

1. Set/refresh AWS profile session (example profile `uzsts`).
2. Ensure static credentials are not exported:

```bash
unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN
```

3. Verify profile works:

```bash
aws sts get-caller-identity --profile uzsts
```

Expected: successful identity output for your account/user/role.

## 2. App Environment Setup

1. Prepare virtual environment and install dependencies:

```bash
cd /Users/terrymayfield/Repositories/metrics-catalog
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Create `.env` from template:

```bash
cp .env.example .env
```

3. Set required Data API variables in `.env`:
- `AWS_PROFILE=uzsts`
- `AWS_DEFAULT_REGION=us-east-1`
- `CLUSTER_ID=<cluster-id>`
- `DATABASE=<db-name>`
- `SECRET_ARN=<secret-arn>`
- `FLASK_SECRET_KEY=<secret>`

4. Load `.env` into shell:

```bash
set -a
source .env
set +a
```

## 3. Run and Verify

1. Start app:

```bash
python run.py
```

2. Verify health:
- Open `http://127.0.0.1:5000/health`
- Expected: `{"status":"ok"}`

3. Verify forms:
- `http://127.0.0.1:5000/kpi-definitions/new`
- `http://127.0.0.1:5000/kpi-usage/new`

## 4. Troubleshooting Notes

- `AccessDeniedException`: missing IAM permissions for Data API or Secrets Manager.
- `ResourceNotFoundException` for secret: bad `SECRET_ARN` or wrong region.
- Auth/session errors: refresh profile login (for SSO-backed profiles, run your org’s login command).
- Startup env errors: check that `CLUSTER_ID`, `DATABASE`, `SECRET_ARN` are present.

## 5. Correct App Start Command

For this repo, use:

```bash
python run.py
```

Do not use stale commands from other repos that reference `src.app`.
