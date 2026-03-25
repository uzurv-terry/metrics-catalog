# KPI Catalog Three-Table Design: Metric Definition, Report, and Usage Intersection

## Objective
Evolve the catalog from the current two-table model into a cleaner three-table model:

- `kpi_catalog.kpi_definition`: the metric contract
- `kpi_catalog.report`: the formal report/dashboard/application asset
- `kpi_catalog.kpi_usage`: the intersection between a metric version and a report

This separates report identity from metric-to-report usage details and creates a cleaner parent model for shared report notes.

## Why Change the Model

The current `kpi_usage` table mixes two responsibilities:

1. report identity
2. metric-in-report usage details

That leads to duplicated report metadata whenever the same report uses multiple metrics. It also makes notes awkward, because some notes belong to the report itself while others belong to the metric definition.

The cleaner model is:

- `kpi_definition`: what the metric is
- `report`: where users consume it
- `kpi_usage`: how that specific metric version is represented inside that report

## Target Tables

## 1. Metric Definition

`kpi_catalog.kpi_definition` remains the authoritative metric-definition table.

Notes support requirement:
- metric definition notes attach through `kpi_catalog.catalog_note`
- notes are version-aware and must reference `kpi_id + kpi_slug + kpi_version`

No new inline note columns are required on `kpi_definition`.

## 2. Report

`kpi_catalog.report` becomes the formal parent table for downstream assets such as dashboards, reports, workbooks, and internal app pages.

Recommended DDL:

```sql
CREATE TABLE IF NOT EXISTS kpi_catalog.report (
  report_id        BIGINT IDENTITY(1,1) NOT NULL,
  report_slug      VARCHAR(255) NOT NULL,
  report_name      VARCHAR(255) NOT NULL,
  report_type      VARCHAR(50)  DEFAULT 'dashboard',  -- dashboard | report | workbook | app_page
  consumer_tool    VARCHAR(100) NOT NULL,             -- tableau | powerbi | looker | internal_app | etc.
  report_url       VARCHAR(512),
  source_system    VARCHAR(255),
  owner_person     VARCHAR(255),
  owner_team       VARCHAR(255),
  status           VARCHAR(50)  DEFAULT 'active',
  created_at       TIMESTAMP    DEFAULT GETDATE(),
  updated_at       TIMESTAMP    DEFAULT GETDATE(),

  PRIMARY KEY (report_id),
  UNIQUE (consumer_tool, report_slug)
)
DISTSTYLE KEY
DISTKEY (report_slug)
SORTKEY (consumer_tool, report_slug, status);
```

Notes support requirement:
- report-level notes attach through `kpi_catalog.catalog_note`
- report notes belong to the report asset, not to one specific metric usage row

## 3. KPI Usage as an Intersection Table

`kpi_catalog.kpi_usage` should become a pure intersection between a metric definition version and a report.

Recommended DDL:

```sql
CREATE TABLE IF NOT EXISTS kpi_catalog.kpi_usage (
  usage_id                  BIGINT IDENTITY(1,1) NOT NULL,
  kpi_id                    VARCHAR(36)  NOT NULL,
  kpi_slug                  VARCHAR(255) NOT NULL,
  kpi_version               INTEGER      NOT NULL,
  report_id                 BIGINT       NOT NULL,

  -- Metric-in-report usage details
  usage_type                VARCHAR(50),   -- card | chart | table | filter | export | api_output
  default_chart_type        VARCHAR(100),
  approved_visualizations   VARCHAR(MAX),
  preferred_dimensions      VARCHAR(MAX),
  preferred_filters         SUPER,
  row_level_security_notes  VARCHAR(MAX),

  created_at                TIMESTAMP DEFAULT GETDATE(),
  updated_at                TIMESTAMP DEFAULT GETDATE(),

  PRIMARY KEY (usage_id),
  FOREIGN KEY (report_id) REFERENCES kpi_catalog.report(report_id)
)
DISTSTYLE KEY
DISTKEY (kpi_slug)
SORTKEY (kpi_slug, kpi_version, report_id, usage_type);
```

### What moves out of `kpi_usage`

These current columns belong on `report`, not on the intersection:

- `consumer_tool`
- `reference_name`
- `reference_url`
- `source_system`

These should not remain on `kpi_usage` if it is truly the intersection table.

### What should be reconsidered

`context_notes` currently lives on `kpi_usage`.

Under the new model, it should usually move out of the intersection because:
- report-wide notes belong on `catalog_note` with `note_scope = 'report'`
- metric-definition notes belong on `catalog_note` with `note_scope = 'metric_definition'`

