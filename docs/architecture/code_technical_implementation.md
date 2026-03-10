# Metrics Catalog: Full Code Technical Implementation

## 1. System Purpose
`metrics-catalog` is a Flask web application used to manage governed KPI metadata in Amazon Redshift.

Primary managed entities:
- `kpi_catalog.kpi_definition`
- `kpi_catalog.kpi_usage`
- `kpi_catalog.kpi_approver`

Read-only lineage UI/API:
- embedded in `/kpi-definitions/overview`
- `/lineage/api/kpi/<slug>/<version>`
- `/lineage/api/report`
- `/lineage/api/search/kpi`
- `/lineage/api/search/report`

The app provides server-rendered CRUD-style workflows (currently create/list/update where applicable) with service-layer governance validation and Redshift Data API persistence.

## 2. Architecture Pattern
The codebase follows a Clean Architecture-inspired layered approach with repository pattern:

- Interface Layer: Flask blueprints, WTForms, Jinja templates
- Application Layer: DTOs, services, repository ports, unit-of-work contract
- Domain Layer: dataclass models + domain exceptions
- Infrastructure Layer: Redshift Data API executor, repository implementations, unit-of-work composition

This keeps business rules in services and SQL concerns in repositories.

## 3. Runtime and Configuration
Config source:
- `.env` (auto-loaded)
- process env vars

Key runtime settings (`app/config.py`):
- Redshift Data API: `CLUSTER_ID`, `DATABASE`, `SECRET_ARN`, `AWS_DEFAULT_REGION`, optional `AWS_PROFILE`
- Flask: `FLASK_SECRET_KEY`, `FLASK_DEBUG`, `PORT`
- Data API tuning: `DATA_API_POLL_INTERVAL_SEC`, `DATA_API_MAX_WAIT_SEC`
- Lineage tuning: `LINEAGE_MAX_NODES`, `LINEAGE_MAX_EDGES`, `LINEAGE_SEARCH_LIMIT`, `LINEAGE_CACHE_TTL_SEC`

App factory (`app/__init__.py`):
- builds Flask app
- wires service container in `app.extensions["services"]`
- registers blueprints
- exposes `/health` which executes `select 1` via Data API

## 4. Data Access Implementation

### 4.1 Connection Factory
`app/infrastructure/redshift/connection_factory.py`
- validates required Data API env vars
- creates `boto3.session.Session`
- creates `redshift-data` client
- returns `RedshiftDataApiExecutor`

### 4.2 Data API Executor
`app/infrastructure/redshift/data_api_executor.py`
- `execute(sql, params)` for non-query statements
- `query(sql, params)` for select statements with pagination support
- polls statement status with configurable poll interval
- converts result field types into Python values
- avoids Data API empty-parameter errors using sentinel mapping:
  - `None`/`""` -> `__APP_NULL_SENTINEL__`

### 4.3 Unit of Work
`app/infrastructure/redshift/unit_of_work.py`
- composes repositories per request scope
- exposes `definitions`, `usage`, `approvers`
- commit/rollback are no-ops in Data API execution model

## 5. Domain Model
Domain dataclasses (`app/domain/models/`):
- `KpiDefinition`
- `KpiUsage`
- `KpiApprover`

Lineage DTOs (`app/application/dto/`):
- `LineageNodeDTO`
- `LineageEdgeDTO`
- `LineageGraphDTO`

Domain exceptions (`app/domain/exceptions.py`):
- validation and conflict errors surfaced to UI via flash messages

## 6. Application Services and Business Rules

### 6.1 KPI Definition Service
`app/application/services/kpi_definition_service.py`

Responsibilities:
- create/list/get/update definitions
- derive `kpi_slug` from `kpi_name`
- generate `kpi_id` UUID on create
- enforce uniqueness checks

Core rules:
- `kpi_name` required and unique
- `kpi_version >= 1`
- `status=active` requires two approvals
- `status=draft` cannot pair with `certification_level=certified`
- JSON fields must parse when provided

### 6.2 KPI Usage Service
`app/application/services/kpi_usage_service.py`

Responsibilities:
- create/list/get/update usage rows

Core rules:
- referenced KPI identity must exist (`kpi_id + kpi_slug + kpi_version`)
- JSON parse validation for preferred filters
- Tableau dashboard guardrail: requires KPI `active + certified`
- multi-tool create is validated once per KPI identity and persisted as one batch write

### 6.3 KPI Approver Service
`app/application/services/kpi_approver_service.py`

Responsibilities:
- create/list approver rows

Core rules:
- `approver_name` required
- `kpi_version >= 1`
- referenced KPI identity must exist
- duplicate approver name for same KPI version is blocked

### 6.4 Lineage Service
`app/application/services/lineage_service.py`

Responsibilities:
- build KPI-centric and report-centric graph payloads
- cache repeated lineage reads in-process
- enforce node/edge/search limits for predictable response time

Core rules:
- KPI lineage requires `kpi_slug` and `kpi_version`
- report lineage requires `consumer_tool` and `reference_name`
- neighborhood graphs are capped server-side

