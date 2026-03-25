# KPI Catalog Two-Table Design (Historical Reference)

> This document reflects the earlier two-table model.
> The proposed target-state design with a formal `report` table is documented in `kpi_catalog_report_intersection_design.md`.

## Objective
Model KPI governance with two Redshift tables:
- `kpi_catalog.kpi_definition` for the KPI contract.
- `kpi_catalog.kpi_usage` for downstream usage and presentation context.

This aligns with `kpi_catalog_technical_design.md` and keeps definitions tool-agnostic while supporting many usage contexts.

## Architectural Position
- Metadata layer: `kpi_catalog.*`
- Execution layer: dbt/SQL KPI logic
- Semantic output layer: `semantic.kpi_values_*`
- Consumption layer: BI tools restricted to semantic outputs

## Canonical DDL

```sql
CREATE SCHEMA IF NOT EXISTS kpi_catalog;

CREATE TABLE IF NOT EXISTS kpi_catalog.kpi_definition (
  -- Identity
  kpi_id                     VARCHAR(36)   NOT NULL,
  kpi_name                   VARCHAR(255)  NOT NULL,
  kpi_slug                   VARCHAR(255)  NOT NULL,
  kpi_version                INTEGER       NOT NULL DEFAULT 1,

  -- Business context
  business_definition        VARCHAR(MAX)  NOT NULL,
  business_question          VARCHAR(MAX),
  primary_use_case           VARCHAR(255),
  decision_owner             VARCHAR(255),
  success_direction          VARCHAR(50) DEFAULT 'higher_is_better',

  -- Ownership & governance
  owner_person               VARCHAR(255)  NOT NULL,
  owner_team                 VARCHAR(255)  NOT NULL,
  steward_person             VARCHAR(255),
  owning_department          VARCHAR(255),
  consuming_departments      VARCHAR(MAX),
  status                     VARCHAR(50) DEFAULT 'draft',
  certification_level        VARCHAR(50) DEFAULT 'experimental',

  -- Classification
  metric_type                VARCHAR(100),
  metric_level               VARCHAR(100),
  leading_or_lagging         VARCHAR(50) DEFAULT 'neutral',
  time_grain_supported       VARCHAR(MAX),
  tags                       VARCHAR(MAX),

  -- Calculation semantics
  formula                    VARCHAR(MAX) NOT NULL,
  numerator_definition       VARCHAR(MAX),
  denominator_definition     VARCHAR(MAX),
  filter_conditions          SUPER,
  null_handling_rules        VARCHAR(MAX),
  rounding_rules             VARCHAR(255),
  windowing_logic            VARCHAR(255),
  known_caveats              VARCHAR(MAX),
  unit_of_measure            VARCHAR(100),

  -- Lineage
  documentation_url          VARCHAR(512),
  metric_query_reference     VARCHAR(512),
  source_systems             VARCHAR(MAX),
  source_objects             SUPER,
  transformation_layer       VARCHAR(100),
  upstream_dependencies      SUPER,

  -- Reliability
  expected_update_frequency  VARCHAR(100),
  data_latency_sla_minutes   INTEGER,
  completeness_threshold     DECIMAL(5,2),
  last_successful_refresh_ts TIMESTAMP,
  reliability_notes          VARCHAR(MAX),

  -- Versioning
  effective_start_date       DATE DEFAULT CURRENT_DATE,
  effective_end_date         DATE,
  change_reason              VARCHAR(MAX),
  breaking_change_flag       BOOLEAN DEFAULT FALSE,
  supersedes_kpi_id          VARCHAR(36),

  -- Review
  review_cadence             VARCHAR(50),
  last_reviewed_date         DATE,

  -- Audit
  created_at                 TIMESTAMP DEFAULT GETDATE(),
  updated_at                 TIMESTAMP DEFAULT GETDATE(),

  PRIMARY KEY (kpi_id),
  UNIQUE (kpi_slug, kpi_version)
)
DISTSTYLE KEY
DISTKEY (kpi_slug)
SORTKEY (kpi_slug, kpi_version, status, certification_level);


CREATE TABLE IF NOT EXISTS kpi_catalog.kpi_usage (
  usage_id         BIGINT IDENTITY(1,1) NOT NULL,
  kpi_id           VARCHAR(36)  NOT NULL,
  kpi_slug         VARCHAR(255) NOT NULL,
  kpi_version      INTEGER      NOT NULL,

  -- Usage identity
  usage_type       VARCHAR(50),
  consumer_tool    VARCHAR(100),
  reference_name   VARCHAR(255) NOT NULL,
  reference_url    VARCHAR(512),

  -- Context & mapping
  source_system    VARCHAR(255),
  context_notes    VARCHAR(MAX),

  -- Presentation / consumption
  default_chart_type       VARCHAR(100),
  approved_visualizations  VARCHAR(MAX),
  preferred_dimensions     VARCHAR(MAX),
  preferred_filters        SUPER,
  row_level_security_notes VARCHAR(MAX),

  -- Audit
  created_at       TIMESTAMP DEFAULT GETDATE(),

  PRIMARY KEY (usage_id)
)
DISTSTYLE KEY
DISTKEY (kpi_slug)
SORTKEY (kpi_slug, kpi_version, consumer_tool, usage_type, reference_name);
```

## Why This Split
- `kpi_definition` stays stable and tool-agnostic.
- `kpi_usage` captures variable downstream usage contexts.
- One KPI can map to many dashboards/reports/apps without definition duplication.

## Governance and Enforcement
- Only `active + certified` KPI definitions should be eligible for executive semantic publication.
- BI tools should read semantic outputs only, not raw/reporting tables.
- CI gates should validate metadata completeness, SQL validity, lineage, and versioning.

## Practical Implementation Notes
- Redshift key constraints are not sufficient as sole integrity enforcement; enforce referential checks for both `kpi_id` and (`kpi_slug`, `kpi_version`) in service/ETL logic.
- Prefer storing `updated_at`/`updated_by` on both tables if frequent catalog edits are expected.
