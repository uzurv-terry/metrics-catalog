# Metric Owner SNS Notification Solution

## Purpose
This document describes a solution for notifying a metric owner by email when ownership is assigned or changed in the metrics catalog application.

The notification channel is Amazon SNS.

## Goal
When a metric definition is created or updated and an owner is assigned, the owner should receive an email that confirms:
- they were assigned as the metric owner
- which metric they now own
- the metric status and version
- where to view the metric in the catalog

## Scope
This solution applies to metric definition ownership, not usage ownership.

Primary event types:
- new metric created with an owner
- existing metric updated and owner changes

Optional later event types:
- owner team changed
- metric status changed to `active`
- metric certification changed

## Current Gap
The current metric definition model contains:
- `owner_person`

It does not contain:
- `owner_email`

SNS email delivery requires a routable email address, so the app needs one of these two patterns:

## Recommended Option A
Add `owner_email` directly to `kpi_catalog.kpi_definition`.

Why this is the simplest option:
- no runtime dependency on a people directory lookup
- deterministic delivery target at save time
- easier auditing and troubleshooting

## Alternate Option B
Resolve `owner_person` to an email through an internal directory service.

Why this is weaker for the current app:
- adds a second integration dependency
- adds lookup latency to the save path
- creates failure modes unrelated to Redshift or SNS

Recommendation:
- use Option A unless the organization already has a stable directory API used by internal apps

## Proposed Data Model Change

Add to `kpi_catalog.kpi_definition`:

```sql
ALTER TABLE kpi_catalog.kpi_definition
ADD COLUMN owner_email VARCHAR(255);
```

The app should treat `owner_email` as required when owner notifications are enabled.

## Notification Trigger Rules

Send a notification when:
1. a new metric is created and `owner_email` is populated
2. an existing metric is updated and either:
   - `owner_person` changed
   - `owner_email` changed

Do not send a notification when:
- the metric is updated but owner fields did not change
- `owner_email` is empty
- the owner notification feature is disabled

## Delivery Flow

Recommended flow:

1. user saves metric definition
2. metric definition service validates and writes to Redshift
3. app determines whether ownership assignment is new or changed
4. app publishes an SNS message
5. SNS sends email to subscribed address or directly to the provided recipient workflow

## Architecture Decision
Do not publish to SNS before the Redshift write succeeds.

Reason:
- ownership email should reflect committed application state

## Preferred Implementation Pattern

### Phase 1: direct publish after successful write
The application service publishes directly to SNS after the Redshift write succeeds.

Advantages:
- simplest implementation
- easy to reason about
- good fit if notification volume is low

Tradeoff:
- save path now includes SNS publish latency

### Phase 2: outbox/event handoff
Write a notification event record after save and let a worker publish to SNS asynchronously.

Advantages:
- more resilient
- save path is less coupled to SNS availability
- easier retries and auditability

Tradeoff:
- requires extra table/process

Recommendation:
- start with direct SNS publish
- move to outbox if notifications become business-critical

## SNS Design

Recommended SNS topic:
- `metric-owner-assignment`

Example configuration:
- topic ARN stored in environment/config
- app publishes JSON payload with metric context

## Suggested Environment Variables

```env
OWNER_NOTIFICATION_ENABLED=true
OWNER_NOTIFICATION_SNS_TOPIC_ARN=arn:aws:sns:us-east-1:123456789012:metric-owner-assignment
METRIC_CATALOG_BASE_URL=https://metrics-catalog.internal.company
```

## Suggested Payload

```json
{
  "event_type": "metric_owner_assigned",
  "kpi_id": "123e4567-e89b-12d3-a456-426614174000",
  "kpi_slug": "gross_profit_margin",
  "kpi_version": 1,
  "metric_name": "Gross Profit Margin",
  "owner_person": "Jane Smith",
  "owner_email": "jane.smith@company.com",
  "status": "draft",
  "certification_level": "experimental",
  "metric_url": "https://metrics-catalog.internal.company/kpi-definitions/overview?kpi_slug=gross_profit_margin&kpi_version=1"
}
```

## Email Content Recommendation

Subject:
- `You were assigned as metric owner: Gross Profit Margin`

Body:
- greeting with owner name
- metric name
- metric id/slug/version
- status/certification
- direct link to Metric Overview
- short explanation of ownership responsibility

## App Layer Changes

## Config
Add settings for:
- feature flag
- SNS topic ARN
- base URL

## Infrastructure
Add an SNS publisher abstraction:
- `OwnerNotificationPublisher`

Implementation:
- `SnsOwnerNotificationPublisher`

Responsibility:
- publish a structured payload to SNS

## Application Service
Update `KpiDefinitionService`:
- on create: publish when owner_email exists
- on update: compare old owner to new owner and publish only on change

## Interface Layer
Update the metric definition form:
- add `owner_email`
- validate email format

## Failure Handling

### Direct publish mode
If the Redshift write succeeds but SNS publish fails:
- do not roll back the metric definition write
- log the publish failure with metric identity
- flash a warning that metric save succeeded but owner notification failed

Reason:
- ownership persistence is more important than notification delivery

### Logging
Log:
- metric identity
- owner email
- event type
- publish success/failure
- SNS message ID when available

## Security and IAM
Application IAM role needs:
- `sns:Publish` on the owner notification topic

If topic encryption is enabled:
- KMS permissions for the topic key may also be required

## Operational Notes
- SNS email subscriptions require confirmation for standard email endpoints
- if direct recipient-specific delivery is required, consider SES later
- if different environments exist, use separate SNS topics per environment

## Recommended Rollout
1. add `owner_email` to the metric definition model and form
2. add config for SNS topic + base URL
3. implement direct publish after successful create/update
4. log publish results
5. add warning handling for SNS failures
6. evaluate whether an outbox pattern is needed

## Summary
The cleanest solution is:
- add `owner_email`
- publish an SNS owner-assignment event after successful metric save
- notify only when ownership is new or changed
- keep the Redshift write authoritative even if SNS delivery fails
