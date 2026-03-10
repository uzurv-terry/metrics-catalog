# AWS Deployment Runbook: KPI Catalog App

## 1. Purpose
This runbook documents how to deploy `metrics-catalog` into your AWS environment using the connection pattern already implemented in this repo:
- Flask app
- Redshift Data API via `boto3`
- Secrets Manager secret referenced by `SECRET_ARN`
- Environment-driven config from `.env`

This is written for an internal deployment model where app runtime sits in your AWS VPC and accesses Redshift through AWS APIs (not direct DB TCP from app code).

## 2. Current App Runtime Contract
The app requires these runtime env vars:
- `CLUSTER_ID`
- `DATABASE`
- `SECRET_ARN`
- `AWS_DEFAULT_REGION`
- `FLASK_SECRET_KEY`

Optional:
- `PORT` (default `5000`)
- `FLASK_DEBUG` (set `false` in deployed environments)
- `LOG_LEVEL`
- `AWS_PROFILE` (local dev only; do not depend on this in EC2/ECS runtime)

Code references:
- `app/config.py`
- `app/infrastructure/redshift/connection_factory.py`
- `app/infrastructure/redshift/data_api_executor.py`

## 3. Recommended Deployment Topology (Given Current Infra)

```text
User (internal network / VPN)
  -> ALB (internal)
    -> EC2 Auto Scaling Group (private subnets)
      -> systemd service (gunicorn serving Flask)
        -> AWS API endpoints (Redshift Data API + Secrets Manager + STS)
          -> Redshift cluster (ClusterIdentifier + SecretArn auth)
```

Why this fits current implementation:
- App already uses Data API and does not need direct Redshift driver pooling.
- Existing local flow is AWS profile based; production should move to IAM role on compute.
- Operationally simple for internal tooling.

## 4. Prerequisites and AWS Resources

## 4.1 Existing/Required AWS Resources
- Redshift cluster: `data-warehouse-uat-cluster` (or environment equivalent)
- Redshift DB: `uzurv_app_rs` (or environment equivalent)
- Secrets Manager secret containing Redshift credentials usable by Data API
- VPC with private subnets for app runtime
- Internal ALB and target group
- TLS certificate in ACM for internal DNS name
- CloudWatch Logs access

## 4.2 IAM Role for App Runtime (EC2 instance profile or ECS task role)
Minimum policy actions:
- `redshift-data:ExecuteStatement`
- `redshift-data:DescribeStatement`
- `redshift-data:GetStatementResult`
- `secretsmanager:GetSecretValue` on the specific secret ARN
- `kms:Decrypt` if secret uses CMK and key policy requires explicit grant
- Optional for diagnostics: `sts:GetCallerIdentity`

Tight scoping recommendations:
- Scope secret permission to exact `SECRET_ARN`.
- Scope Redshift Data API actions by cluster/database condition where feasible.
- Deny wildcard secret access by default.

## 5. Environment Strategy by Stage
Use separate values for each environment (`dev`, `uat`, `prod`):
- `CLUSTER_ID`
- `DATABASE`
- `SECRET_ARN`
- `AWS_DEFAULT_REGION`
- `FLASK_SECRET_KEY`
- App URL / DNS / ALB target group

Suggested naming convention:
- App service name: `metrics-catalog-<env>`
- Env file path: `/opt/metrics-catalog/shared/.env.<env>`
- CloudWatch log group: `/apps/metrics-catalog/<env>`

## 6. Production Runtime Configuration
Example deployed env file (`/opt/metrics-catalog/shared/.env.uat`):

```bash
CLUSTER_ID=data-warehouse-uat-cluster
DATABASE=uzurv_app_rs
SECRET_ARN=arn:aws:secretsmanager:us-east-1:371707344195:secret:datawarehouse-uat/connections-xxxxxx
AWS_DEFAULT_REGION=us-east-1
FLASK_SECRET_KEY=<long-random-secret>
FLASK_DEBUG=false
LOG_LEVEL=INFO
PORT=5000
```

Important:
- Do not set static AWS keys in this file.
- Do not rely on `AWS_PROFILE` in deployed runtime; use compute IAM role.

## 7. Build and Artifact Process

## 7.1 Build Artifact Contents
Package:
- `app/`
- `run.py`
- `requirements.txt`
- deployment scripts (`deploy/` recommended)

Exclude:
- `.env`
- local caches (`__pycache__/`, `.DS_Store`)
- developer-only files

## 7.2 Reproducible Build Step
From CI runner:

```bash
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
python3 -m compileall app run.py
```

If compile step fails, fail deployment.

## 8. EC2 Deployment Procedure (Systemd + Gunicorn)

## 8.1 One-Time Host Bootstrap
On each app host:
1. Create app directories:
   - `/opt/metrics-catalog/current`
   - `/opt/metrics-catalog/releases`
   - `/opt/metrics-catalog/shared`
2. Install Python runtime and system packages.
3. Install `gunicorn` (or include in requirements).
4. Place env file in `/opt/metrics-catalog/shared/.env.<env>`.

