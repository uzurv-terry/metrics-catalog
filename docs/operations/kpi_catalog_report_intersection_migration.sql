-- KPI Catalog migration: introduce report as a formal parent table,
-- convert kpi_usage toward a metric-to-report intersection model,
-- and update catalog_note to support notes on metric definitions and reports.
--
-- IMPORTANT
-- 1. Review this script before running it in Redshift.
-- 2. Redshift DDL is often auto-commit; do not assume transaction rollback behavior.
-- 3. This script is designed to move the schema toward the new target model
--    without immediately breaking the current Flask app.
-- 4. Do not drop the legacy report-identifying columns from kpi_usage
--    until the application has been refactored to use report_id.


-- ============================================================
-- 0. PRE-CHECKS
-- ============================================================

-- Review the current shape of the tables before applying changes.
select schemaname, tablename, "column", type, encoding, distkey, sortkey
from pg_table_def
where schemaname = 'kpi_catalog'
  and tablename in ('kpi_definition', 'kpi_usage', 'catalog_note', 'report')
order by tablename, sortkey desc, "column";

-- Check how many current usage rows exist.
select count(*) as usage_row_count
from kpi_catalog.kpi_usage;

-- If catalog_note already exists, inspect current note scopes.
-- Comment out if the table does not exist yet.
select note_scope, count(*) as note_count
from kpi_catalog.catalog_note
group by note_scope
order by note_scope;


-- ============================================================
-- 1. CREATE THE NEW REPORT TABLE
-- ============================================================

-- Formal downstream asset table.
-- One report/dashboard/app page should exist once here,
-- even if it uses multiple metrics.
create table if not exists kpi_catalog.report (
  report_id        bigint identity(1,1) not null,
  report_slug      varchar(255) not null,
  report_name      varchar(255) not null,
  report_type      varchar(50)  default 'dashboard',
  consumer_tool    varchar(100) not null,
  report_url       varchar(512),
  source_system    varchar(255),
  owner_person     varchar(255),
  owner_team       varchar(255),
  status           varchar(50)  default 'active',
  created_at       timestamp    default getdate(),
  updated_at       timestamp    default getdate(),
  primary key (report_id),
  unique (consumer_tool, report_slug)
)
diststyle key
distkey (report_slug)
sortkey (consumer_tool, report_slug, status);


-- ============================================================
-- 2. ALTER KPI_USAGE TOWARD AN INTERSECTION MODEL
-- ============================================================

-- Add the new report parent reference.
alter table kpi_catalog.kpi_usage
add column report_id bigint;

-- Add updated_at so future edits to usage metadata are auditable.
alter table kpi_catalog.kpi_usage
add column updated_at timestamp default getdate();

-- Optional informational foreign key.
-- Redshift treats foreign keys as informational, not strongly enforced OLTP constraints.
-- Uncomment if you want the metadata declared in the catalog.
--
-- alter table kpi_catalog.kpi_usage
-- add constraint fk_kpi_usage_report
-- foreign key (report_id)
-- references kpi_catalog.report(report_id);


-- ============================================================
-- 3. BACKFILL REPORT FROM DISTINCT LEGACY KPI_USAGE ROWS
-- ============================================================

-- Current kpi_usage rows contain report identity fields:
--   consumer_tool
--   reference_name
--   reference_url
--   source_system
--
-- This insert creates one formal report row per distinct legacy report identity.
-- The generated report_slug is deterministic and includes a hash suffix
-- to reduce collisions when names are similar.
insert into kpi_catalog.report (
  report_slug,
  report_name,
  report_type,
  consumer_tool,
  report_url,
  source_system,
  status,
  created_at,
  updated_at
)
select distinct
  trim(both '-' from regexp_replace(lower(coalesce(reference_name, 'report')), '[^a-z0-9]+', '-'))
    || '-'
    || substring(
         md5(
           coalesce(reference_name, '')
           || '|'
           || coalesce(reference_url, '')
           || '|'
           || coalesce(source_system, '')
           || '|'
           || coalesce(consumer_tool, '')
         ),
         1,
         8
       )                                                as report_slug,
  reference_name                                        as report_name,
  case
    when usage_type in ('dashboard', 'report') then usage_type
    when usage_type = 'api' then 'app_page'
    else 'dashboard'
  end                                                   as report_type,
  consumer_tool,
  reference_url                                         as report_url,
  source_system,
  'active'                                              as status,
  min(created_at) over (
    partition by
      reference_name,
      reference_url,
      source_system,
      consumer_tool,
      case
        when usage_type in ('dashboard', 'report') then usage_type
        when usage_type = 'api' then 'app_page'
        else 'dashboard'
      end
  )                                                     as created_at,
  getdate()                                             as updated_at
from kpi_catalog.kpi_usage;


-- ============================================================
-- 4. BACKFILL KPI_USAGE.REPORT_ID
-- ============================================================

-- Map each legacy usage row to its new report parent.
update kpi_catalog.kpi_usage u
set
  report_id = r.report_id,
  updated_at = getdate()
