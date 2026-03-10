# KPI Web Form Solution Summary

## Goal
Build a lightweight Django web application that manages governed KPI metadata in Redshift and records downstream KPI usage, while enforcing semantic-layer consumption and governance policy.

## Authoritative Design Alignment
Based on `kpi_catalog_technical_design.md`, the web form supports two catalog tables:
- `kpi_catalog.kpi_definition`: KPI contract metadata (identity, semantics, governance, lineage, reliability, versioning).
- `kpi_catalog.kpi_usage`: downstream usage mapping (where/how KPI is consumed, tool context, presentation hints), keyed with `kpi_slug` and `kpi_version`.

## Core Governance Model
- KPI catalog is the control plane.
- Semantic outputs (`semantic.kpi_values_*`) are the data plane.
- BI tools (e.g., Tableau) must consume `semantic.*`, not ad-hoc raw/reporting tables.
- Executive KPI publication requires `status='active'` and `certification_level='certified'`.

## MVP Scope for the Web Form
- Server-rendered Django UI (no SPA required).
- Create/edit/list for:
  - `kpi_definition` rows (including version lifecycle fields)
  - `kpi_usage` rows linked by `kpi_id`, `kpi_slug`, and `kpi_version`
- Validation and authorization in service layer.
- Basic audit logging of user actions.
- KPI usage create UX supports:
  - KPI lookup by either `kpi_id` or `kpi_slug` (auto-fills id/slug/version)
  - Multi-select consumer tools (one usage row per selected tool)
  - In-page plain-language definitions for `reference_name`, `source_system`, and `reference_url`
  - Additional notes capture for usage context.

## Recommended Architecture
- Two DB connections:
  - `default` (Postgres): Django auth/session/audit
  - `warehouse` (Redshift): `kpi_catalog` writes
- Layered flow:
  - views/forms for HTTP concerns
  - services for governance rules
  - repositories for parameterized Redshift SQL

## Key App Rules to Enforce
- `kpi_usage` must reference an existing KPI definition by both `kpi_id` and (`kpi_slug`, `kpi_version`).
- Activation/certification transitions restricted to admin role.
- Breaking changes to KPI semantics require version/change metadata updates.
- Usage records must contain stable consumer identity (`usage_type`, `consumer_tool`, `reference_name`).
- Only cataloged active/certified KPI versions can be published to executive semantic outputs.

## Navigation Guidance
- Keep top navigation for small internal tools (2-5 main sections).
- Add persistent left-side navigation when section count grows, labels are stable, and users switch contexts frequently.
- For this KPI tool, current top nav is appropriate now; introduce left nav if governance sections expand (approvals, audits, access controls, glossary).

## Delivery Sequence
1. Implement `kpi_definition` forms and validation.
2. Implement `kpi_usage` forms and validation (`kpi_id` + `kpi_slug` + `kpi_version` lookup + consumer metadata).
3. Add role-based access control and audit logs.
4. Add service-layer unit tests and Redshift integration tests.
5. Deploy and enforce BI access path to `semantic.*`.

## Outcome
The web form becomes a practical governance interface for KPI contract management and usage lineage, aligned with the semantic-layer enforcement strategy.
