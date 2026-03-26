-- Import Dashboard Data Definitions.xlsx / Summary into the existing KPI catalog tables.
-- Mapping used in this script:
--   Organization -> kpi_definition.owner_team / owning_department
--   Metric       -> kpi_definition.kpi_name
--   Definition   -> kpi_definition.business_definition
--   Formula      -> kpi_definition.formula
--   Workbook     -> report + kpi_usage

create schema if not exists kpi_catalog;

create table if not exists kpi_catalog.kpi_definition (
  kpi_id                     varchar(36)   not null,
  kpi_name                   varchar(255)  not null,
  kpi_slug                   varchar(255)  not null,
  kpi_version                integer       not null default 1,
  business_definition        varchar(max)  not null,
  business_question          varchar(max),
  primary_use_case           varchar(255),
  decision_owner             varchar(255),
  success_direction          varchar(50) default 'higher_is_better',
  owner_person               varchar(255)  not null,
  owner_team                 varchar(255)  not null,
  steward_person             varchar(255),
  owning_department          varchar(255),
  consuming_departments      varchar(max),
  status                     varchar(50) default 'draft',
  certification_level        varchar(50) default 'experimental',
  metric_type                varchar(100),
  metric_level               varchar(100),
  leading_or_lagging         varchar(50) default 'neutral',
  time_grain_supported       varchar(max),
  tags                       varchar(max),
  formula                    varchar(max) not null,
  numerator_definition       varchar(max),
  denominator_definition     varchar(max),
  filter_conditions          super,
  null_handling_rules        varchar(max),
  rounding_rules             varchar(255),
  windowing_logic            varchar(255),
  known_caveats              varchar(max),
  unit_of_measure            varchar(100),
  documentation_url          varchar(512),
  metric_query_reference     varchar(512),
  source_systems             varchar(max),
  source_objects             super,
  transformation_layer       varchar(100),
  upstream_dependencies      super,
  expected_update_frequency  varchar(100),
  data_latency_sla_minutes   integer,
  completeness_threshold     decimal(5,2),
  last_successful_refresh_ts timestamp,
  reliability_notes          varchar(max),
  effective_start_date       date default current_date,
  effective_end_date         date,
  change_reason              varchar(max),
  breaking_change_flag       boolean default false,
  supersedes_kpi_id          varchar(36),
  review_cadence             varchar(50),
  last_reviewed_date         date,
  created_at                 timestamp default getdate(),
  updated_at                 timestamp default getdate(),
  primary key (kpi_id),
  unique (kpi_slug, kpi_version)
)
diststyle key
distkey (kpi_slug)
sortkey (kpi_slug, kpi_version, status, certification_level);

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

create table if not exists kpi_catalog.kpi_usage (
  usage_id                  bigint identity(1,1) not null,
  kpi_id                    varchar(36)  not null,
  kpi_slug                  varchar(255) not null,
  kpi_version               integer      not null,
  report_id                 bigint       not null,
  usage_type                varchar(50),
  default_chart_type        varchar(100),
  approved_visualizations   varchar(max),
  preferred_dimensions      varchar(max),
  preferred_filters         super,
  row_level_security_notes  varchar(max),
  created_at                timestamp default getdate(),
  updated_at                timestamp default getdate(),
  primary key (usage_id)
)
diststyle key
distkey (kpi_slug)
sortkey (kpi_slug, kpi_version, report_id, usage_type);

insert into kpi_catalog.report (
  report_slug, report_name, report_type, consumer_tool,
  report_url, source_system, owner_person, owner_team, status
)
select
  'dashboard-data-definitions-summary',
  'Dashboard Data Definitions.xlsx - Summary',
  'workbook',
  'excel',
  null,
  'excel_workbook',
  null,
  null,
  'active'
where not exists (
  select 1
  from kpi_catalog.report
  where consumer_tool = 'excel'
    and report_slug = 'dashboard-data-definitions-summary'
);

