# Metric Overview and Notes Solution

## Purpose
This document describes two additions to the metrics catalog application:

1. a single-pane metric overview page
2. a new notes table that can attach to either a metric definition or a report

The target-state design for notes assumes this storage contract:
- `kpi_catalog.kpi_definition`
- `kpi_catalog.report`
- `kpi_catalog.kpi_usage`

The product language in the UI shifts from "KPI" to "Metric", while the physical tables remain in the `kpi_catalog` schema.

## 1. Metric Overview Page

## Goal
Provide a single page that shows the full story of one metric version without forcing the user to navigate between multiple forms or tables.

## Route
Recommended route in the current Flask app:
- `/kpi-definitions/overview`

Even though the route remains under `kpi-definitions`, the user-facing page title should be "Metric Overview".
The page should support search-first loading by `kpi_slug` and `kpi_version` query parameters.

## What the page should show
In one pane, the page should show:
- metric name
- formula
- business question
- business definition
- status
- certification level
- owner details
- documentation location
- effective dates
- all report/dashboard/app usage rows tied to the metric version
- report-level notes relevant to those downstream assets

## Data sources

### Metric definition source
Read from:
- `kpi_catalog.kpi_definition`

By:
- `kpi_slug`
- `kpi_version`

### Usage source
Read from:
- `kpi_catalog.kpi_usage`
- `kpi_catalog.report`

By joining:
- `kpi_usage.report_id = report.report_id`
- `kpi_usage.kpi_slug`
- `kpi_usage.kpi_version`

## Rendering approach
The page should use a read-only detail layout rather than an edit form.
It should begin with a search section and only render metric details after a selection is loaded.

Recommended sections:
- header with name, id, slug, version, status, certification
- formula block
- business question block
- business definition block
- report/usage list
- side detail panel with owner/governance metadata

## Why this page matters
- improves discoverability of one metric’s complete context
- reduces navigation friction
- gives analysts and approvers a read-first page before making edits
- creates a natural anchor page for future notes, approvals, and audit history

## 2. Notes Table Requirement

## Goal
Support free-form structured notes that can be attached to either:
- a metric definition
- a report

This covers common operational needs such as:
- caveats
- migration notes
- dashboard warnings
- semantic concerns
- temporary exceptions
- business context not appropriate for the core metric contract

## Design choice
Add one shared notes table instead of separate metric-note and usage-note tables.

Recommended table name:
- `kpi_catalog.catalog_note`

This avoids creating user-facing "KPI" terminology in the table name while still living inside the existing `kpi_catalog` schema.

## Table responsibilities
The notes table should:
- support notes on a metric definition
- support notes on a report
- preserve author and timestamps
- support multiple notes per parent record
- allow note categorization

## Recommended DDL

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

## Important Redshift note
In Redshift, foreign keys are informational and not fully enforced like an OLTP database.

That means the application must enforce note integrity explicitly.

## Required application rules

### Rule 1: exactly one parent target
A note must belong to one of these:
- a metric definition
- a report

It must not belong to both at once.

Recommended enforcement:
- if `note_scope = 'metric_definition'`, require `kpi_id + kpi_slug + kpi_version` and require `report_id` to be null
- if `note_scope = 'report'`, require `report_id` and require metric identity fields to be null

### Rule 2: metric identity must be valid
If the note is attached to a metric:
- the referenced metric identity must exist in `kpi_definition`

### Rule 3: report identity must be valid
If the note is attached to a report:
- the referenced `report_id` must exist in `report`

### Rule 4: note body required
Do not allow empty notes.

### Rule 5: preserve auditability
Notes should be additive by default.
If a note is no longer relevant, prefer:
- `is_active = false`

instead of destructive deletion.

## Why one shared notes table is better
- simpler UI and service logic
- one audit model
- one pattern for metric-definition and report annotations
- easier to extend later to approvals, lineage assets, or semantic outputs

## 3. UI Direction for Notes

## Metric Definition page
Future enhancement:
- allow adding notes directly from the metric definition workspace
- show a recent notes panel or count

## Metric Usage page
Future enhancement:
- show the linked report and report-level notes
- keep usage-specific display metadata on the intersection row

## Metric Overview page
Best long-term home for notes:
- show all active metric-level notes
- optionally group report notes by report/dashboard

This makes the overview page the main read surface for the metric’s full context.

## 4. Implementation Recommendation

## Phase 1
Implemented / in scope now:
- single-pane metric overview page
- user-facing terminology shift from KPI to Metric in the app UI

## Phase 2
Next build:
- add `catalog_note` table
- add repository, service, and form support for notes
- surface notes on metric overview and report detail flows

## 5. Summary
The right solution is:
- use "Metric" as the application language
- add a read-first metric overview page
- add one shared notes table that can attach to either the metric definition or the report

This gives the catalog a cleaner target-state note model while making the metric overview easier to read, annotate, and govern.