## 7. Repository Layer
Repository ports (`app/application/ports/`) define contracts.
Redshift implementations live in `app/infrastructure/redshift/repositories/`.

### 7.1 KPI Definition Repository
- lookup by key/identity/name
- recent list
- recent summary list for table views
- insert/update operations
- maps SUPER fields using `json_parse/json_serialize`

### 7.2 KPI Usage Repository
- recent list + by `usage_id`
- recent summary list for table views
- insert/update
- batch insert for multi-tool create flows
- optional values normalized to NULL via sentinel-based `nullif`

### 7.3 KPI Approver Repository
- recent list
- recent summary list for table views
- insert
- existence check for duplicate approver-by-KPI

### 7.4 Lineage Repository
- KPI lineage query (`kpi_definition` left join `kpi_usage`)
- report lineage query (`kpi_usage` join `kpi_definition`)
- KPI search query
- report search query

## 8. Web Interface Implementation

## 8.1 Blueprints
`app/interface/web/blueprints/`
- `kpi_definitions.py` (`/kpi-definitions/`)
- `kpi_usage.py` (`/kpi-usage/`)
- `kpi_approvers.py` (`/kpi-approvers/`)
- `lineage.py` (lineage API endpoints + legacy redirect from `/lineage/`)

All blueprints:
- perform form binding
- map form -> DTO
- call services
- translate domain/service errors into flash messages
- follow post/redirect/get pattern on successful writes

## 8.2 Forms
`app/interface/web/forms/`
- `KpiDefinitionForm`
- `KpiUsageForm`
- `KpiApproverForm`

Notable UX behavior:
- required labels marked `(Required)`
- date pickers for effective dates (`type=date`)
- KPI lookup helper fields for usage/approver forms
- KPI lookup uses debounced server-side typeahead instead of preloaded datalist rows
- lineage page uses debounced search and lightweight SVG rendering instead of an external graph library

## 8.3 Templates
`app/interface/web/templates/`

Shared layout:
- `base.html` defines design tokens, nav buttons, breadcrumb, shared scripts
- scripts include submit disable (`Saving...`) and unsaved-change warning

Page patterns:
- split workspace layout: create form + list table side-by-side
- top error summary and inline field errors
- progressive disclosure (`details.more-options`) for advanced fields

## 9. Navigation and Breadcrumb
Top nav buttons:
- Home
- KPI Definitions
- KPI Usage
- KPI Approvers
- Visual KPI Map

Breadcrumb behavior:
- context-aware path per blueprint
- includes edit-state suffix where relevant

## 10. Current Data Workflows

### 10.1 KPI Definition
- create new definition (version fixed to 1 for new KPI)
- edit existing definition by slug/version key
- list recent definitions

### 10.2 KPI Usage
- create usage rows for one or more selected tools (one row per tool)
- edit usage row by `usage_id`
- list recent usage rows
- create path batches multi-tool inserts into one repository write

### 10.3 KPI Approver
- add approver rows tied to KPI identity/version
- list recent approver rows
- create page resolves KPI identity through server-side typeahead

### 10.4 Visual KPI Map
- search KPIs by name/slug/ID
- search reports by `reference_name`
- render bounded KPI->report or report->KPI neighborhood graphs
- expose read-only lineage APIs backed by `kpi_definition` and `kpi_usage`

## 11. Validation and Integrity Strategy
Because Redshift constraints are often informational, integrity is enforced primarily in application services:
- identity existence checks
- uniqueness checks
- cross-field governance rules
- allowed state transitions

SQL still declares PK/sort/dist where relevant for optimizer and operational structure.

## 12. Performance Considerations
Current implemented optimizations:
- configurable Data API poll interval (`DATA_API_POLL_INTERVAL_SEC`)
- reduced list limits for heavy pages
- submit button disable to prevent duplicate user submits
- in-process lineage cache with TTL
- lineage node/edge/search caps
- server-side KPI typeahead for usage and approver forms
- summary-only list queries for list/table pages
- batched multi-tool usage inserts

Current bottlenecks:
- synchronous Data API round-trips per validation/write step
- validation reads that still occur before writes under the Data API model

Likely next improvements:
- request timing instrumentation on write/search/lineage endpoints
- shared cache for multi-instance read paths
- optional async write pipeline only if Data API latency remains unacceptable

## 13. Deployment Integration
Operational deployment guides:
- `docs/operations/aws_deployment_runbook.md`
- `docs/operations/redshift_connection_process.md`
- `docs/operations/allowable_operations_guide.md`

App is designed for internal AWS deployment using IAM role auth and Redshift Data API.

## 14. Known Scope Boundaries
Not currently implemented:
- delete/archive flows for definitions/usage/approvers
- full RBAC authorization model inside app routes
- optimistic locking/version conflict resolution on edit
- comprehensive automated unit/integration test suite

## 15. Summary
The app currently provides a production-leaning governance interface with:
- clean separation of concerns
- explicit service-level governance rules
- Redshift Data API persistence
- user-oriented web forms for definitions, usage, and approvers
- read-only visual lineage exploration with bounded graph rendering

The implementation is stable for controlled internal workflows and is structured for incremental hardening (RBAC, tests, advanced performance).