insert into kpi_catalog.kpi_definition (
  kpi_id, kpi_name, kpi_slug, kpi_version,
  business_definition, owner_person, owner_team, owning_department,
  status, certification_level, formula, metric_query_reference
)
with source_rows as (
  select 2 as source_row_number, 'Client Services' as organization_name, 'Assigned Rides' as metric_name, 'All scheduled and on-demand rides. If "Include Unactivated Will Calls" is selected above, on-demand Will Call rides that entered our system but were never activated by the rider will be included in the total ride population.' as definition_text, 'COUNT(Assigned Rides)' as formula_text
  union all select 3 as source_row_number, 'Client Services' as organization_name, 'Completed Rides' as metric_name, 'All assigned rides that were ultimately marked as "completed"' as definition_text, 'COUNT(Completed Rides)' as formula_text
  union all select 4 as source_row_number, 'Client Services' as organization_name, '% Completed' as metric_name, 'The percentage of assigned rides that were completed' as definition_text, 'COUNT(Completed Rides) / COUNT(Assigned Rides)' as formula_text
  union all select 5 as source_row_number, 'Client Services' as organization_name, 'Available Rides' as metric_name, 'All assigned rides that did not have one of the following cancellations: "Rider cancelled", "Rider no show", "Rider ride limit reached", "Rider eligibility expired", "Rider marked as ineligible", "Ride reassigned", "Ride modified", "Lyft rider no show", "Incident during ride"' as definition_text, 'COUNT(Available Rides)' as formula_text
  union all select 6 as source_row_number, 'Client Services' as organization_name, '% Available ' as metric_name, 'The percentage of assigned rides that were available' as definition_text, 'COUNT(Available Rides) / COUNT(Assigned Rides)' as formula_text
  union all select 7 as source_row_number, 'Client Services' as organization_name, 'Accepted Rides' as metric_name, 'All assigned rides that weren''t returned' as definition_text, 'COUNT(Accepted Rides)' as formula_text
  union all select 8 as source_row_number, 'Client Services' as organization_name, '% Accepted' as metric_name, 'The percentage of assigned rides that were accepted ' as definition_text, 'COUNT(Accepted Rides) / COUNT(Assigned Rides)' as formula_text
  union all select 9 as source_row_number, 'Client Services' as organization_name, 'Returned Rides' as metric_name, 'All assigned rides that resulted in a "No driver interest" cancellation reason' as definition_text, 'COUNT(Returned Rides)' as formula_text
  union all select 10 as source_row_number, 'Client Services' as organization_name, '% Returned' as metric_name, 'The percentage of assigned rides that were returned' as definition_text, 'COUNT(Returned Rides) / COUNT(Assigned Rides)' as formula_text
  union all select 11 as source_row_number, 'Client Services' as organization_name, 'Rider Cancellations' as metric_name, 'All assigned rides that had a cancellation reason of "Rider cancelled"' as definition_text, 'COUNT(Rider Cancellations)' as formula_text
  union all select 12 as source_row_number, 'Client Services' as organization_name, '% Rider Cancelled' as metric_name, 'The percentage of assigned rides that had rider cancellations' as definition_text, 'COUNT(Rider Cancellations) / COUNT(Assigned Rides)' as formula_text
  union all select 13 as source_row_number, 'Client Services' as organization_name, 'Rider No Shows' as metric_name, 'All assigned rides that had a cancellation reason of "Rider no show"' as definition_text, 'COUNT(Rider No Shows)' as formula_text
  union all select 14 as source_row_number, 'Client Services' as organization_name, '% Rider No Show' as metric_name, 'The percentage of assigned rides that had rider no shows' as definition_text, 'COUNT(Rider No Shows) / COUNT(Assigned Rides)' as formula_text
  union all select 15 as source_row_number, 'Client Services' as organization_name, 'Rider Cancellations & Rider No Shows' as metric_name, 'All assigned rides that had a cancellation reason of "Rider cancelled" or "Rider no show", regardless of pairing status' as definition_text, 'COUNT(Rider Cancellations) + COUNT(Rider No Shows)' as formula_text
  union all select 16 as source_row_number, 'Client Services' as organization_name, '% Rider Cancelled or RNS' as metric_name, 'The percentage of assigned rides that had rider cancellations or rider no shows' as definition_text, '(COUNT(Rider Cancellations) + COUNT(Rider No Shows)) / COUNT(Assigned Rides)' as formula_text
  union all select 17 as source_row_number, 'Client Services' as organization_name, 'Rider Late Cancellations' as metric_name, 'All assigned rides that had a cancellation reason of "Rider cancelled" AFTER being paired with a driver, and were cancelled after that transit program''s acceptable cancellation period, OR were rider no shows' as definition_text, 'COUNT(Late Rider Cancellations)' as formula_text
  union all select 18 as source_row_number, 'Client Services' as organization_name, '% Late Rider Cancelled' as metric_name, 'The percentage of all rider cancellations AFTER a driver was paired that were late cancellations (rider no shows included as late cancellations)' as definition_text, 'COUNT(Late Rider Cancellations) / COUNT(Rider Cancellations Made After Driver Paired)' as formula_text
  union all select 19 as source_row_number, 'Client Services' as organization_name, 'Unique Drivers ' as metric_name, 'The count of unique drivers that have entered the in-progress status of a ride' as definition_text, 'COUNT(Unique Drivers)' as formula_text
  union all select 20 as source_row_number, 'Client Services' as organization_name, 'Unique Riders' as metric_name, 'The count of unique riders that have completed a ride' as definition_text, 'COUNT(Unique Riders)' as formula_text
  union all select 21 as source_row_number, 'Client Services' as organization_name, '% UZURV On-Time' as metric_name, 'The percentage of completed and incident cancellation rides that had a pick-up arrived time no later than 15 minutes after the scheduled pick-up date' as definition_text, 'COUNT(UZURV On-Time Rides) / (COUNT(Completed Rides) + COUNT(Incident Cancellations))' as formula_text
  union all select 22 as source_row_number, 'Client Services' as organization_name, '% Program On-Time' as metric_name, 'The percentage of completed and incident cancellation rides that had a pick-up arrived time within the transit program''s allowable time window' as definition_text, 'COUNT(Program On-Time Rides) / (COUNT(Completed Rides) + COUNT(Incident Cancellations))' as formula_text
  union all select 23 as source_row_number, 'Client Services' as organization_name, '% Program Early' as metric_name, 'The percentage of completed and incident cancellation rides that had a pick-up arrived time before the transit program''s allowable earliest time window' as definition_text, 'COUNT(Program Early Rides) / (COUNT(Completed Rides) + COUNT(Incident Cancellations))' as formula_text
  union all select 24 as source_row_number, 'Client Services' as organization_name, '% Program Late' as metric_name, 'The percentage of completed and incident cancellation rides that had a pick-up arrived time after the transit program''s allowable latest time window' as definition_text, 'COUNT(Program Late Rides) / (COUNT(Completed Rides) + COUNT(Incident Cancellations))' as formula_text
  union all select 25 as source_row_number, 'Finance' as organization_name, 'Charged Rides' as metric_name, 'The distinct count of rides that had a status of completed, rider cancelled, or rider no show, though some of these can be charged as $0' as definition_text, 'COUNTD(Ride Requests)' as formula_text
  union all select 26 as source_row_number, 'Finance' as organization_name, 'Revenue' as metric_name, 'What external clients pay UZURV for all rides' as definition_text, 'SUM(Ride Revenue)' as formula_text
  union all select 27 as source_row_number, 'Finance' as organization_name, 'Revenue per Ride' as metric_name, 'What external clients pay UZURV, per ride' as definition_text, 'SUM(Ride Revenue) / COUNT(Rides)' as formula_text
  union all select 28 as source_row_number, 'Finance' as organization_name, 'Revenue per P3 Mile' as metric_name, 'What external clients pay UZURV, per P3 mile' as definition_text, 'SUM(Ride Revenue) / SUM(P3 Miles)' as formula_text
  union all select 29 as source_row_number, 'Finance' as organization_name, 'Provider Cost' as metric_name, 'What UZURV pays providers for all rides' as definition_text, 'SUM(Provider Cost)' as formula_text
  union all select 30 as source_row_number, 'Finance' as organization_name, 'Provider Cost per Ride' as metric_name, 'What UZURV pays providers, per ride' as definition_text, 'SUM(Provider Cost) / COUNT(Rides)' as formula_text
  union all select 31 as source_row_number, 'Finance' as organization_name, 'Provider Cost per P3 Mile' as metric_name, 'What UZURV pays providers, per P3 mile' as definition_text, 'SUM(Provider Cost) / SUM(P3 Miles)' as formula_text
  union all select 32 as source_row_number, 'Finance' as organization_name, 'Provider Incentive' as metric_name, 'What UZURV pays providers in incentives only' as definition_text, 'SUM(Provider Incentive)' as formula_text
  union all select 33 as source_row_number, 'Finance' as organization_name, 'Provider Incentive per Ride' as metric_name, 'What UZURV pays providers in incentives only, per ride' as definition_text, 'SUM(Provider Incentive) / COUNT(Rides)' as formula_text
  union all select 34 as source_row_number, 'Finance' as organization_name, 'Provider Incentive per P3 Mile' as metric_name, 'What UZURV pays providers in incentives only, per P3 Mile' as definition_text, 'SUM(Provider Incentive) / SUM(P3 Miles)' as formula_text
  union all select 35 as source_row_number, 'Finance' as organization_name, 'Insurance Cost' as metric_name, 'What UZURV is charged by insurance carrier on P2 and P3 miles for all rides' as definition_text, 'SUM(Insurance Cost)' as formula_text
  union all select 36 as source_row_number, 'Finance' as organization_name, 'Insurance Cost per Ride' as metric_name, 'What UZURV is charged by insurance carrier on P2 and P3 miles, per ride' as definition_text, 'SUM(Insurance Cost) / COUNT(Rides)' as formula_text
  union all select 37 as source_row_number, 'Finance' as organization_name, 'Insurance Cost per P3 Mile' as metric_name, 'What UZURV is charged by insurance carrier on P2 and P3 miles, per P3 Mile' as definition_text, 'SUM(Insurance Cost) / SUM(P3 Miles)' as formula_text
  union all select 38 as source_row_number, 'Finance' as organization_name, 'UZURV Cost' as metric_name, 'Total provider and insurance cost to UZURV for all rides' as definition_text, 'SUM(Provider Cost + Insurance Cost)' as formula_text
  union all select 39 as source_row_number, 'Finance' as organization_name, 'UZURV Cost per Ride' as metric_name, 'Total provider and insurance cost to UZURV, per ride' as definition_text, 'SUM(Provider Cost + Insurance Cost) / COUNT(Rides)' as formula_text
  union all select 40 as source_row_number, 'Finance' as organization_name, 'UZURV Cost per P3 Mile' as metric_name, 'Total provider and insurance cost to UZURV, per P3 mile' as definition_text, 'SUM(Provider Cost + Insurance Cost) / SUM(P3 Miles)' as formula_text
  union all select 41 as source_row_number, 'Finance' as organization_name, 'Gross Profit' as metric_name, 'What external clients pay UZURV for a ride minus what UZURV pays providers for all rides' as definition_text, 'SUM(Ride Revenue - Provider Cost)' as formula_text
  union all select 42 as source_row_number, 'Finance' as organization_name, 'Gross Profit per Ride' as metric_name, 'What external clients pay UZURV for a ride minus what UZURV pays providers, per ride' as definition_text, 'SUM(Ride Revenue - Provider Cost) / COUNT(Rides)' as formula_text
  union all select 43 as source_row_number, 'Finance' as organization_name, 'Gross Profit per P3 Mile' as metric_name, 'What external clients pay UZURV for a ride minus what UZURV pays providers, per P3 mile' as definition_text, 'SUM(Ride Revenue - Provider Cost) / SUM(P3 Miles)' as formula_text
  union all select 44 as source_row_number, 'Finance' as organization_name, 'Adjusted Gross Profit' as metric_name, 'What external clients pay UZURV for all rides minus what UZURV pays providers and insurance carriers for all rides' as definition_text, 'SUM(Ride Revenue - Provider Cost - Insurance Cost)' as formula_text
  union all select 45 as source_row_number, 'Finance' as organization_name, 'Adjusted Gross Profit per Ride' as metric_name, 'What external clients pay UZURV for a ride minus what UZURV pays providers and insurance carriers, per ride' as definition_text, 'SUM(Ride Revenue - Provider Cost - Insurance Cost) / COUNT(Rides)' as formula_text
  union all select 46 as source_row_number, 'Finance' as organization_name, 'Adjusted Gross Profit per P3 Mile' as metric_name, 'What external clients pay UZURV for a ride minus what UZURV pays providers and insurance carriers, per P3 mile' as definition_text, 'SUM(Ride Revenue - Provider Cost - Insurance Cost) / SUM(P3 Miles)' as formula_text
  union all select 47 as source_row_number, 'Finance' as organization_name, 'P2:P3 Ratio' as metric_name, 'Ratio of P2 miles to P3 miles' as definition_text, 'SUM(P2 Miles) / SUM(P3 Miles)' as formula_text
  union all select 48 as source_row_number, 'Finance' as organization_name, 'Gross Profit Margin (GPM)' as metric_name, 'Gross profit divided by ride revenue' as definition_text, 'SUM(Ride Revenue - Provider Cost) / SUM(Ride Revenue)' as formula_text
  union all select 49 as source_row_number, 'Finance' as organization_name, 'Adjusted Gross Profit Margin (GPM)' as metric_name, 'Adjusted gross profit divided by ride revenue' as definition_text, 'SUM(Ride Revenue - Provider Cost - Insurance Cost) / SUM(Ride Revenue)' as formula_text
  union all select 50 as source_row_number, 'Rider App' as organization_name, 'All Ride Creations' as metric_name, 'All ride requests that were created during the selected period' as definition_text, 'COUNT(All Ride Creations)' as formula_text
  union all select 51 as source_row_number, 'Rider App' as organization_name, 'Rider App Creations ' as metric_name, 'All ride requests that were created via the Rider App' as definition_text, 'COUNT(Rider App Creations)' as formula_text
  union all select 52 as source_row_number, 'Rider App' as organization_name, 'Rider App Creation Rate' as metric_name, 'The percentage of all ride requests that were created via the Rider App' as definition_text, 'COUNT(Rider App Creations) / COUNT(All Ride Creations)' as formula_text
  union all select 53 as source_row_number, 'Rider App' as organization_name, 'Rider App Activations ' as metric_name, 'All will calls that were activated via the Rider App (Note: ride now rides are not included here, as they''re counted as part of ride creations)' as definition_text, 'COUNT(Rider App Activations)' as formula_text
  union all select 54 as source_row_number, 'Rider App' as organization_name, 'Rider App Activation Rate' as metric_name, 'The percentage of will calls that were activated via the Rider App' as definition_text, 'COUNT(Rider App Activations) / COUNT(All Ride Activations)' as formula_text
  union all select 55 as source_row_number, 'Rider App' as organization_name, 'Rider App Cancellations' as metric_name, 'All ''Rider cancelled'' cancellations that are cancelled via the Rider App' as definition_text, 'COUNT(Rider App Cancellations)' as formula_text
  union all select 56 as source_row_number, 'Rider App' as organization_name, 'Rider App Cancellation Rate' as metric_name, 'The percentage of all ''Rider cancelled'' cancellations that are cancelled via the Rider App' as definition_text, 'COUNT(Rider App Cancellations) / COUNT(All Rider Cancellations)' as formula_text
  union all select 57 as source_row_number, 'Rider App' as organization_name, 'Total Riders' as metric_name, 'All unique riders that have intended to take a ride during the selected period' as definition_text, 'COUNT(All Riders)' as formula_text
  union all select 58 as source_row_number, 'Rider App' as organization_name, 'Rider App Installations' as metric_name, 'All unique riders that have installed the Rider App' as definition_text, 'COUNT(Rider App Installations)' as formula_text
  union all select 59 as source_row_number, 'Rider App' as organization_name, 'Rider App Users' as metric_name, 'All unique riders that have either scheduled, activated, or cancelled a ride via the Rider App' as definition_text, 'COUNT(Rider App Users)' as formula_text
  union all select 60 as source_row_number, 'Rider App' as organization_name, 'Rider App Lapsed Users' as metric_name, 'All unique former Rider App users that did not use the Rider App for their most recent ride (i.e. no creation, activation, or cancellation via Rider App)' as definition_text, 'COUNT(Rider App Lapsed Users)' as formula_text
  union all select 61 as source_row_number, 'Rider App' as organization_name, 'Rider App Current Users' as metric_name, 'All unique riders that used the Rider App for their most recent ride (i.e. one of creation, activation, or cancellation) Calculated by Rider App Users - Rider App Lapsed Users' as definition_text, 'COUNT(Rider App Current Users)' as formula_text
  union all select 62 as source_row_number, 'Rider App' as organization_name, 'Rider App Unrealized Rate' as metric_name, 'The percentage of unique riders that have downloaded the Rider App but haven''t used it' as definition_text, '(COUNT(Rider App Installations) - COUNT(Rider App Users)) / COUNT(Rider App Installations)' as formula_text
  union all select 63 as source_row_number, 'Rider App' as organization_name, 'Rider App Usage Rate' as metric_name, 'The percentage of all unique riders that have used the Rider App at least once' as definition_text, 'COUNT(Rider App Users) / COUNT(All Riders)' as formula_text
  union all select 64 as source_row_number, 'Rider App' as organization_name, 'Rider App Current Usage Rate' as metric_name, 'The percentage of all unique riders that used the Rider App for their most recent ride (i.e. one of creation, activation, or cancellation)' as definition_text, 'COUNT(Rider App Current Users) / COUNT(All Users)' as formula_text
  union all select 65 as source_row_number, 'Rider App' as organization_name, 'Rider App Lapsed Usage Rate' as metric_name, 'The percentage of Rider App users that did not use the Rider App for their most recent ride (i.e. no creation, activation, or cancellation via Rider App)' as definition_text, 'COUNT(Rider App Lapsed Users) / COUNT(Rider App Users)' as formula_text
  union all select 66 as source_row_number, 'Rider App' as organization_name, 'Call Center Hours Saved' as metric_name, 'The number of hours saved, based on TOG Efficiency parameter, assuming that every ride creation, activation, and cancellation in the Rider App would have had to go through the call center' as definition_text, 'SUM(Call Center Hours Saved)' as formula_text
  union all select 67 as source_row_number, 'Rider App' as organization_name, 'Call Center Opportunity Costs Saved' as metric_name, 'The costs saved, based on TOG Efficiency and TOG Hourly Rate parameters, assuming that every ride creation, activation, and cancellation in the Rider App would have had to go through the call center' as definition_text, 'SUM(Call Center Hours Saved) * TOG Hourly Rate' as formula_text
  union all select 68 as source_row_number, 'Ride Execution' as organization_name, 'Completed' as metric_name, 'A ride request resulted in a reservation status of ''Completed''' as definition_text, '' as formula_text
  union all select 69 as source_row_number, 'Ride Execution' as organization_name, 'Returned' as metric_name, 'A ride request resulted in a ride request cancellation reason of ''No driver interest''' as definition_text, '' as formula_text
  union all select 70 as source_row_number, 'Ride Execution' as organization_name, 'Returned: Driver Cancelled' as metric_name, 'A ride request included at least one reservation with a cancellation reason of ''Driver cancelled'' and resulted in a ride request cancellation reason of ''No driver interest''' as definition_text, '' as formula_text
  union all select 71 as source_row_number, 'Ride Execution' as organization_name, 'Returned: No Driver Paired' as metric_name, 'A ride request had no drivers paired/associated reservations and resulted in a ride request cancellation reason of ''No driver interest''' as definition_text, '' as formula_text
  union all select 72 as source_row_number, 'Ride Execution' as organization_name, 'Sent to Lyft' as metric_name, 'A ride request was sent to Lyft at some point (even if a UZURV driver eventually paired with the ride)' as definition_text, '' as formula_text
  union all select 73 as source_row_number, 'Ride Execution' as organization_name, 'Driver Cancelled' as metric_name, 'A ride request included at least one reservation with a cancellation reason of ''Driver cancelled''' as definition_text, '' as formula_text
  union all select 74 as source_row_number, 'Ride Execution' as organization_name, 'Late Driver Cancelled' as metric_name, 'A ride request included at least one reservation with a cancellation reason of ''Driver cancelled'', which occured after that respective program''s allowable cancellation window, OR resulted in a reservation cancellation reason of ''Driver no show''' as definition_text, '' as formula_text
  union all select 75 as source_row_number, 'Ride Execution' as organization_name, 'Driver No Show' as metric_name, 'A ride request resulted in a reservation cancellation reason of ''Driver no show''' as definition_text, '' as formula_text
  union all select 76 as source_row_number, 'Ride Execution' as organization_name, 'Rider Cancelled & Rider No Show (RNS)' as metric_name, 'A ride request resulted in a reservation cancellations reason of ''Rider cancelled'' or ''Rider no show''' as definition_text, '' as formula_text
  union all select 77 as source_row_number, 'Ride Execution' as organization_name, 'Rider Cancelled' as metric_name, 'A ride request resulted in a reservation cancellations reason of ''Rider cancelled''' as definition_text, '' as formula_text
  union all select 78 as source_row_number, 'Ride Execution' as organization_name, 'Rider No Show' as metric_name, 'A ride request resulted in a reservation cancellations reason of ''Rider no show''' as definition_text, '' as formula_text
  union all select 79 as source_row_number, 'Ride Execution' as organization_name, 'Late Rider Cancelled' as metric_name, 'A ride request resulted in a reservation with a cancellation reason of ''Rider cancelled'', which occured after that respective program''s allowable cancellation window, OR resulted in a reservation cancellation reason of ''Rider no show''' as definition_text, '' as formula_text
  union all select 80 as source_row_number, 'Ride Execution' as organization_name, 'Provider Incentive Offered' as metric_name, 'A ride request included a driver incentive at some point' as definition_text, '' as formula_text
  union all select 81 as source_row_number, 'Ride Execution' as organization_name, 'Actual Multi-Ride Journey' as metric_name, 'A ride request had its final reservation as part of a multi-ride journey' as definition_text, '' as formula_text
  union all select 82 as source_row_number, 'Ride Execution' as organization_name, 'Intended Multi-Ride Journey' as metric_name, 'A driver initially paired with a ride request as part of a multi-ride journey, regardless if it was eventually split out into single rides or not' as definition_text, '' as formula_text
  union all select 83 as source_row_number, 'Ride Execution' as organization_name, 'UZURV On-Time' as metric_name, 'A ride request resulted in a pick-up arrived time no later than 15 minutes after the scheduled pick-up date' as definition_text, '' as formula_text
  union all select 84 as source_row_number, 'Ride Execution' as organization_name, 'Program On-Time' as metric_name, 'A ride request resulted in a pick-up arrived time within that program''s allowable time window' as definition_text, '' as formula_text
  union all select 85 as source_row_number, 'Ride Measures' as organization_name, 'P2 Minutes' as metric_name, 'P2 duration of a reservation, represented as minutes' as definition_text, '' as formula_text
  union all select 86 as source_row_number, 'Ride Measures' as organization_name, 'P2 Miles' as metric_name, 'P2 distance of a reservation, represented in miles' as definition_text, '' as formula_text
  union all select 87 as source_row_number, 'Ride Measures' as organization_name, 'P3 Minutes' as metric_name, 'P2 duration of a reservation, represented as minutes' as definition_text, '' as formula_text
  union all select 88 as source_row_number, 'Ride Measures' as organization_name, 'P3 Miles' as metric_name, 'P2 distance of a reservation, represented in miles' as definition_text, '' as formula_text
  union all select 89 as source_row_number, 'Ride Measures' as organization_name, 'P2:P3 Miles' as metric_name, 'P2 miles / P3 miles value for a reservation (NOT aggregated sum value like Finance dashboard)' as definition_text, '' as formula_text
  union all select 90 as source_row_number, 'Ride Measures' as organization_name, 'Provider Pay' as metric_name, 'What a provider was paid for a reservation' as definition_text, '' as formula_text
  union all select 91 as source_row_number, 'Ride Measures' as organization_name, 'Provider Incentive Offered' as metric_name, 'The last incentive amount offered to all drivers for a ride request' as definition_text, '' as formula_text
  union all select 92 as source_row_number, 'Ride Measures' as organization_name, 'Created to Scheduled Hours' as metric_name, 'The time, represented in hours, between when a ride request was created and the scheduled pick-up date. NOTE: Created represents first created in our system and doesn''t account for hold time before entering driver feed.' as definition_text, '' as formula_text
  union all select 93 as source_row_number, 'Ride Measures' as organization_name, 'Cancelled to Scheduled Hours' as metric_name, 'The time, represented in hours, between when a reservation was cancelled and the scheduled pick-up date' as definition_text, '' as formula_text
  union all select 94 as source_row_number, 'Ride Measures' as organization_name, 'Last Cancelled to Scheduled Hours' as metric_name, 'The time, represented in hours, between the latest cancellation of a ride requestsand the scheduled pick-up date' as definition_text, '' as formula_text
  union all select 95 as source_row_number, 'Ride Measures' as organization_name, 'Pairings per Ride' as metric_name, 'The number of reservations per ride request' as definition_text, '' as formula_text
  union all select 96 as source_row_number, 'Ride Measures' as organization_name, 'Created to Paired Minutes' as metric_name, 'The time, represented in minutes, between when a ride request was created and when it was paired (a ride request with multiple reservations will have multiple values). NOTE: Created represents first created in our system and doesn''t account for hold time before entering driver feed.' as definition_text, '' as formula_text
  union all select 97 as source_row_number, 'Ride Measures' as organization_name, 'Created to First Paired Minutes' as metric_name, 'The time, represented in minutes, between when a ride request was created and when it was first paired (a ride request will have only one value). NOTE: Created represents first created in our system and doesn''t account for hold time before entering driver feed.' as definition_text, '' as formula_text
  union all select 98 as source_row_number, 'Ride Measures' as organization_name, 'Drop-off Arrived to Completed Minutes' as metric_name, 'The time, represented in minutes, between when a reservation was marked by the driver as drop-off arrived and when it was marked as completed' as definition_text, '' as formula_text
  union all select 99 as source_row_number, 'Ride Measures' as organization_name, 'Pick-up Arrived to In Progress Minutes' as metric_name, 'The time, represented in minutes, between when a reservation was marked by the driver as pick-up arrived and when it was marked as in progress' as definition_text, '' as formula_text
  union all select 100 as source_row_number, 'Ride Monitoring' as organization_name, 'Alerts per Day' as metric_name, 'The distinct count of operations alerts divided by the number of days with at least one ride' as definition_text, '' as formula_text
  union all select 101 as source_row_number, 'Ride Monitoring' as organization_name, 'Alert Ride %' as metric_name, 'The percentage of total ride requests that resulted in at least one operations alert' as definition_text, '' as formula_text
  union all select 102 as source_row_number, 'Ride Monitoring' as organization_name, 'Assigned %' as metric_name, 'The percentage of alerts that were assigned to an operations associate in the CRM' as definition_text, '' as formula_text
  union all select 103 as source_row_number, 'Ride Monitoring' as organization_name, 'Updated %' as metric_name, 'The percentage of alerts that were updated by an operations associate in the CRM' as definition_text, '' as formula_text
  union all select 104 as source_row_number, 'Ride Monitoring' as organization_name, 'Closed % ' as metric_name, 'The percentage of alerts that were updated by an operations associate in the CRM' as definition_text, '' as formula_text
  union all select 105 as source_row_number, 'Ride Monitoring' as organization_name, 'Created -> Assigned Minutes' as metric_name, 'The number of minutes between when an alert was created and when it was last assigned to an operations associate in the CRM' as definition_text, '' as formula_text
  union all select 106 as source_row_number, 'Ride Monitoring' as organization_name, 'Created -> Updated Minutes' as metric_name, 'The number of minutes between when an alert was created and when it was updated by an operations associate in the CRM' as definition_text, '' as formula_text
  union all select 107 as source_row_number, 'Ride Monitoring' as organization_name, 'Created -> Closed Minutes' as metric_name, 'The number of minutes between when an alert was created and when it was closed by the system' as definition_text, '' as formula_text
  union all select 108 as source_row_number, 'Ride Monitoring' as organization_name, 'Assigned -> Updated Minutes' as metric_name, 'The number of minutes between when an alert was last assigned to an operations associate in the CRM and when it was updated by that associate' as definition_text, '' as formula_text
  union all select 109 as source_row_number, 'Ride Monitoring' as organization_name, 'Assigned -> Closed Minutes' as metric_name, 'The number of minutes between when an alert was last assigned to an operations associate in the CRM and when it was closed by the system' as definition_text, '' as formula_text
  union all select 110 as source_row_number, 'NGAP' as organization_name, 'UZURV On-Time %' as metric_name, 'The percentage of completed rides where the pick-up arrival time occurred no later than 15 minutes after the scheduled pick-up time (relevant for scheduled pairing only)' as definition_text, '' as formula_text
  union all select 111 as source_row_number, 'NGAP' as organization_name, 'Late Driver Cancel %' as metric_name, 'The percentage of rides with a cancellation reason of "Driver cancelled" that occurred after the program’s allowable cancellation window divided by all rides with that are either "Completed", "Driver cancelled" or "Driver no show"' as definition_text, '' as formula_text
  union all select 112 as source_row_number, 'NGAP' as organization_name, 'Driver No Show %' as metric_name, 'The percentage of rides with a reservation cancellation reason of "Driver no show" divided by all rides with that are either "Completed", "Driver cancelled" or "Driver no show"' as definition_text, '' as formula_text
  union all select 113 as source_row_number, 'NGAP' as organization_name, 'Average P2 Minutes' as metric_name, 'The average P2 minutes for completed rides only (relevant for on-demand pairing only)' as definition_text, '' as formula_text
  union all select 114 as source_row_number, 'NGAP' as organization_name, 'Average P2 Miles' as metric_name, 'The average P2 miles for completed rides only (relevant for on-demand pairing only)' as definition_text, '' as formula_text
  union all select 115 as source_row_number, 'NGAP' as organization_name, 'Median P2:P3 Ratio' as metric_name, 'The median ratio of P2 miles to P3 miles for completed rides only (relevant for on-demand pairing only)' as definition_text, '' as formula_text
  union all select 116 as source_row_number, 'NGAP' as organization_name, 'Inexperience Paired %' as metric_name, 'The percentage of paired instances (on-demand equals ride instances; scheduled equals journey instances) that were paired with an inexperienced driver (defined as fewer than the configured completed reservation count)' as definition_text, '' as formula_text
  union all select 117 as source_row_number, 'NGAP' as organization_name, 'Average Reliability Score' as metric_name, 'The average reliability score used for all NGAP paired driver instances (on-demand equals ride instances; scheduled equals journey instances)' as definition_text, '' as formula_text
  union all select 118 as source_row_number, 'NGAP' as organization_name, 'Average Reputation Score' as metric_name, 'The average reputation score used for all NGAP paired driver instances (on-demand equals ride instances; scheduled equals journey instances)' as definition_text, '' as formula_text
  union all select 119 as source_row_number, 'NGAP' as organization_name, 'Average Safety Score' as metric_name, 'The average safety score used for all NGAP paired driver instances (on-demand equals ride instances; scheduled equals journey instances)' as definition_text, '' as formula_text
)
select
  lower(substring(md5(v.organization_name || '|' || trim(v.metric_name)), 1, 8) || '-' ||
        substring(md5(v.organization_name || '|' || trim(v.metric_name)), 9, 4) || '-' ||
        substring(md5(v.organization_name || '|' || trim(v.metric_name)), 13, 4) || '-' ||
        substring(md5(v.organization_name || '|' || trim(v.metric_name)), 17, 4) || '-' ||
        substring(md5(v.organization_name || '|' || trim(v.metric_name)), 21, 12)) as kpi_id,
  v.metric_name,
  trim(both '-' from regexp_replace(lower(v.organization_name || '-' || trim(v.metric_name)), '[^a-z0-9]+', '-')) as kpi_slug,
  1 as kpi_version,
  v.definition_text,
  'Unknown (not provided in source workbook)' as owner_person,
  v.organization_name as owner_team,
  v.organization_name as owning_department,
  'active' as status,
  'experimental' as certification_level,
  v.formula_text,
  'Dashboard Data Definitions.xlsx|Summary|' || lpad(cast(v.source_row_number as varchar(10)), 4, '0') as metric_query_reference