## 8.2 Systemd Service Unit
Create `/etc/systemd/system/metrics-catalog.service`:

```ini
[Unit]
Description=Metrics Catalog Flask App
After=network.target

[Service]
User=ec2-user
Group=ec2-user
WorkingDirectory=/opt/metrics-catalog/current
EnvironmentFile=/opt/metrics-catalog/shared/.env.uat
ExecStart=/usr/bin/python3 -m gunicorn --bind 0.0.0.0:5000 --workers 2 --threads 4 --timeout 120 run:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Then:

```bash
sudo systemctl daemon-reload
sudo systemctl enable metrics-catalog
sudo systemctl start metrics-catalog
sudo systemctl status metrics-catalog
```

## 8.3 Release Rollout
For each deploy:
1. Upload artifact to host (or pull from artifact store).
2. Extract to `/opt/metrics-catalog/releases/<timestamp-or-sha>`.
3. Install dependencies there.
4. Update symlink:
   - `/opt/metrics-catalog/current -> /opt/metrics-catalog/releases/<new>`
5. Restart service:
   - `sudo systemctl restart metrics-catalog`
6. Verify health:
   - `curl -sS http://127.0.0.1:5000/health`

## 9. ALB, Networking, and DNS

## 9.1 Target Group
- Protocol: HTTP
- Port: `5000`
- Health check path: `/health`
- Healthy threshold: 2-3 checks
- Matcher: `200`

## 9.2 Security Groups
- ALB SG: allow inbound from approved internal CIDRs (or VPN CIDRs)
- App SG: allow inbound `5000` from ALB SG only
- App SG outbound: allow HTTPS to AWS APIs (Data API, Secrets Manager, STS)

## 9.3 Private Subnet Egress
If app hosts are in private subnets, ensure route to AWS APIs via:
- NAT gateway, or
- Interface VPC Endpoints (recommended for tighter egress control):
  - Secrets Manager
  - STS
  - (and required endpoints used by your SDK path)

## 10. Deployment Validation Checklist
After each deployment:
1. `GET /health` returns `{"status":"ok"}`.
2. Open `/kpi-definitions/` and `/kpi-usage/` successfully.
3. Create one test KPI definition.
4. Create one KPI usage row for that definition.
5. Confirm records exist in Redshift:

```sql
select kpi_id, kpi_slug, kpi_version, created_at
from kpi_catalog.kpi_definition
order by created_at desc
limit 5;

select usage_id, kpi_id, kpi_slug, kpi_version, consumer_tool, created_at
from kpi_catalog.kpi_usage
order by created_at desc
limit 5;
```

## 11. Rollback Procedure
If health checks fail or critical functionality breaks:
1. Point `current` symlink back to previous release.
2. `sudo systemctl restart metrics-catalog`
3. Verify `GET /health`.
4. Keep failed release directory for forensics.
5. Create incident note with deploy SHA/time.

## 12. Observability and Operations

## 12.1 Logs
At minimum collect:
- Gunicorn stdout/stderr
- Flask errors
- Deployment events

Recommended:
- Ship logs to CloudWatch Logs
- Include request path, method, status, latency, and error stack traces

## 12.2 Alerts
Create alerts for:
- ALB target unhealthy
- `5xx` rate above threshold
- Health check failures
- Redshift Data API statement failures/timeouts

## 13. Security Hardening
- `FLASK_DEBUG=false` in all non-local environments.
- Keep `FLASK_SECRET_KEY` in secure env store.
- Restrict ALB ingress to internal networks.
- Use least privilege on runtime IAM role.
- Rotate Redshift secret per security policy.
- Ensure only approved principals can deploy.

## 14. CI/CD Pipeline Outline
Recommended pipeline stages:
1. Lint/type checks (if configured)
2. Compile smoke test (`compileall`)
3. Unit tests (add as project grows)
4. Build artifact
5. Deploy to UAT
6. UAT smoke test (`/health` + create flow)
7. Manual approval gate
8. Deploy to PROD
9. Post-deploy validation and monitoring checks

## 15. Infrastructure-as-Code Recommendation
If not already codified, manage these via IaC (Terraform/CloudFormation/CDK):
- IAM role/policies
- ALB/listener/target group
- ASG launch template
- Security groups
- CloudWatch alarms
- SSM parameters / secrets references

This makes deployments repeatable and reduces config drift.

## 16. Known App-Specific Notes
- `/health` actively executes `select 1` against Redshift Data API. It validates data-path readiness, not just process uptime.
- `run.py` honors runtime `PORT` env and loads `.env` automatically.
- The app currently uses synchronous request/response Data API calls, so latency depends on Data API response time.

## 17. Quick UAT Go-Live Checklist
- [ ] Runtime IAM role has required permissions.
- [ ] Env file has correct `CLUSTER_ID`, `DATABASE`, `SECRET_ARN`, `AWS_DEFAULT_REGION`.
- [ ] `FLASK_DEBUG=false`.
- [ ] ALB health check path configured to `/health`.
- [ ] Internal DNS record points to ALB.
- [ ] Smoke create/edit flows pass.
- [ ] Rollback tested once.
