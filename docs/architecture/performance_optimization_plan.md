# Metrics Catalog Performance Optimization Plan

## 1. Purpose
This document defines a performance-focused view of the current `metrics-catalog` implementation and a practical roadmap for improving response time, save latency, and page rendering speed.

The recommendations here are grounded in the app as it exists today:
- Flask server-rendered UI
- repository pattern + service layer
- Amazon Redshift Data API (`boto3` + `redshift-data`)
- synchronous request/response execution model

## 2. Current Performance Profile

## 2.1 Primary Bottleneck
The dominant source of latency is Redshift Data API round-trip overhead, not Python execution.

Typical request cost today includes:
- Data API `execute_statement`
- repeated `describe_statement` polling
- optional `get_statement_result`
- repository-level validation reads before writes
- full-page redirect after save, followed by list query

For create/update flows, one user action often results in multiple Redshift calls.

## 2.2 Secondary Bottlenecks
- Loading large recent lists after redirects
- Preloading large metric lookup sets for forms
- Re-validating state with separate existence/uniqueness queries
- Search and lineage reads that are not yet backed by a shared cache
- Rendering large client payloads when a smaller neighborhood would suffice

## 3. Performance Goals

## 3.1 User-Visible Goals
- Save actions should feel fast and predictable.
- Search interactions should feel near-instant after debounce.
- Read-only visual lineage should render quickly even when usage grows.

## 3.2 Target Metrics
- P50 form save response: under 1.0s where possible
- P95 form save response: under 2.5s
- P95 search response: under 800ms
- P95 lineage response: under 1.2s
- No page should fetch more rows than are needed for its first screen

## 4. Current Implemented Optimizations
Already in code:
- `DATA_API_POLL_INTERVAL_SEC` for faster polling cadence
- reduced list limits on heavy pages
- lineage node/edge/search caps
- in-process lineage cache with TTL
- debounced client-side lineage search
- bounded lineage graph rendering
- server-side metric typeahead for Metric Usage and Metric Approvers forms
- summary-only list queries for definitions, usage, and approvers pages
- batched multi-tool usage inserts through a single repository write
- request timing logs for route-level latency measurement
- Redshift Data API timing logs for statement-level latency measurement

These changes reduced initial page payload size, lowered Data API round trips for multi-tool usage creation, and cut list-page query/result size.

## 5. High-Impact Performance Work

## 5.1 Replace Large Datalists with Server-Side Typeahead
Status:
- Implemented for Metric Usage, Metric Approvers, and Metric Overview pages.

Implementation:
- forms now render an empty datalist
- browser fetches metric matches from `/lineage/api/search/kpi`
- search starts at 2+ characters with a 250ms debounce
- selected match still auto-fills `kpi_id`, `kpi_slug`, and `kpi_version`

Impact:
- faster initial page load
- smaller HTML payloads
- lower memory use in browser

## 5.2 Slim List Queries to Overview-Only Reads
Status:
- Implemented for Metric Definitions, Metric Usage, and Metric Approvers pages.

Implementation:
- repositories now expose `list_recent_summary()`
- list pages use summary methods instead of full entity reads
- edit/detail flows still use full fetch methods where needed

Expected impact:
- faster Redshift response
- smaller Data API payloads
- lower template rendering cost

## 5.3 Reduce Save-Flow Validation Round Trips
Current issue:
- create/update flows perform multiple repository reads before the final write.
- this is correct for integrity, but expensive under Data API.

Recommendation:
- consolidate validation reads where practical
- for metric definition create:
  - combine slug/version and name checks into one query if possible
- for metric usage create:
  - validate metric identity once, then reuse result for all selected consumer tools
- for metric approvers:
  - keep existence check but consider combining duplicate detection with the identity read path if it stays readable

Expected impact:
- lower save latency
- fewer polling cycles per request

Priority:
- High

## 5.4 Batch Multi-Tool Usage Inserts
Status:
- Implemented.

Implementation:
- service now exposes `create_many()`
- metric identity is validated once for the whole batch
- all rows in a batch must reference the same `kpi_id + kpi_slug + kpi_version`
- repository emits one `INSERT ... VALUES (...), (...), ...` statement for the full selection

Expected impact:
- significantly faster multi-tool save path
- fewer Data API `execute_statement` and polling cycles per user save

## 5.5 Introduce Shared Cache for Read-Heavy Features
Current issue:
- lineage currently uses in-process cache only.
- multi-instance deployment will not share that cache.

Recommendation:
- phase 1: keep in-process cache for local/UAT
- phase 2: move search/lineage read caching to Redis or equivalent shared cache

Best cache candidates:
- lineage graph payloads
- metric search results
- report search results
- recent summary lists if they become frequently revisited

Priority:
- Medium

## 6. Data API-Specific Optimizations

## 6.1 Tune Polling Carefully
Current knob:
- `DATA_API_POLL_INTERVAL_SEC`

Guidance:
- keep low enough to reduce perceived latency
- do not set unrealistically low if you see excessive polling chatter
- practical range: `0.1` to `0.25` seconds