from source_rows v
where not exists (
  select 1
  from kpi_catalog.kpi_definition d
  where d.kpi_slug = trim(both '-' from regexp_replace(lower(v.organization_name || '-' || trim(v.metric_name)), '[^a-z0-9]+', '-'))
    and d.kpi_version = 1
);

insert into kpi_catalog.kpi_usage (
  kpi_id, kpi_slug, kpi_version, report_id, usage_type
)
select
  d.kpi_id,
  d.kpi_slug,
  d.kpi_version,
  r.report_id,
  'table' as usage_type
from kpi_catalog.kpi_definition d
join kpi_catalog.report r
  on r.consumer_tool = 'excel'
 and r.report_slug = 'dashboard-data-definitions-summary'
where d.metric_query_reference like 'Dashboard Data Definitions.xlsx|Summary|%'
  and not exists (
    select 1
    from kpi_catalog.kpi_usage u
    where u.kpi_slug = d.kpi_slug
      and u.kpi_version = d.kpi_version
      and u.report_id = r.report_id
  )
order by d.metric_query_reference;

create or replace view kpi_catalog.v_dashboard_data_definitions_summary as
select
  d.owner_team as "Organization",
  d.kpi_name as "Metric",
  d.business_definition as "Definition",
  d.formula as "Formula "
from kpi_catalog.kpi_usage u
join kpi_catalog.report r
  on r.report_id = u.report_id
join kpi_catalog.kpi_definition d
  on d.kpi_id = u.kpi_id
 and d.kpi_slug = u.kpi_slug
 and d.kpi_version = u.kpi_version
where r.consumer_tool = 'excel'
  and r.report_slug = 'dashboard-data-definitions-summary'
order by d.metric_query_reference;

-- Workbook facts: 118 data rows across 7 organizations; 52 rows have a blank formula cell.
