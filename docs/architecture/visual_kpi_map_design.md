# KPI Lineage Visualization (Flask-Centric Design)

## 1. Purpose
Build a lineage experience in this Flask app that shows how KPI definitions are consumed by reports/dashboards/tools, optimized for internal governance workflows.

Primary workflows:
1. KPI -> Reports: select a KPI and see all downstream report assets.
2. Report -> KPIs: select a report asset and see all KPIs it depends on.

## 2. Scope and Non-Goals

In scope:
- Read-only lineage APIs
- Lineage page in existing Flask UI
- KPI/report search inputs
- Neighborhood graph rendering (not full-catalog graph)

Out of scope (phase 1):
- Full graph database
- Cross-system lineage beyond `kpi_catalog` tables
- Write/edit lineage from graph UI

## 3. Current Architecture Alignment
This feature should follow the same structure already used by the app:
- Interface: Flask blueprints + Jinja templates + JS
- Application: service layer for graph assembly and validation
- Infrastructure: repository SQL via Redshift Data API executor

Existing runtime constraints:
- Redshift Data API is synchronous and can be slower than direct DB connections.
- Existing pages already optimize by limiting result-set sizes.

## 4. Data Sources

## 4.1 `kpi_catalog.kpi_definition`
Used for KPI node metadata:
- `kpi_id`, `kpi_slug`, `kpi_name`, `kpi_version`
- `status`, `certification_level`
- `metric_query_reference` (displayed as Documentation Location)

## 4.2 `kpi_catalog.kpi_usage`
Used as edge table between KPI and report assets:
- `usage_id`
- `kpi_slug`, `kpi_version`, `kpi_id`
- `reference_name`, `reference_url`, `consumer_tool`, `usage_type`

## 4.3 `kpi_catalog.kpi_approver` (optional phase 2)
Not required for core lineage graph; may be used for governance badges or side-panel metadata.

## 5. Asset Identity Recommendation
Current usage table lacks a guaranteed stable report identifier. For robust report-centric lineage, add:
- `asset_id VARCHAR(255)` to `kpi_catalog.kpi_usage`

Interim fallback (if `asset_id` is not added yet):
- Use `(consumer_tool, reference_name)` as composite identity.
- Normalize `reference_name` case/whitespace in query conditions.

## 6. Flask Implementation Plan

## 6.1 Project Structure
```text
app/
  application/
    dto/
      lineage_graph_dto.py
    ports/
      lineage_repository.py
    services/
      lineage_service.py
  infrastructure/redshift/repositories/
    lineage_repository.py
  interface/web/
    blueprints/
      lineage.py
    templates/
      metric_overview.html  # embedded lineage section
    static/
      lineage.js
      lineage.css
```

## 6.2 Blueprint Endpoints
Page shell:
- `GET /kpi-definitions/overview`

JSON APIs:
- `GET /api/lineage/kpi/<kpi_slug>/<int:kpi_version>`
- `GET /api/lineage/report` with query params:
  - preferred: `asset_id`
  - fallback: `consumer_tool`, `reference_name`
- `GET /api/search/kpi?q=<term>`
- `GET /api/search/report?q=<term>&tool=<optional>`

## 6.3 Service Layer Responsibilities
`LineageService` should:
- validate route/query inputs
- enforce neighborhood size limits
- map repository rows -> graph DTO (`nodes`, `edges`, `details`)
- optionally filter by visibility policy (status/certification/tool)

## 6.4 Repository Layer Responsibilities
`LineageRepository` should:
- perform parameterized single-purpose read queries
- return lightweight row shapes (avoid selecting large text fields)
- support hard limits (`LIMIT` clauses)

## 7. API Contracts

## 7.1 KPI-centric response
`GET /api/lineage/kpi/<slug>/<version>`

```json
{
  "nodes": [
    {"id": "kpi:revenue:v1", "type": "kpi", "label": "Revenue", "status": "active", "certification_level": "certified"},
    {"id": "asset:tableau:exec-scorecard", "type": "report", "label": "Executive Scorecard", "tool": "tableau"}
  ],
  "edges": [
    {"id": "usage:123", "source": "kpi:revenue:v1", "target": "asset:tableau:exec-scorecard", "usage_type": "dashboard"}
  ],
  "meta": {"node_count": 2, "edge_count": 1}
}
```

## 7.2 Report-centric response
`GET /api/lineage/report?...`

```json
{
  "nodes": [
    {"id": "asset:tableau:exec-scorecard", "type": "report", "label": "Executive Scorecard", "tool": "tableau"},
    {"id": "kpi:revenue:v1", "type": "kpi", "label": "Revenue", "status": "active", "certification_level": "certified"}
  ],
  "edges": [
    {"id": "usage:123", "source": "kpi:revenue:v1", "target": "asset:tableau:exec-scorecard", "usage_type": "dashboard"}
  ],
  "meta": {"node_count": 2, "edge_count": 1}
}
```