from kpi_catalog.report r
where r.consumer_tool = u.consumer_tool
  and r.report_slug =
      trim(both '-' from regexp_replace(lower(coalesce(u.reference_name, 'report')), '[^a-z0-9]+', '-'))
      || '-'
      || substring(
           md5(
             coalesce(u.reference_name, '')
             || '|'
             || coalesce(u.reference_url, '')
             || '|'
             || coalesce(u.source_system, '')
             || '|'
             || coalesce(u.consumer_tool, '')
           ),
           1,
           8
         );


-- ============================================================
-- 5. ALTER OR CREATE CATALOG_NOTE
-- ============================================================

-- CASE A: catalog_note already exists in the older metric/usage format.
-- Add report_id and widen note_scope to support:
--   metric_definition
--   report
--
-- If catalog_note does not already exist, skip this section and use CASE B below.
alter table kpi_catalog.catalog_note
add column report_id bigint;

alter table kpi_catalog.catalog_note
alter column note_scope type varchar(30);

-- Optional informational foreign key.
-- Uncomment if you want the metadata declared in the catalog.
--
-- alter table kpi_catalog.catalog_note
-- add constraint fk_catalog_note_report
-- foreign key (report_id)
-- references kpi_catalog.report(report_id);

-- Convert old metric scope value to the new explicit name.
update kpi_catalog.catalog_note
set note_scope = 'metric_definition'
where note_scope = 'metric';

-- Convert old usage notes to report notes by mapping usage_id -> report_id.
-- REVIEW THIS RESULT CAREFULLY.
-- Some existing usage notes may actually be relationship-specific rather than report-wide.
update kpi_catalog.catalog_note n
set
  report_id = u.report_id,
  note_scope = 'report',
  updated_at = getdate()
from kpi_catalog.kpi_usage u
where n.usage_id = u.usage_id
  and n.note_scope = 'usage';

-- Optional cleanup after you confirm all migrated notes are correct.
-- Do not run this until you are satisfied with the report_id backfill.
--
-- alter table kpi_catalog.catalog_note
-- drop column usage_id;


-- CASE B: catalog_note does not exist yet.
-- Run this instead of CASE A if you are creating the table from scratch.
--
-- create table if not exists kpi_catalog.catalog_note (
--   note_id            bigint identity(1,1) not null,
--   note_scope         varchar(30)  not null,  -- metric_definition | report
--   kpi_id             varchar(36),
--   kpi_slug           varchar(255),
--   kpi_version        integer,
--   report_id          bigint,
--   note_type          varchar(50)  default 'general',
--   note_title         varchar(255),
--   note_body          varchar(max) not null,
--   author_name        varchar(255) not null,
--   author_email       varchar(255),
--   is_active          boolean      default true,
--   created_at         timestamp    default getdate(),
--   updated_at         timestamp    default getdate(),
--   primary key (note_id),
--   foreign key (report_id) references kpi_catalog.report(report_id),
--   foreign key (kpi_id) references kpi_catalog.kpi_definition(kpi_id)
-- )
-- diststyle key
-- distkey (kpi_slug)
-- sortkey (note_scope, kpi_slug, kpi_version, report_id, created_at);


-- ============================================================
-- 6. OPTIONAL PHYSICAL TUNING UPDATES
-- ============================================================

-- Redshift sortkey changes can be expensive. Run only if you want to align
-- the physical table layout with the new target-state design.
--
-- alter table kpi_catalog.kpi_usage
-- alter sortkey (kpi_slug, kpi_version, report_id, usage_type);
--
-- alter table kpi_catalog.catalog_note
-- alter sortkey (note_scope, kpi_slug, kpi_version, report_id, created_at);


-- ============================================================
-- 7. POST-CHECKS
-- ============================================================

-- Verify report rows were created.
select count(*) as report_row_count
from kpi_catalog.report;

-- Verify every existing usage row now maps to a report.
select count(*) as usage_rows_missing_report_id
from kpi_catalog.kpi_usage
where report_id is null;

-- Review report distribution by tool and type.
select consumer_tool, report_type, count(*) as report_count
from kpi_catalog.report
group by consumer_tool, report_type
order by consumer_tool, report_type;

-- Review notes after scope migration.
-- Comment out if catalog_note does not exist.
select note_scope, count(*) as note_count
from kpi_catalog.catalog_note
group by note_scope
order by note_scope;

-- Review any notes that still have no valid parent after migration.
-- Comment out if catalog_note does not exist.
select *
from kpi_catalog.catalog_note
where
  (note_scope = 'metric_definition' and (kpi_id is null or kpi_slug is null or kpi_version is null))
  or
  (note_scope = 'report' and report_id is null);


-- ============================================================
-- 8. DEFERRED CLEANUP: DO NOT RUN UNTIL THE APP IS REFACTORED
-- ============================================================

-- The current Flask app still reads these legacy fields from kpi_usage.
-- Leave them in place until the code has been updated to read report_id
-- and join to kpi_catalog.report.
--
-- alter table kpi_catalog.kpi_usage drop column consumer_tool;
-- alter table kpi_catalog.kpi_usage drop column reference_name;
-- alter table kpi_catalog.kpi_usage drop column reference_url;
-- alter table kpi_catalog.kpi_usage drop column source_system;
-- alter table kpi_catalog.kpi_usage drop column context_notes;