If the team later discovers a real need for relationship-specific notes, add a third `note_scope = 'usage'` intentionally. Do not keep it by accident.

## Updated Notes Table

`catalog_note` should be updated so it attaches to either:

- a metric definition version
- a report

Recommended DDL:

```sql
CREATE TABLE IF NOT EXISTS kpi_catalog.catalog_note (
  note_id            BIGINT IDENTITY(1,1) NOT NULL,

  note_scope         VARCHAR(30)  NOT NULL,  -- 'metric_definition' or 'report'

  kpi_id             VARCHAR(36),
  kpi_slug           VARCHAR(255),
  kpi_version        INTEGER,

  report_id          BIGINT,

  note_type          VARCHAR(50)  DEFAULT 'general',
  note_title         VARCHAR(255),
  note_body          VARCHAR(MAX) NOT NULL,

  author_name        VARCHAR(255) NOT NULL,
  author_email       VARCHAR(255),

  is_active          BOOLEAN      DEFAULT TRUE,
  created_at         TIMESTAMP    DEFAULT GETDATE(),
  updated_at         TIMESTAMP    DEFAULT GETDATE(),

  PRIMARY KEY (note_id),
  FOREIGN KEY (report_id) REFERENCES kpi_catalog.report(report_id),
  FOREIGN KEY (kpi_id) REFERENCES kpi_catalog.kpi_definition(kpi_id)
)
DISTSTYLE KEY
DISTKEY (kpi_slug)
SORTKEY (note_scope, kpi_slug, kpi_version, report_id, created_at);
```

## Required Application Rules for `catalog_note`

### Rule 1: exactly one parent target

A note must belong to one of these:

- a metric definition version
- a report

It must not belong to both at once.

### Rule 2: metric-definition scope requirements

If `note_scope = 'metric_definition'`:

- require `kpi_id`
- require `kpi_slug`
- require `kpi_version`
- require `report_id` to be null

### Rule 3: report scope requirements

If `note_scope = 'report'`:

- require `report_id`
- require `kpi_id`, `kpi_slug`, and `kpi_version` to be null

### Rule 4: note body required

Do not allow empty notes.

### Rule 5: additive audit behavior

Notes should be additive by default. Prefer `is_active = false` over destructive deletion.

## Query Shape Changes

## Metric Overview

The overview page should now load report usage through a join:

```sql
select
  u.usage_id,
  u.kpi_id,
  u.kpi_slug,
  u.kpi_version,
  u.usage_type,
  u.default_chart_type,
  u.approved_visualizations,
  u.preferred_dimensions,
  u.row_level_security_notes,
  r.report_id,
  r.report_name,
  r.report_slug,
  r.report_type,
  r.consumer_tool,
  r.report_url,
  r.source_system
from kpi_catalog.kpi_usage u
join kpi_catalog.report r
  on r.report_id = u.report_id
where u.kpi_slug = :kpi_slug
  and u.kpi_version = :kpi_version
order by r.consumer_tool, r.report_name;
```

## Report Detail / Report Notes

Report-level notes should be retrieved by `report_id`, not by `usage_id`.

## Migration Plan from the Current Model

1. Create `kpi_catalog.report`.
2. Backfill distinct report assets from current `kpi_usage` rows.
   Use current fields:
   - `reference_name -> report_name`
   - derived slug -> `report_slug`
   - `consumer_tool -> consumer_tool`
   - `reference_url -> report_url`
   - `source_system -> source_system`
3. Add `report_id` to `kpi_usage`.
4. Backfill `kpi_usage.report_id` by joining to the new `report` table.
5. Migrate note usage:
   - metric notes remain metric-definition notes
   - report notes use `report_id`
   - existing `context_notes` should be reviewed before migration because some may be report-wide and some may actually be usage-specific
6. Remove duplicated report identity columns from `kpi_usage` only after backfill is validated.

## Application Impact

The current app code does not yet implement the `report` table or `catalog_note` flow. To align the application with this design:

1. Add `Report` domain model, DTO, repository, service, form, and list/create/edit UI.
2. Refactor `KpiUsage` so it references `report_id` and only stores intersection-specific metadata.
3. Update overview/lineage queries to join `kpi_usage` to `report`.
4. Add notes UI and service logic using the new `catalog_note` parent rules.
5. Migrate existing `kpi_usage` form copy from "Dashboard or Report Name" to selecting a formal report record.

## Summary

The target model should be:

- `kpi_definition` = metric contract
- `report` = formal downstream asset
- `kpi_usage` = metric-to-report intersection
- `catalog_note` = notes attached to either metric definitions or reports

That is the cleanest way to avoid duplicated report metadata and to give notes a stable parent model.
