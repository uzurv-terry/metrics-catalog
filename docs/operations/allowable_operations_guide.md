# Allowable Operations Guide (KPI Catalog App)

## 1. Purpose
Define which operations are allowed in the KPI Catalog app and surrounding AWS runtime, including required controls and approvals.

This guide applies to:
- `kpi_catalog.kpi_definition`
- `kpi_catalog.kpi_usage`
- App runtime and deployment operations in AWS

## 2. Operating Principles
- KPI definition is a governed contract; usage is downstream mapping metadata.
- All writes go through the app/service layer (no ad-hoc bypass).
- Least privilege applies to both data and infrastructure operations.
- High-impact state changes require explicit approval evidence.

## 3. Operation Classes
- `Standard`: everyday operations, low to moderate risk.
- `Controlled`: allowed but requires additional checks/approvals.
- `Restricted`: only platform/data governance operators.
- `Prohibited`: not allowed in normal operations.

## 4. Allowed App Data Operations

## 4.1 KPI Definition Operations (`kpi_definition`)
1. `Create KPI Definition` — `Standard`
- Allowed via UI form.
- Enforced controls:
  - KPI ID auto-generated.
  - KPI slug derived from KPI name.
  - KPI name uniqueness enforced.
  - Required fields must pass validation.

2. `Update KPI Definition Metadata` (non-breaking) — `Standard`
- Allowed via UI edit flow.
- Must preserve valid required metadata.

3. `Set status=active` — `Controlled`
- Allowed only when two approvals are supplied (`approval_1_by`, `approval_2_by`).
- If approvals missing, operation is blocked by service validation.

4. `Set certification_level=certified` — `Controlled`
- Allowed only when Documentation Location is provided.

5. `Breaking Change update` — `Controlled`
- Allowed with `breaking_change_flag=true` and documented `change_reason`.
- Version lifecycle impact should be reviewed by governance owner.

6. `Delete KPI Definition` — `Prohibited` (current app behavior)
- No delete endpoint exists.
- Deactivation/deprecation lifecycle should be used instead.

## 4.2 KPI Usage Operations (`kpi_usage`)
1. `Create Usage Mapping` — `Standard`
- Allowed via UI.
- Must resolve valid `kpi_id + kpi_slug + kpi_version`.

2. `Create Multi-tool Usage` — `Standard`
- Allowed via multi-select Consumer Tools.
- System creates one row per selected tool.

3. `Update Usage Mapping` — `Standard`
- Allowed via UI edit.
- KPI identity and usage metadata validations still apply.

4. `Delete Usage Mapping` — `Prohibited` (current app behavior)
- No delete endpoint exists.

## 5. Controlled Governance Rules (Always Enforced)
1. KPI identity integrity
- Usage rows must point to an existing KPI definition identity.

2. Active status gate
- KPI cannot become `active` without two approvals.

3. Certification gate
- Certified KPI requires Documentation Location.

4. Tableau executive guardrail
- Tableau dashboard usage for non-`active+certified` KPI is rejected.

## 6. Infrastructure and Deployment Operations

## 6.1 Allowed Operations
1. `Deploy new app release` — `Controlled`
- Requires CI artifact build, health check pass, and post-deploy validation.

2. `Rollback deployment` — `Restricted`
- Allowed for on-call/platform operator during incident or failed deploy.

3. `Update runtime env vars` — `Restricted`
- Allowed only via approved change path.
- Mandatory checks after change: `/health`, form smoke tests.

4. `Rotate secret referenced by SECRET_ARN` — `Controlled`
- Allowed with coordination window and post-rotation validation.

## 6.2 Restricted Operations
1. `IAM policy broadening` (wildcards, broader secret access)
- Restricted to cloud security/platform owners.

2. `Network path changes` (SG, ALB, private subnet egress)
- Restricted to platform team.

3. `Schema DDL changes` in `kpi_catalog`
- Restricted to data platform team with design review.

## 7. Prohibited Operations
1. Direct ad-hoc writes to `kpi_catalog` tables from analyst tools or unmanaged scripts.
2. Running app in non-local environments with `FLASK_DEBUG=true`.
3. Storing static AWS keys in deployed `.env` files.
4. Granting BI roles direct write access to KPI catalog tables.
5. Skipping health checks after deployment/config changes.

## 8. Approval and Change Control Expectations
1. Standard operations
- In-app validation and normal change logging are sufficient.

2. Controlled operations
- Require documented reason and approver context (ticket/change record).

3. Restricted operations
- Require platform/data governance owner approval and rollback plan.

## 9. Evidence and Audit Expectations
Capture and retain:
- who performed the operation
- what changed
- when it changed
- validation evidence (health check, smoke test, query verification)
- associated ticket/change record for controlled/restricted actions

## 10. Day-2 Operational Checklist
For any controlled/restricted change:
1. Confirm intended scope and rollback path.
2. Apply change.
3. Verify `/health` = OK.
4. Verify KPI definition and KPI usage pages load.
5. Execute one create or read smoke check.
6. Record evidence in the change ticket.

## 11. Current-State Note
The app currently supports `create`, `list`, and `update` flows only. Delete/archive operations are intentionally not exposed in the UI at this time.
