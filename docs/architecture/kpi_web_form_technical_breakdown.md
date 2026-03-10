# KPI Web Form Technical Breakdown

## 1. Problem Statement and Objectives
The application must provide a governed write path into Redshift `kpi_catalog` so KPI definitions and usage mappings are controlled, auditable, and aligned with semantic-layer consumption.

Objectives:
- Separate KPI contract metadata from usage metadata.
- Enforce governance rules around status, certification, and versioning.
- Support CI/governance gates and semantic materialization workflows.
- Keep implementation simple enough for rapid deployment.

## 2. Canonical Data Model

### 2.1 KPI Definition (`kpi_catalog.kpi_definition`)
Stores the KPI contract:
- Identity (`kpi_id`, `kpi_slug`, `kpi_name`, `kpi_version`)
- Business context
- Ownership/governance (`status`, `certification_level`)
- Calculation semantics (`formula`, filter/rounding/null rules)
- Lineage (`metric_query_reference`, `source_objects`)
- Reliability/SLA
- Version/lifecycle (`kpi_version`, effective dates, change metadata)

### 2.2 KPI Usage (`kpi_catalog.kpi_usage`)
Stores where/how KPI is consumed:
- Reference to KPI by `kpi_id`, `kpi_slug`, and `kpi_version`
- Usage identity (`usage_type`, `consumer_tool`, `reference_name`, `reference_url`)
- Context (`source_system`, `context_notes`)
- Presentation hints (`default_chart_type`, `approved_visualizations`, `preferred_dimensions`, `preferred_filters`)
- Usage-level security notes (`row_level_security_notes`)

## 3. Logical Architecture

```text
Browser
  -> Django Views + Forms
    -> Service Layer (governance rules)
      -> Repository Layer (parameterized SQL)
        -> Redshift: kpi_catalog.kpi_definition, kpi_catalog.kpi_usage

Django default DB: auth/sessions/local app audit
```

## 4. Suggested App Structure

```text
kpi_admin/
  config/
    settings.py
    urls.py
  kpi_portal/
    forms.py
    views.py
    permissions.py
    services/
      kpi_definition_service.py
      kpi_usage_service.py
    repositories/
      kpi_definition_repository.py
      kpi_usage_repository.py
    validators/
      kpi_validators.py
    templates/
      kpi_form.html
      kpi_list.html
      kpi_usage_form.html
      kpi_usage_list.html
```

## 5. Core User Flows

### 5.1 Create or Update KPI Definition
1. User submits definition form.
2. Form validates required fields and value constraints.
3. `KpiDefinitionService` enforces governance/version rules.
4. Repository writes to `kpi_catalog.kpi_definition`.
5. Audit event captured in app audit store.

### 5.2 Create KPI Usage Mapping
1. User searches with either `kpi_id` or `kpi_slug`; UI auto-fills `kpi_id`, `kpi_slug`, and `kpi_version`.
2. Service verifies KPI exists and key values resolve to the same definition version.
3. User selects one or more `consumer_tools`.
4. Service validates usage metadata (`usage_type`, `consumer_tool`, `reference_name`).
5. Repository writes one row per selected consumer tool to `kpi_catalog.kpi_usage`.
5. Audit event recorded.

## 6. Validation and Governance Rules

### 6.1 Definition Rules
- Required metadata completeness for governed KPI lifecycle.
- `active + certified` controls for executive publication eligibility.
- Breaking logic changes must include version/change metadata.
- Effective date windows should not overlap for incompatible active definitions.

### 6.2 Usage Rules
- `kpi_id` and (`kpi_slug`, `kpi_version`) must exist in `kpi_definition` and match the same record.
- Usage identity must be specific enough for impact analysis.
- Presentation metadata should remain usage-scoped, not copied back into definitions.
- `consumer_tools` multi-select on create maps to multiple single-tool records for normalized storage.
- Accessible helper text defines:
  - `reference_name`: human-recognizable asset name.
  - `source_system`: where the usage is hosted.
  - `reference_url`: direct open link to the usage surface.
  - `additional_notes`: free-text implementation context.

## 7. Data Access and SQL Strategy
- Use `connections['warehouse']` and parameterized SQL for Redshift.
- Avoid Django-managed migrations for Redshift catalog tables.
- Keep Django migrations on `default` DB only.

Representative statements:
- `INSERT INTO kpi_catalog.kpi_definition (...) VALUES (...)`
- `INSERT INTO kpi_catalog.kpi_usage (...) VALUES (...)`

Redshift note:
- Primary/unique constraints are informational in many Redshift patterns; enforce critical integrity checks in service/CI logic.
- DDL should declare explicit `PRIMARY KEY`, `DISTKEY`, and `SORTKEY` on both tables for optimizer hints and operational consistency.

## 8. Authorization Model
- `kpi_admin`: full create/update rights including status/certification transitions.
- `kpi_editor`: create/update draft definitions and usage mappings.
- `kpi_viewer`: read-only.
- Enforce policy in service layer, not only in UI.

## 9. Auditability and Observability

### 9.1 Audit Trail
Track:
- actor
- action (`create_definition`, `update_definition`, `create_usage`, `update_usage`)
- target key (`kpi_id`, `usage_id`)
- before/after payload
- timestamp

### 9.2 Operational Metrics
Track:
- form success/failure counts
- validation rejection by rule
- Redshift write latency
- downstream CI/gate failures (if integrated)

## 10. CI and Governance Integration
Required checks for KPI-related changes:
- metadata completeness
- SQL/model compilation
- approved source object references
- version/change metadata for breaking changes
- semantic artifact regeneration

Reject changes that introduce uncataloged or uncertified executive KPI usage.

## 11. Semantic-Layer Enforcement
- Semantic KPI outputs materialize to `semantic.kpi_values_*`.
- BI roles should have `SELECT` on `semantic.*` only.
- Catalog governs what is eligible for publication.

## 12. Deployment
- Single-container Django service (Gunicorn).
- Env-based config for dual DB connections.
- Typical variables:
  - `DJANGO_SECRET_KEY`
  - `DJANGO_DEBUG=false`
  - `DEFAULT_DATABASE_URL`
  - `WAREHOUSE_DATABASE_URL`
  - `ALLOWED_HOSTS`

## 13. Risks and Mitigations
- Direct SQL bypass of governance.
  - Mitigation: restrict write permissions to app/service role.
- Drift between catalog metadata and semantic outputs.
  - Mitigation: CI regeneration and validation gates.
- Incomplete usage lineage.
  - Mitigation: require `usage_type` + consumer identity fields in form validation.

## 14. Definition of Done
- Web form supports create/update/list for `kpi_definition` and `kpi_usage`.
- Governance validation blocks invalid states before warehouse writes.
- Audit trail captures all write operations.
- Semantic-layer and BI consumption controls are documented and enforceable.
- KPI usage create form supports KPI ID/slug lookup and multi-tool row creation.
