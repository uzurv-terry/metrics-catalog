# KPI Approver Table Design

## Purpose
Track approvers associated with specific KPI versions so approval events are stored as structured metadata instead of only free-text fields.

## Table

```sql
CREATE TABLE IF NOT EXISTS kpi_catalog.kpi_approver (
  approver_id      BIGINT IDENTITY(1,1) NOT NULL,
  kpi_id           VARCHAR(36)  NOT NULL,
  kpi_slug         VARCHAR(255) NOT NULL,
  kpi_version      INTEGER      NOT NULL,

  approver_name    VARCHAR(255) NOT NULL,
  approver_email   VARCHAR(255),
  approver_role    VARCHAR(100) NOT NULL,
  approval_notes   VARCHAR(MAX),

  approved_at      TIMESTAMP    DEFAULT GETDATE(),
  created_at       TIMESTAMP    DEFAULT GETDATE(),

  PRIMARY KEY (approver_id)
)
DISTSTYLE KEY
DISTKEY (kpi_slug)
SORTKEY (kpi_slug, kpi_version, approver_name, approved_at);
```

## Notes
- App validates that referenced KPI identity exists (`kpi_id + kpi_slug + kpi_version`).
- App prevents duplicate `approver_name` for the same KPI version.
- Add this DDL in Redshift before using the KPI Approvers page.