Recommendation:
- benchmark `0.1`, `0.15`, `0.2`
- choose the lowest stable value that does not cause operational noise

## 6.2 Keep Statements Short and Bounded
Guidance:
- always use `LIMIT`
- keep result sets narrow
- avoid “load everything and filter in Python”
- prefer one well-shaped query over multiple small read queries

## 6.3 Avoid N+1 Patterns
This matters especially in:
- lineage graph assembly
- usage identity validation across many rows
- repeated lookup/autocomplete endpoints

## 7. UI and Rendering Optimizations

## 7.1 Prefer Progressive Loading
Do not load:
- all metric options
- all report assets
- all lineage neighborhoods

Load only:
- current page list summary
- typed search results
- selected lineage neighborhood

## 7.2 Keep Graph Rendering Bounded
The lineage module should remain neighborhood-only.

Recommended default limits:
- `LINEAGE_MAX_NODES=60`
- `LINEAGE_MAX_EDGES=120`
- `LINEAGE_SEARCH_LIMIT=20`

If these are exceeded:
- truncate on server
- show a clear “results truncated for performance” message

## 7.3 Preserve Perceived Performance
Continue using:
- disabled submit buttons during save
- inline loading status text
- search debounce

Add next:
- skeleton or loading placeholder for lineage graph
- small “Last loaded” timestamp on graph panel if caching is used

## 7.4 Search Usability Improvements
Recommended next usability improvements:
- keyboard navigation for search results with up/down arrows and Enter-to-select
- auto-submit exact match when the user presses Enter
- highlight the matched term in result labels
- show the last 5 recently viewed metrics in the Metric Overview page
- keep a selected-result chip visible after search so users know what is loaded
- add a clear distinction between metric-name matches and slug/id matches
- show result counts with lightweight category labels such as `name`, `slug`, or `id`

These changes improve perceived quality even when backend response times stay the same.

## 7.5 Search Performance Improvements
Additional performance work for search:
- add short-lived client-side memory cache per page session for repeated search terms
- enforce a 3-character minimum for broad catalog search if result sets grow materially
- add server-side prefix-first search path before falling back to contains search
- add a denormalized search helper table if Redshift search latency remains high
- paginate or cap results more aggressively for common short queries
- consider a shared Redis cache for search results in multi-instance deployment

Recommendation:
- implement keyboard navigation and client-side session cache next
- evaluate helper-table design only after timing logs confirm Redshift search remains the bottleneck

## 8. Data Model Changes That Improve Performance

## 8.1 Add Stable Report Asset Identity
Current report lineage fallback depends on:
- `consumer_tool`
- `reference_name`

Recommendation:
- add `asset_id VARCHAR(255)` to `kpi_catalog.kpi_usage`

Why:
- faster and more reliable report-centric lookups
- avoids case/whitespace normalization issues
- simplifies caching keys

Priority:
- High for lineage maturity

## 8.2 Add Summary-Focused Indexing Strategy in DDL
Redshift uses sort/dist strategy rather than row-store indexes.

Recommendations:
- keep sort keys aligned to common reads
- for usage-heavy reads, ensure sort key supports:
  - `kpi_slug`
  - `kpi_version`
  - `consumer_tool`
  - `reference_name`

This is already reasonably aligned in current design.

## 9. Deployment and Runtime Considerations

## 9.1 Multi-Instance Behavior
If deployed behind an ALB with more than one app instance:
- in-process cache will fragment
- search/lineage cache hit rate will drop

Recommendation:
- move read cache to shared cache once scale justifies it

## 9.2 Logging for Performance
Add request timing around:
- save endpoints
- search endpoints
- lineage endpoints

At minimum log:
- route
- elapsed time
- query type
- row count where relevant

This should be the basis for optimization, not guesswork.

## 10. Recommended Delivery Sequence

## Phase 1: Immediate Wins
1. Measure the impact of the new typeahead, summary-query, and batched-insert paths using the timing logs.
2. Tune `DATA_API_POLL_INTERVAL_SEC` based on observed latency rather than default values.
3. Implement keyboard navigation and client-side session caching for search.
4. Identify the slowest endpoints and confirm whether the time is in request overhead or Data API execution.

## Phase 2: Structural Improvements
1. Add `asset_id` to `kpi_usage`.
2. Add shared cache for lineage/search.
3. Evaluate whether metric definition and approver validation reads can be consolidated further.

## Phase 3: Optional Deeper Changes
1. Consider direct Redshift connector for write-heavy workflows if Data API latency remains unacceptable.
2. Add asynchronous work only if the UX requirement truly demands it.

## 11. Strong Recommendation
The single most important improvement remains reducing Data API round trips per save and keeping page payloads bounded.

The current implementation now does the three highest-value near-term changes:
1. server-side typeahead for metric lookup
2. batch create for multi-tool usage
3. summary-only list queries

The next performance phase should focus on measurement, query consolidation, and shared caching.
