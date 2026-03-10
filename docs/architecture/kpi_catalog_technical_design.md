# KPI Catalog – Technical Design (Redshift + Semantic Layer)

## Objective

Design a scalable, governed KPI metadata system in Redshift that:

* Separates KPI definition from KPI usage
* Supports strict versioning
* Enables semantic materialization
* Enforces BI consumption through governed outputs
* Implements catalog-driven governance and CI enforcement

---

# 1. High-Level Architecture

The KPI system is composed of four layers:

1. **Metadata Layer** → `kpi_catalog` schema (definitions + usage)
2. **Execution Layer** → dbt / SQL models implementing KPI logic
3. **Semantic Output Layer** → `semantic.kpi_values_*` tables/views
4. **Consumption Layer** → Tableau (restricted to semantic schema)

```
RAW → ENRICHED → REPORTING → SEMANTIC (KPI outputs) → TABLEAU
                 ↑
           KPI CATALOG (contract layer)
```

The catalog acts as the **control plane**. All KPI execution artifacts must map to a catalog entry.

---

# 2. Schema Definition

```sql
CREATE SCHEMA IF NOT EXISTS kpi_catalog;
```

---

# 3. KPI Definition Table

## `kpi_catalog.kpi_definition`

This table stores the authoritative KPI **contract**: identity, business meaning, calculation semantics, governance, lineage, SLAs, and versioning.

**Key design choice:** Presentation/consumption details (dashboards, preferred dimensions, tool-specific visualization hints) are *not* stored here, because a KPI can be consumed in multiple tools and contexts with different visualization needs.

```sql
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
```


# 4. KPI Usage Table

## `kpi_catalog.kpi_usage`

This table tracks **where and how** a KPI is consumed (dashboards, reports, extracts, applications), including **presentation hints** that vary by context.

This is where dashboard/report-specific fields belong because:

- the same KPI can appear in many dashboards/tools,
- each usage may have different preferred dimensions/filters,
- row-level security and presentation can differ by audience.

```sql
CREATE TABLE IF NOT EXISTS kpi_catalog.kpi_usage (
  usage_id        BIGINT IDENTITY(1,1) NOT NULL,
  kpi_id          VARCHAR(36)  NOT NULL,
  kpi_slug        VARCHAR(255) NOT NULL,
  kpi_version     INTEGER      NOT NULL,

  -- Usage identity
  usage_type      VARCHAR(50),   -- dashboard | report | extract | api | notebook
  consumer_tool   VARCHAR(100),  -- tableau | looker | powerbi | internal_app | etc.
  reference_name  VARCHAR(255) NOT NULL,
  reference_url   VARCHAR(512),

  -- Context & mapping
  source_system   VARCHAR(255),  -- if the KPI is mirrored into another metric system
  context_notes   VARCHAR(MAX),

  -- Presentation / consumption (context-specific)
  default_chart_type      VARCHAR(100),
  approved_visualizations VARCHAR(MAX),
  preferred_dimensions    VARCHAR(MAX),
  preferred_filters       SUPER,
  row_level_security_notes VARCHAR(MAX),

  -- Audit
  created_at      TIMESTAMP DEFAULT GETDATE(),

  PRIMARY KEY (usage_id)
)
DISTSTYLE KEY
DISTKEY (kpi_slug)
SORTKEY (kpi_slug, kpi_version, consumer_tool, usage_type, reference_name);
```


### Why Separate Usage?

- Avoids repeating dashboard references inside KPI definition rows
- Enables many-to-one relationships
- Supports impact analysis
- Enables deprecation management

---

# 5. Semantic KPI Output Layer

Governed KPI outputs must be materialized from catalog definitions.

Example daily semantic table:

```sql
CREATE TABLE semantic.kpi_values_day (
  kpi_slug          VARCHAR(255),
  kpi_version       INTEGER,
  as_of_date        DATE,
  market_key        VARCHAR(50),
  state_key         VARCHAR(50),
  numerator_value   DECIMAL(18,6),
  denominator_value DECIMAL(18,6),
  kpi_value         DECIMAL(18,6),
  refresh_ts        TIMESTAMP,
  source_run_id     VARCHAR(50)
)
DISTSTYLE AUTO
SORTKEY (kpi_slug, as_of_date);
````

All BI tools must read from `semantic.*` only.

---

# 6. Access Enforcement Model

## Role-Based Access

* Tableau role: `SELECT` on `semantic.*`
* No Tableau access to `raw`, `enriched`, or unrestricted reporting tables
* Only `active + certified` KPIs are published

---

# 7. Versioning Rules

| Change Type         | Action                 |
| ------------------- | ---------------------- |
| Filter logic change | Major version bump     |
| Grain change        | Major version bump     |
| New dimension added | Minor bump             |
| Description update  | Patch                  |
| Deprecation         | Set effective_end_date |

Dashboards must filter on:

```sql
effective_end_date IS NULL
AND status = 'active'
AND certification_level = 'certified'
```

---

# 8. CI / Governance Gates

For every KPI change:

* Validate required metadata fields
* Validate SQL compiles
* Validate source tables are approved
* Enforce version bump for breaking changes
* Require change_reason
* Regenerate semantic views
* Reject uncataloged KPIs

---

# 9. Design Philosophy

KPIs are:

* Versioned data products
* Governed semantic contracts
* Executable metadata
* Observable assets
* Organizational alignment mechanisms

The KPI catalog becomes the **control plane for executive trust**.

---

# 10. Best-Practice Assessment: Definition vs Usage

Separating **KPI definition** from **KPI usage/presentation** aligns with common semantic-layer and metrics-governance patterns:

* A semantic layer/metrics store aims to define metrics once (logic, grain, filters) and expose them to many endpoints (BI tools, notebooks, apps). This implies the metric definition should be **tool-agnostic**, while consumption details live closer to the endpoint.
* Dashboard logic should not be the place where business logic is stored; dashboards should visualize, not own the SQL/metric definitions.
* Downstream “where it’s used” metadata is often modeled separately (e.g., dbt **Exposures** are explicitly for downstream usage such as dashboards/apps, distinct from metric definitions).

In this design:

* `kpi_definition` = the contract (business + semantic definition + governance + lineage + SLA + version)
* `kpi_usage` = downstream usage graph + tool-specific mapping + presentation hints + RLS notes

---

# 11. Sources

The following public sources reflect and support the approach of keeping metric definitions centralized and tool-agnostic, and treating downstream dashboard/report usage separately:

* dbt Labs – Semantic Layer introduction: [https://www.getdbt.com/blog/semantic-layer-introduction](https://www.getdbt.com/blog/semantic-layer-introduction)
* Medium (overview of dbt semantic layer benefits): [https://medium.com/%40aashnasahni10/meet-dbt-clouds-semantic-layer-what-it-solves-and-what-it-doesn-t-43deb7abd5dc](https://medium.com/%40aashnasahni10/meet-dbt-clouds-semantic-layer-what-it-solves-and-what-it-doesn-t-43deb7abd5dc)
* MetricLayer – Modern semantic layer playbook (centralize metrics across BI tools): [https://www.metriclayer.dev/semantic-layer/](https://www.metriclayer.dev/semantic-layer/)
* dbt Cloud metadata patterns (Exposures vs Metrics vs Semantic Layer – downstream usage modeled separately): [https://zenn.dev/chi_xing/articles/1af8c01c102d11](https://zenn.dev/chi_xing/articles/1af8c01c102d11)
* Looker (LookML concepts; measures/dimensions live in the modeling layer, not dashboards): [https://cloud.google.com/looker/docs/lookml-terms-and-concepts](https://cloud.google.com/looker/docs/lookml-terms-and-concepts)