## 8. Query Strategy (Performance-Oriented)

## 8.1 KPI -> Reports
```sql
select
    k.kpi_slug,
    k.kpi_version,
    k.kpi_name,
    k.status,
    k.certification_level,
    u.usage_id,
    u.consumer_tool,
    u.reference_name,
    u.reference_url,
    u.usage_type
from kpi_catalog.kpi_definition k
join kpi_catalog.kpi_usage u
  on k.kpi_slug = u.kpi_slug
 and k.kpi_version = u.kpi_version
where k.kpi_slug = :kpi_slug
  and k.kpi_version = cast(:kpi_version as integer)
order by u.created_at desc
limit cast(:max_edges as integer)
```

## 8.2 Report -> KPIs (fallback identity)
```sql
select
    u.usage_id,
    u.consumer_tool,
    u.reference_name,
    u.reference_url,
    u.usage_type,
    k.kpi_slug,
    k.kpi_version,
    k.kpi_name,
    k.status,
    k.certification_level
from kpi_catalog.kpi_usage u
join kpi_catalog.kpi_definition k
  on u.kpi_slug = k.kpi_slug
 and u.kpi_version = k.kpi_version
where lower(u.consumer_tool) = lower(:consumer_tool)
  and lower(u.reference_name) = lower(:reference_name)
order by k.kpi_slug, k.kpi_version
limit cast(:max_edges as integer)
```

## 9. Frontend Rendering Strategy
Recommended library: Cytoscape.js (good defaults + mature graph UX).

Render constraints:
- default max 60 nodes
- default max 120 edges
- show message if graph truncated

UI layout:
- search bar (KPI / report)
- graph canvas
- side panel with selected node details

Do not auto-load full graph on page open.

## 10. Performance Plan

## 10.1 Hard Limits
Enforce server-side limits from config:
- `LINEAGE_MAX_NODES` (default 60)
- `LINEAGE_MAX_EDGES` (default 120)
- `LINEAGE_SEARCH_LIMIT` (default 20)

## 10.2 Caching
Phase 1: in-process TTL cache (5 min) for API responses keyed by request params.
Phase 2: Redis cache shared across instances.

Cache keys:
- `lineage:kpi:<slug>:<version>`
- `lineage:report:<tool>:<reference_name>` or `lineage:report:<asset_id>`

## 10.3 Query Slimming
- Select only fields needed for graph and side panel.
- Avoid large text columns in lineage queries.
- Keep joins limited to `kpi_definition` + `kpi_usage` in phase 1.

## 10.4 Reduce Data API Overhead
- Reuse existing tuned poll interval (`DATA_API_POLL_INTERVAL_SEC`).
- Keep lineage API read queries short and bounded.
- Prefer one query per request (no N+1 query patterns).

## 10.5 Search UX
- Typeahead endpoint with debounce (250-300ms).
- Return top N matches only.
- Require minimum query length (e.g., 2 chars).

## 11. Security and Governance
- Restrict lineage APIs to authenticated internal users.
- Apply visibility filters if needed:
  - only active/certified KPIs for broad audiences
  - include draft/experimental only for governance roles
- Never expose secrets/internal SQL paths in payloads.

## 12. Rollout Phases

Phase 1 (MVP):
1. Flask lineage blueprint + APIs
2. KPI-centric and report-centric queries
3. Cytoscape neighborhood graph
4. hard limits + loading/error states

Phase 2:
1. search endpoints + typeahead
2. TTL cache
3. report identity hardening (`asset_id`)

Phase 3:
1. governance overlays (approver badges/status chips)
2. impact analysis actions
3. expanded filtering (tool/team/domain)

## 13. Success Metrics
- P95 lineage API latency < 1200ms (Data API environment)
- P95 graph render < 100ms for bounded graph sizes
- >= 95% requests within node/edge limits without timeout
- reduced incident triage time for KPI/report impact analysis

## 14. Risks and Mitigations
- Risk: Data API latency spikes
  - Mitigation: cache + strict limits + lightweight queries
- Risk: unstable report identity using `reference_name`
  - Mitigation: introduce `asset_id` column
- Risk: oversized graphs degrade UX
  - Mitigation: neighborhood-only rendering + truncation notices

## 15. Recommendation
Proceed with this feature as the next step, but implement it as a bounded, read-optimized Flask module first. Prioritize stable report identity and caching early to keep response time predictable as usage grows.
